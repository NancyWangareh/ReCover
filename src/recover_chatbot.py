"""
ReCover chatbot: single-file version of ReCover_Chatbot.ipynb.

It reads the approved insurance documents, builds a searchable library, and chats with a trader
in the terminal. Answers use only the documents, cite file and page, and say so when information
is missing.
       
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
from google import genai
from google.genai import types
from pypdf import PdfReader

# ---- Settings you can change ----
REPO_URL = "https://github.com/NancyWangareh/ReCover.git"   
MODEL = "gemini-3.8-flash"                          
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2" 
COLLECTION_NAME = "recover_docs"                     
MIN_SIMILARITY = 0.30
TOP_K = 4               # how many chunks each search query may return
MAX_RESULTS = 5         # how many chunks we keep in total for one question
OCR_DIR = Path("data/ocr_text")      # where transcriptions of scanned PDFs are saved
CHROMA_DIR = Path("data/chroma_db")  # where the searchable library is saved
# ---------------------------------

# These are filled in by main() before they are used.
DOCS_DIR = None      # folder holding the approved documents
REPO_ROOT = None     # the folder above it
client = None        # connection to Gemini
embedder = None      # the model that turns text into numbers
collection = None    # the searchable library (ChromaDB)
def find_docs_dir():
    """Look for the folder holding the approved documents."""
    for candidate in [Path("ReCover/data collection"), Path("data collection")]:
        if candidate.exists():
            return candidate
    return None


def setup_repo():
    """Find the documents folder, cloning the team repo first if we can't see it."""
    global DOCS_DIR, REPO_ROOT
    if find_docs_dir() is None:
        if "<owner>" in REPO_URL:
            sys.exit("Edit REPO_URL at the top of this file and put in your team's repo link, or run this file from inside the cloned repo.")
        subprocess.run(["git", "clone", REPO_URL], check=True)
    DOCS_DIR = find_docs_dir()
    if DOCS_DIR is None:
        sys.exit("Could not find the 'data collection' folder after cloning. Check REPO_URL.")
    REPO_ROOT = DOCS_DIR.parent
    print("Documents folder:", DOCS_DIR)


def get_api_key():
    """Read the Gemini key from the GEMINI_API_KEY environment variable (or Colab Secrets in Colab).
    The key is never written in the code, which matters because this file goes on GitHub."""
    try:
        from google.colab import userdata
        return userdata.get("GEMINI_API_KEY")
    except Exception:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            sys.exit("No Gemini key found. Set the GEMINI_API_KEY environment variable.")
        return key


# ======================================================================
# 1. Read the documents: check which PDFs have text, OCR the scanned ones
# ======================================================================

def find_scanned_pdfs(pdf_files):
    """A scanned PDF is a set of photos: pypdf finds 0 characters of text in it. Return those file names."""
    needs_ocr = []
    for pdf in pdf_files:
        reader = PdfReader(str(pdf))
        chars = sum(len(page.extract_text() or "") for page in reader.pages)
        print(f"{pdf.name}: {len(reader.pages)} pages, {chars:,} characters of text")
        if chars == 0:
            needs_ocr.append(pdf.name)
    return needs_ocr


OCR_PROMPT = """Transcribe ALL text in this PDF exactly as printed.
Do not summarize, translate, or correct anything, and keep every number exactly as written.
Start each page with a line like: === PAGE 1 === (number = the page's position in the PDF, starting at 1).
If a page has no text, write [no text] under its page line."""


def ocr_scanned_pdfs(needs_ocr):
    """Transcribe each scanned PDF with Gemini and save it in data/ocr_text/ (skipped if already saved).
    Always spot-check the saved text against the original PDF: a wrong number here becomes a wrong answer later."""
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    for name in needs_ocr:
        out_file = OCR_DIR / f"{Path(name).stem}.txt"
        if out_file.exists():
            print(f"{name}: already transcribed, skipping")
            continue
        uploaded = client.files.upload(file=str(DOCS_DIR / name))   # send the PDF to Gemini
        resp = client.models.generate_content(
            model=MODEL,
            contents=[uploaded, OCR_PROMPT],
            config=types.GenerateContentConfig(temperature=0),   # 0 = most literal output
        )
        out_file.write_text(resp.text, encoding="utf-8")
        print(f"{name}: {len(resp.text):,} characters saved")


# ======================================================================
# 2. Pages -> chunks -> searchable library
# ======================================================================

def split_ocr_pages(raw):
    """Cut an OCR text file into (page number, text) pairs using the === PAGE n === markers."""
    parts = re.split(r"=== PAGE (\d+) ===", raw)
    # re.split gives: [text before first marker, "1", text of page 1, "2", text of page 2, ...]
    return [(int(num), text.strip()) for num, text in zip(parts[1::2], parts[2::2])]


def build_pages(pdf_files, needs_ocr):
    """One record per page: {"source": file name, "page": number, "text": text}."""
    pages = []
    for pdf in pdf_files:
        if pdf.name in needs_ocr:
            raw = (OCR_DIR / f"{pdf.stem}.txt").read_text(encoding="utf-8")
            ocr_pages = split_ocr_pages(raw)
            expected = len(PdfReader(str(pdf)).pages)
            if len(ocr_pages) != expected:
                # A mismatch means a page marker is missing or duplicated, so page citations could be wrong.
                print(f"WARNING: {pdf.name} has {expected} pages but the transcription has {len(ocr_pages)}. "
                      "Delete its .txt file in data/ocr_text and run again.")
            for num, text in ocr_pages:
                pages.append({"source": pdf.name, "page": num, "text": text})
        else:
            reader = PdfReader(str(pdf))
            for i, page in enumerate(reader.pages, start=1):   # start=1 because humans count pages from 1
                pages.append({"source": pdf.name, "page": i, "text": (page.extract_text() or "").strip()})
    return pages


def build_chunks(pages):
    """Cut each page into pieces of about 1,000 characters. Each chunk keeps its source file and page."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,   # neighbouring chunks share 150 characters so a cut sentence keeps its meaning
        separators=["\n\n", "\n", ". ", " ", ""],   # prefer cutting at blank lines, then sentence ends
    )
    chunks = []
    for p in pages:
        if not p["text"] or p["text"] == "[no text]":
            continue   # skip empty pages
        for i, piece in enumerate(splitter.split_text(p["text"])):
            if len(piece.strip()) >= 30:   # drop tiny fragments such as a lone page number
                chunks.append({"id": f"{p['source']}-p{p['page']}-c{i}", "source": p["source"],
                               "page": p["page"], "text": piece.strip()})
    return chunks


def build_library(chunks):
    """Turn every chunk into numbers (an embedding) and store them in ChromaDB, rebuilt from scratch each run."""
    global embedder, collection
    import chromadb
    from sentence_transformers import SentenceTransformer

    embedder = SentenceTransformer(EMBED_MODEL)
    vectors = embedder.encode([c["text"] for c in chunks], batch_size=32,
                              normalize_embeddings=True, show_progress_bar=True).tolist()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Delete any old copy first, so re-running never crashes on duplicate ids or keeps stale chunks.
    if COLLECTION_NAME in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(COLLECTION_NAME)
    collection = chroma.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=vectors,
        metadatas=[{"source": c["source"], "page": c["page"]} for c in chunks],   # lets us cite pages later
    )
    print(f"Stored {collection.count()} chunks")


# ======================================================================
# 3. Finding the right pages for a question
# ======================================================================

# A short description of each document, so Gemini knows which products exist.
# Edit the legal-notice line if its description is wrong (I only know it by its file name).
DOCS_GUIDE = """Documents available:
- Britam Biashara Network Product Guide: business insurance (fire, theft/burglary, money, all risks, goods in transit, work injury, public liability), plus group medical, funeral, group life
- Jubilee Traders Comprehensive Insurance Policy (TCIP) brochure: one-package business insurance for shops and traders
- Jubilee J-Inue policy document: health insurance
- Kenya Microinsurance Policy Paper (final draft)
- Kenya legal notice (file ke-act-ln-2020-26)"""

REWRITE_PROMPT = f"""You prepare search queries for a retrieval system about Kenyan insurance.
{DOCS_GUIDE}

Rewrite the trader's message as 1 to 2 standalone English search queries.
- KEEP the topic words from the message (for example 'theft', 'premium rate', 'excluded'). Do not replace them with product names.
- Add a product's full name only when the message clearly names that product, or when it is ambiguous which Jubilee or Britam product is meant.
- Never answer the question. Only write the queries.
Return a JSON list of strings."""


def make_queries(question):
    """Return the list of search queries: the trader's own question first, then up to 2 rewrites."""
    rewrites = []
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=f"{REWRITE_PROMPT}\n\nTrader message: {question}",
            config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
        )
        parsed = json.loads(resp.text)
        if isinstance(parsed, list):   # only trust the output if it is really a list of strings
            rewrites = [q for q in parsed if isinstance(q, str)][:2]
    except Exception as e:
        print(f"(rewrite failed, using the original question only: {e})")
    return [question] + [q for q in rewrites if q != question]


def retrieve(question):
    """Find the chunks most relevant to the question. Returns [] when nothing is relevant enough."""
    best = {}   # chunk id -> best hit seen so far (a chunk may be found by more than one query)

    for query in make_queries(question):
        vec = embedder.encode(query, normalize_embeddings=True).tolist()
        res = collection.query(query_embeddings=[vec], n_results=TOP_K,
                               include=["documents", "metadatas", "distances"])
        for cid, doc, meta, dist in zip(res["ids"][0], res["documents"][0],
                                        res["metadatas"][0], res["distances"][0]):
            sim = 1 - dist   # the database gives distance; similarity = 1 - distance (higher = closer)
            if sim >= MIN_SIMILARITY and (cid not in best or sim > best[cid]["similarity"]):
                best[cid] = {"source": meta["source"], "page": meta["page"],
                             "text": doc, "similarity": sim}

    hits = sorted(best.values(), key=lambda h: h["similarity"], reverse=True)   # best matches first
    return hits[:MAX_RESULTS]


# ======================================================================
# 4. Reading what the trader tells us
# ======================================================================

PROFILE_PROMPT = """You read a message from a Kenyan trader asking about insurance and extract only the facts they stated.
Messages may be English, Kiswahili or Sheng. Return a JSON object with ONLY these keys:
- stall_type: "open_air" (open-air stall, tarpaulin, no walls), "temporary_structure" (wooden or mabati kiosk), "permanent_building" (stone or brick shop, 'duka ya mawe'), or null
- business_type: short English text such as "mitumba shoes", or null
- stock_value_kes: whole number, or null
- budget_amount_kes: the amount the trader says they can pay, as a whole number, or null
- budget_period: "day", "week" or "month" (the period for that amount), or null
- wants_cover_fire, wants_cover_theft, wants_cover_health, wants_cover_accident: true if the trader says they want it or worry about it, otherwise null
- dependents: whole number, or null
Use null for anything not clearly stated. Never guess."""

STALL_TYPES = {"open_air", "temporary_structure", "permanent_building"}
PERIODS = {"day", "week", "month"}
WANTS = ["wants_cover_fire", "wants_cover_theft", "wants_cover_health", "wants_cover_accident"]


def clean_profile(raw):
    """Keep only the fields we know, with valid values. Anything else from Gemini is thrown away."""
    out = {}
    if raw.get("stall_type") in STALL_TYPES:
        out["stall_type"] = raw["stall_type"]
    if isinstance(raw.get("business_type"), str) and raw["business_type"].strip():
        out["business_type"] = raw["business_type"].strip()
    for key in ("stock_value_kes", "budget_amount_kes", "dependents"):
        v = raw.get(key)
        # isinstance(v, bool) check: Python treats True as the number 1, which we don't want
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
            out[key] = int(v)
    if raw.get("budget_period") in PERIODS:
        out["budget_period"] = raw["budget_period"]
    for key in WANTS:
        if raw.get(key) is True:   # we only store a "want" when it is clearly True; missing means "not mentioned"
            out[key] = True
    return out


def extract_profile(message):
    """Ask Gemini to fill in the form from the trader's message. Returns {} if anything goes wrong."""
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=f"{PROFILE_PROMPT}\n\nTrader message: {message}",
            config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
        )
        parsed = json.loads(resp.text)
        return clean_profile(parsed) if isinstance(parsed, dict) else {}
    except Exception as e:
        print(f"(profile extraction failed: {e})")
        return {}


# ======================================================================
# 5. The rules (plain Python, no AI)
# ======================================================================

TCIP_SRC = "TCIP-BROCHURE.pdf, p.1"
BRITAM_SRC = "BRITAM-PRODUCTS-PROFILE-Final-Final.pdf, p.7"
DB_SRC = "ReCover_Microinsurance_Product_Matching_Database.xlsx (Products P001/P002)"

TCIP_MAX_STOCK = 15_000_000   # KES; the brochure's limit for contents and stock
# search word -> readable label. A short word such as "jewel" also catches jewellery, jeweller, jewelry.
TCIP_EXCLUDED = {
    "bank": "banks",
    "forex": "forex bureaux",
    "jewel": "jewellery shops",
    "manufactur": "premises where manufacturing is carried out",
}
STALL_WORDS = {
    "open_air": "an open-air stall",
    "temporary_structure": "a temporary (wooden or mabati) kiosk",
    "permanent_building": "a permanent stone or brick shop",
}
ORDER = {"may_qualify": 0, "needs_confirmation": 1, "does_not_meet": 2}   # best to worst


def worse(a, b):
    """Return the more serious of two statuses, so one failed check is never overwritten by a later pass."""
    return a if ORDER[a] >= ORDER[b] else b


def monthly_budget(profile):
    """Convert the trader's budget to KES per month. Returns None if amount or period is missing."""
    amount, period = profile.get("budget_amount_kes"), profile.get("budget_period")
    if amount is None or period is None:
        return None
    factor = {"month": 1, "week": 52 / 12, "day": 7 * 52 / 12}[period]
    return round(amount * factor)


def check_tcip(profile):
    """Check the trader against the Jubilee TCIP brochure."""
    status, reasons = "may_qualify", []
    stall = profile.get("stall_type")
    stock = profile.get("stock_value_kes")
    business = (profile.get("business_type") or "").lower()

    # Check 1: stock value above the policy limit
    if stock is not None and stock > TCIP_MAX_STOCK:
        status = worse(status, "does_not_meet")
        reasons.append((f"Stock of KES {stock:,} is above the KES {TCIP_MAX_STOCK:,} limit for contents and stock.", TCIP_SRC))

    # Check 2: excluded business type (a keyword match on free text, so we say "appears to match")
    for keyword, label in TCIP_EXCLUDED.items():
        if keyword in business:
            status = worse(status, "does_not_meet")
            reasons.append((f"'{profile['business_type']}' appears to match an excluded business ({label}).", TCIP_SRC))

    # Check 3: the premises. A missing fact gives needs_confirmation, never a guess.
    if stall is None:
        status = worse(status, "needs_confirmation")
        reasons.append(("Premises should have walls of reinforced concrete, concrete blocks, bricks or stone, and a hard roof of tiles, cement or metal sheets. The trader's premises type was not stated.", TCIP_SRC))
    elif stall == "permanent_building":
        # Stays may_qualify: the brochure also requires a hard roof, which the trader hasn't told us about.
        reasons.append(("Stone or brick walls match the wall rule. The roof must be tiles, cement or metal sheets; the roof was not stated.", TCIP_SRC))
    else:
        status = worse(status, "does_not_meet")
        reasons.append((f"Premises should have walls of reinforced concrete, concrete blocks, bricks or stone. {STALL_WORDS[stall].capitalize()} does not match that.", TCIP_SRC))

    # The brochure gives no premium, so say so instead of letting anyone guess one.
    reasons.append(("The brochure does not state a premium.", TCIP_SRC))
    return {"product": "Jubilee Traders Comprehensive Insurance Policy (TCIP)", "status": status, "reasons": reasons}


def check_britam(profile):
    """Check the trader against the Britam Biashara guide. Always needs_confirmation, with the reason spelled out."""
    stall = profile.get("stall_type")
    reasons = [("The guide says the cover applies to all occupations other than the defined exclusions, but it does not list those exclusions or any stall-type rule.", BRITAM_SRC)]
    if stall == "open_air":
        reasons.append(("Open-air stall eligibility must be confirmed in writing by the insurer; do not assume it is covered.", DB_SRC))
    elif stall == "temporary_structure":
        reasons.append(("The guide does not say whether a temporary kiosk qualifies; the insurer must confirm in writing.", BRITAM_SRC))
    else:
        reasons.append(("Eligibility for the trader's premises must be confirmed with the insurer.", DB_SRC))
    reasons.append(("The guide gives premium rates (percentages), not a flat premium, and does not say what amount the rate applies to. A quote is needed.", "BRITAM-PRODUCTS-PROFILE-Final-Final.pdf, p.8"))
    return {"product": "Britam Biashara Cover", "status": "needs_confirmation", "reasons": reasons}


def run_rules(profile):
    """Run every product check, and build one note about the budget. Returns (results, budget_note)."""
    results = [check_tcip(profile), check_britam(profile)]
    monthly = monthly_budget(profile)
    note = None
    if monthly is not None:
        # We cannot say whether a product "fits": neither document gives a flat premium.
        note = (f"The trader's budget is about KES {monthly:,} per month. Neither document gives a flat premium, "
                "so we cannot say whether a product fits the budget until the insurer gives a quote.")
    return results, note


def run_rule_tests():
    """Quick checks that need no internet or API key. If a rule breaks, the program stops with an error."""
    r, _ = run_rules({"stall_type": "permanent_building", "stock_value_kes": 300000})
    assert r[0]["status"] == "may_qualify" and r[1]["status"] == "needs_confirmation"

    r, _ = run_rules({"stall_type": "temporary_structure", "business_type": "mitumba shoes"})
    assert r[0]["status"] == "does_not_meet"

    r, note = run_rules({"stall_type": "permanent_building", "business_type": "jewellery",
                         "budget_amount_kes": 100, "budget_period": "week"})
    assert r[0]["status"] == "does_not_meet"

    assert run_rules({"stall_type": "permanent_building", "stock_value_kes": 20_000_000})[0][0]["status"] == "does_not_meet"
    assert run_rules({"stall_type": "open_air"})[0][0]["status"] == "does_not_meet"
    assert run_rules({})[0][0]["status"] == "needs_confirmation"      # nothing known -> ask, don't assume
    assert monthly_budget({"budget_amount_kes": 20, "budget_period": "day"}) == 607    # matches the workbook (about 606.67)
    assert monthly_budget({"budget_amount_kes": 100, "budget_period": "week"}) == 433
    assert monthly_budget({}) is None
    print(note)


# ======================================================================
# 6. The instructions Gemini must follow
# ======================================================================

SYSTEM = """You are 'ReCover', a plain-spoken insurance information assistant for informal traders in Kenya (for example mitumba sellers).

LANGUAGE: Reply in the language the trader used: English, Kiswahili, or a Swahili/English/Sheng mix. Keep it simple, no insurance jargon.

RULES (strict):
1. Use ONLY the EXCERPTS and RULE RESULTS provided. Every number, product name, limit and exclusion must come from them.
2. After each fact, cite its label, like [S1] or [R1]. Never cite a label that was not provided.
3. If the material does not answer part of the question, say clearly that the approved documents do not specify it. Do not guess or use general knowledge.
4. Premiums in the excerpts may be percentage rates. Quote the rate as printed. Do not calculate a premium. Say the exact premium needs a quote from the insurer.
5. If an excerpt looks unclear or contradictory (for example '15% (1.5%)'), say so instead of picking one.
6. Never promise a payout. Mention the conditions and exclusions shown in the material.
7. RULE RESULTS (labelled [R1], [R2]) come from checked rules and are authoritative for eligibility.
   - may_qualify: do NOT say 'yes, you qualify'. Say they may qualify and name what still has to be confirmed.
   - needs_confirmation: say the insurer must confirm eligibility.
   - does_not_meet: say the document's requirement is not met. Do not recommend that product.
8. If a BUDGET NOTE is given, repeat it. Never say a product fits or does not fit the budget.
9. Only mention a product if it is relevant to the question."""

# Shown when we found no relevant evidence. It is fixed text, so no AI call is made and nothing can be invented.
UNAVAILABLE = ("I don't have that information in the approved insurance documents, "
               "so I can't answer it without guessing.")


# ======================================================================
# 7. The chatbot
# ======================================================================

class ReCover:
    def __init__(self):
        self.profile = {}    # what the trader has told us so far
        self.history = []    # the trader's earlier messages (not the bot's long answers)

    def search_text(self, message):
        """Short follow-ups ('does that fit my budget?') are too vague to search alone,
        so with fewer than 8 words we attach the previous message."""
        if self.history and len(message.split()) < 8:
            return f"{self.history[-1]} {message}"
        return message

    def ask(self, message):
        # 1. Update the profile. A new value (for example a corrected stock figure) replaces the old one.
        self.profile.update(extract_profile(message))

        # 2. Find the evidence. No evidence = fixed message, no AI answer.
        hits = retrieve(self.search_text(message))
        if not hits:
            self.history.append(message)
            return UNAVAILABLE, []

        # 3. Run the rules, but only if the trader has told us something.
        results, budget_note = run_rules(self.profile) if self.profile else ([], None)

        # 4. Build the labelled material for Gemini.
        labelled = {}   # label -> readable source, used for the source list at the end
        rule_lines, excerpt_lines = [], []
        for i, r in enumerate(results, start=1):
            sources = list(dict.fromkeys(src for _, src in r["reasons"]))   # unique sources, in order
            labelled[f"R{i}"] = f"rules check: {r['product']} (based on {'; '.join(sources)})"
            lines = "\n".join(f"  - {text} ({src})" for text, src in r["reasons"])
            rule_lines.append(f"[R{i}] {r['product']}: status = {r['status']}\n{lines}")
        for i, h in enumerate(hits, start=1):
            labelled[f"S{i}"] = f"{h['source']}, p.{h['page']}"
            excerpt_lines.append(f"[S{i}] ({h['source']}, p.{h['page']})\n{h['text']}")

        prompt = (
            f"WHAT THE TRADER HAS TOLD US SO FAR: {self.profile or 'nothing yet'}\n\n"
            f"TRADER'S EARLIER MESSAGES: {self.history[-3:] or 'none'}\n\n"
            "RULE RESULTS:\n" + ("\n\n".join(rule_lines) or "(none)") + "\n\n"
            f"BUDGET NOTE: {budget_note or '(none)'}\n\n"
            "EXCERPTS:\n" + "\n\n".join(excerpt_lines) + "\n\n"
            f"TRADER QUESTION: {message}"
        )
        resp = client.models.generate_content(
            model=MODEL, contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.2),   # low temperature = steady, factual
        )
        text = resp.text

        # 5. Find the labels the answer used. Gemini sometimes writes several in one bracket, like [S1, R1],
        #    so we read everything inside each [...] and pick out every S#/R# label.
        cited = []
        for group in re.findall(r"\[([^\]]+)\]", text):
            for label in re.findall(r"[SR]\d+", group):
                if label not in cited:
                    cited.append(label)
        sources = [f"[{c}] {labelled[c]}" for c in cited if c in labelled]

        self.history.append(message)
        return text, sources


def chat(bot, message):
    """Send one message and print the answer with its sources."""
    print(f"Trader: {message}\n")
    text, sources = bot.ask(message)
    print(f"ReCover: {text}\n")
    if sources:
        print("Sources:\n  " + "\n  ".join(sources))
    print("\n" + "=" * 70 + "\n")


# ======================================================================
# 8. Ways to run it
# ======================================================================

def run_demo():
    """A few example conversations."""
    bot = ReCover()
    chat(bot, "Niko na kibanda ya mitumba viatu Gikomba, ni mabati na stock yangu ni 300,000 bob. Nataka bima ya moto.")
    chat(bot, "My budget ni around 500 bob a month. Je, hiyo bima inatoshea bajeti yangu?")
    bot2 = ReCover()
    chat(bot2, "Nina duka ya mawe Gikomba. Je, Jubilee TCIP inanikubali?")
    chat(bot2, "Who will win the football match on Sunday?")
    bot3 = ReCover()
    chat(bot3, "What is the premium rate for theft cover?")
    chat(bot3, "How much is the monthly premium for Jubilee TCIP?")


def load_trader_questions():
    """Read the Trader_Questions sheet. The real table starts a few rows down, so we find the header row by looking for 'ID'."""
    workbook = next(REPO_ROOT.rglob("Microinsurance_Data_Collection_Workbook.xlsx"), None)
    if workbook is None:
        raise FileNotFoundError("Microinsurance_Data_Collection_Workbook.xlsx was not found in the repo.")
    raw = pd.read_excel(workbook, sheet_name="Trader_Questions", header=None)
    header_row = next(i for i, row in raw.iterrows() if str(row.iloc[0]).strip() == "ID")
    df = pd.read_excel(workbook, sheet_name="Trader_Questions", header=header_row)
    df = df[df["ID"].astype(str).str.match(r"Q\d+")]       # keep only the real question rows
    df = df.copy()
    # Q12 contains a placeholder; fill in an example amount so it can be asked
    df["Question (English)"] = df["Question (English)"].str.replace("[amount]", "150", regex=False)
    return df


def run_test_questions(limit):
    """Run the workbook's trader questions (each in a fresh conversation) and save the answers to
    data/test_results.csv so a person can check them against the documents. limit=0 runs all of them."""
    questions = load_trader_questions()
    if limit:
        questions = questions.head(limit)
    rows = []
    for _, q in questions.iterrows():
        try:
            text, sources = ReCover().ask(q["Question (English)"])   # a new ReCover() per question = no memory carried over
        except Exception as e:
            text, sources = f"ERROR: {e}", []
        rows.append({"id": q["ID"], "category": q["Category"], "question": q["Question (English)"],
                     "answer": text, "sources": " | ".join(sources)})
        print(f"{q['ID']}: {q['Question (English)']}\n  -> {text[:200]}...\n")
    Path("data").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv("data/test_results.csv", index=False)
    print("Saved data/test_results.csv")


def interactive_chat():
    """Chat in the terminal. Type 'new' to start a fresh conversation, 'quit' to leave."""
    bot = ReCover()
    print("\nReCover is ready. Ask a question. Type 'new' for a new conversation or 'quit' to leave.")
    while True:
        try:
            message = input("\nTrader: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not message:
            continue
        if message.lower() in {"quit", "exit"}:
            break
        if message.lower() == "new":
            bot = ReCover()
            print("Started a new conversation.")
            continue
        text, sources = bot.ask(message)
        print(f"\nReCover: {text}")
        if sources:
            print("\nSources:\n  " + "\n  ".join(sources))


def main():
    global client
    parser = argparse.ArgumentParser(description="ReCover insurance information chatbot")
    parser.add_argument("--demo", action="store_true", help="run the demo conversations instead of chatting")
    parser.add_argument("--test-questions", type=int, nargs="?", const=5, default=None, metavar="N",
                        help="run the first N workbook trader questions (0 = all; default 5)")
    args = parser.parse_args()

    run_rule_tests()
    print("All rule tests passed.\n")

    setup_repo()
    client = genai.Client(api_key=get_api_key())

    pdf_files = sorted(DOCS_DIR.glob("*.pdf"))
    needs_ocr = find_scanned_pdfs(pdf_files)
    ocr_scanned_pdfs(needs_ocr)
    pages = build_pages(pdf_files, needs_ocr)
    chunks = build_chunks(pages)
    print(f"{len(pages)} pages, {len(chunks)} chunks")
    build_library(chunks)

    if args.demo:
        run_demo()
    elif args.test_questions is not None:
        run_test_questions(args.test_questions)
    else:
        interactive_chat()


if __name__ == "__main__":
    main()