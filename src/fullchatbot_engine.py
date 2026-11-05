import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from google import genai
from google.genai import types
import requests
from sentence_transformers import SentenceTransformer

# ----------------- CONFIGURATION -----------------
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "recover_docs"
CHROMA_PATH = "data/chroma_db"
MIN_SIMILARITY = 0.30
TOP_K = 4
MAX_RESULTS = 5
RECOMMENDER_URL = "https://recover-rwf9.onrender.com/recommend"
RECOMMENDER_TIMEOUT = 90

# ----------------- CITATIONS & METADATA -----------------
TCIP_SRC = "TCIP-BROCHURE.pdf, p.1"
BRITAM_SRC = "BRITAM-PRODUCTS-PROFILE-Final-Final.pdf, p.7"
DB_SRC = "ReCover_Microinsurance_Product_Matching_Database.xlsx (Products P001/P002)"
SRC_REC = (
    "ReCover recommendation service (Britam Biashara Lite plan table collected by the team; "
    "prices not yet checked against the brochure)"
)

TCIP_MAX_STOCK = 15_000_000
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
ORDER = {"may_qualify": 0, "needs_confirmation": 1, "does_not_meet": 2}

LANG_RULE = {
    "en": "Respond entirely in clear, plain English.",
    "sw": "Jibu kwa Kiswahili rahisi kueleweka. Epuka maneno magumu ya kisheria.",
    "sheng": "Respond in natural Kenyan code-switching (English, Swahili and common Sheng like 'bob', 'kibanda', 'moto').",
}

QUESTION_GROUPS = [
    ["risks", "stock_value_kes"],
    ["budget", "preferred_premium_frequency"],
    ["monthly_income_kes", "income_receipt_pattern", "income_variability"],
    ["restock_cycle_days", "total_loss_24m_kes"],
]

FIELD_QUESTIONS = {
    "risks": "which business risk they want cover for: fire, theft, or both (recommendations are only available for fire and theft on business stock for now)",
    "stock_value_kes": "roughly how much their stock is worth, in KES",
    "budget": "how much they can pay for insurance, and how often (per day, per week or per month)",
    "preferred_premium_frequency": "how they would prefer to pay: daily, weekly, monthly, or when they restock",
    "monthly_income_kes": "about how much they earn in a month, in KES",
    "income_receipt_pattern": "whether their money comes in daily, weekly or monthly",
    "income_variability": "whether their income is steady, changes sometimes, or changes a lot",
    "restock_cycle_days": "how many days there are between restocking",
    "total_loss_24m_kes": "roughly how much they lost to fire, theft or similar in the last 2 years, in KES (0 if nothing)",
}

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

PROFILE_PROMPT = """You read a message from a Kenyan trader talking to an insurance assistant and extract only what they stated.
Messages may be English, Kiswahili or Sheng. Return a JSON object with ONLY these keys:
- language: "en", "sw" (Kiswahili) or "sheng" (mixed Swahili/English/Sheng)
- intent: "recommendation" if the trader asks which plan or product to buy, asks for suggestions or options for their business, or is answering questions about their business and money; otherwise "information"
- stall_type: "open_air" (open-air stall, tarpaulin, no walls), "temporary_structure" (wooden or mabati kiosk), "permanent_building" (stone or brick shop, 'duka ya mawe'), or null
- business_type: short English text such as "mitumba shoes", or null
- stock_value_kes: whole number, or null
- budget_amount_kes: the amount the trader says they can pay for insurance, as a whole number, or null
- budget_period: "day", "week" or "month" (the period for that amount), or null
- wants_cover_fire, wants_cover_theft, wants_cover_health, wants_cover_accident: true if the trader says they want it or worry about it, otherwise null
- dependents: whole number, or null
- monthly_income_kes: what the trader earns in a month, whole number, or null
- income_receipt_pattern: how often money comes in: "daily", "weekly" or "monthly", or null
- income_variability: "low" (steady), "medium" (changes sometimes) or "high" (changes a lot), or null
- restock_cycle_days: whole number of days between restocking, or null
- total_loss_24m_kes: money or stock lost to fire, theft or similar in the last 2 years, whole number (0 if the trader says they lost nothing), or null if not mentioned
- preferred_premium_frequency: how they prefer to pay: "daily", "weekly", "monthly" or "pay_at_restock" (pays when they restock), or null
- primary_risk_concern: the one risk worrying them most: "fire", "theft", "health", "weather_flood", "accident" or "other", or null
Use null for anything not clearly stated. Never guess."""

SYSTEM_INFO = """You are 'ReCover', a plain-spoken insurance information assistant for informal traders in Kenya (for example mitumba sellers).

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

SYSTEM_REC = """You are 'ReCover', a plain-spoken insurance assistant for informal traders in Kenya (for example mitumba sellers).
You explain the plan options below. They come from the team's recommendation service.

RULES (strict):
1. Use ONLY the RECOMMENDATION RESULTS and NOTES. Copy every number exactly as given. Never calculate or change a number. Never mention a plan that is not in the results.
2. After each fact, cite its label, like [A1]. Never cite a label that was not provided.
3. Present the plans as options to explore, not as guaranteed or best-for-sure. Never promise a payout or an approval.
4. State each plan's annual, monthly and weekly premium and cover limit as given, and say whether it is within the trader's budget as reported.
5. Follow every line in NOTES. If a note says every plan is above the budget, say that plainly and do not hide it.
6. Mention the suggested payment schedule, and that the insurer must confirm it.
7. Do not mention clusters, models, scores or how the service works internally.
8. Follow the ACTIVE LANGUAGE instruction. Keep it short and simple, like a WhatsApp message."""

UNAVAILABLE = (
    "I don't have that information in the approved insurance documents, "
    "so I can't answer it without guessing."
)

# ----------------- DETERMINISTIC RULES & HELPERS -----------------
def worse(a: str, b: str) -> str:
    return a if ORDER[a] >= ORDER[b] else b

def monthly_budget(profile: Dict[str, Any]) -> Optional[int]:
    amount = profile.get("budget_amount_kes")
    period = profile.get("budget_period")
    if amount is None or period is None:
        return None
    factor = {"month": 1, "week": 52 / 12, "day": 7 * 52 / 12}[period]
    return round(amount * factor)

def check_tcip(profile: Dict[str, Any]) -> Dict[str, Any]:
    status, reasons = "may_qualify", []
    stall = profile.get("stall_type")
    stock = profile.get("stock_value_kes")
    business = (profile.get("business_type") or "").lower()

    if stock is not None and stock > TCIP_MAX_STOCK:
        status = worse(status, "does_not_meet")
        reasons.append((f"Stock of KES {stock:,} is above the KES {TCIP_MAX_STOCK:,} limit for contents and stock.", TCIP_SRC))

    for keyword, label in TCIP_EXCLUDED.items():
        if re.search(r'\b' + re.escape(keyword), business):
            status = worse(status, "does_not_meet")
            reasons.append((f"'{profile['business_type']}' appears to match an excluded business ({label}).", TCIP_SRC))

    if stall is None:
        status = worse(status, "needs_confirmation")
        reasons.append(("Premises should have walls of reinforced concrete, concrete blocks, bricks or stone, and a hard roof of tiles, cement or metal sheets. The trader's premises type was not stated.", TCIP_SRC))
    elif stall == "permanent_building":
        reasons.append(("Stone or brick walls match the wall rule. The roof must be tiles, cement or metal sheets; the roof was not stated.", TCIP_SRC))
    else:
        status = worse(status, "does_not_meet")
        reasons.append((f"Premises should have walls of reinforced concrete, concrete blocks, bricks or stone. {STALL_WORDS[stall].capitalize()} does not match that.", TCIP_SRC))

    reasons.append(("The brochure does not state a premium.", TCIP_SRC))
    return {"product": "Jubilee Traders Comprehensive Insurance Policy (TCIP)", "status": status, "reasons": reasons}

def check_britam(profile: Dict[str, Any]) -> Dict[str, Any]:
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

def run_rules(profile: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    results = [check_tcip(profile), check_britam(profile)]
    monthly = monthly_budget(profile)
    note = None
    if monthly is not None:
        note = (
            f"The trader's budget is about KES {monthly:,} per month. Neither document gives a flat premium, "
            "so we cannot say whether a product fits the budget until the insurer gives a quote."
        )
    return results, note

def missing_fields(profile: Dict[str, Any]) -> List[str]:
    missing = []
    if not (profile.get("wants_cover_fire") or profile.get("wants_cover_theft")):
        missing.append("risks")
    if profile.get("stock_value_kes") is None or profile.get("stock_value_kes") <= 0:
        missing.append("stock_value_kes")
    if monthly_budget(profile) is None:
        missing.append("budget")
    for key in ["preferred_premium_frequency", "monthly_income_kes", "income_receipt_pattern", "income_variability"]:
        if profile.get(key) is None:
            missing.append(key)
    if profile.get("restock_cycle_days") is None or profile.get("restock_cycle_days") <= 0:
        missing.append("restock_cycle_days")
    if profile.get("total_loss_24m_kes") is None:
        missing.append("total_loss_24m_kes")
    return missing

def next_question_fields(missing: List[str]) -> List[str]:
    for group in QUESTION_GROUPS:
        fields = [f for f in group if f in missing]
        if fields:
            return fields
    return []

def build_payload(profile: Dict[str, Any]) -> Dict[str, Any]:
    fire = bool(profile.get("wants_cover_fire"))
    theft = bool(profile.get("wants_cover_theft"))
    return {
        "stock_value_kes": float(profile["stock_value_kes"]),
        "total_loss_24m_kes": float(profile["total_loss_24m_kes"]),
        "monthly_income_kes": float(profile["monthly_income_kes"]),
        "wtp_monthly_kes": float(monthly_budget(profile)),
        "restock_cycle_days": int(profile["restock_cycle_days"]),
        "primary_risk_concern": (
            profile.get("primary_risk_concern")
            if profile.get("primary_risk_concern") in {"fire", "theft"}
            else ("fire" if fire else "theft")
        ),
        "wants_cover_fire": fire,
        "wants_cover_theft": theft,
        "income_variability": profile["income_variability"],
        "preferred_premium_frequency": profile["preferred_premium_frequency"],
        "income_receipt_pattern": profile["income_receipt_pattern"],
    }

def call_recommender(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for attempt in (1, 2):
        try:
            resp = requests.post(RECOMMENDER_URL, json=payload, timeout=RECOMMENDER_TIMEOUT)
            if resp.status_code == 200 and resp.json().get("success"):
                return resp.json()["result"]
        except Exception:
            pass
    return None

def recommendation_facts(result: Dict[str, Any], profile: Dict[str, Any]) -> Tuple[Dict[str, str], List[str], List[str]]:
    labelled, lines, notes = {}, [], []
    priced = above_budget = 0

    for n, r in enumerate(result.get("recommendations", []), start=1):
        label = f"A{n}"
        labelled[label] = SRC_REC
        if "product_name" not in r:
            lines.append(f"[{label}] No suitable plan found for {r.get('risk_type', 'this risk')}: {r.get('message', 'no detail given')}")
            continue
        annual = float(r["annual_premium_kes"])
        monthly = float(r.get("monthly_premium_equivalent_kes", annual / 12))
        status = r.get("affordability_status", "unknown")
        priced += 1
        if status != "Within stated WTP":
            above_budget += 1
        lines.append(
            f"[{label}] Cover for {r.get('risk_type')}: Britam Biashara Lite plan {r['product_name']}. "
            f"Annual premium KES {annual:,.0f} (about KES {monthly:,.0f} per month, KES {annual / 52:,.0f} per week). "
            f"Cover limit KES {float(r.get('coverage_limit_kes', 0)):,.0f} for stock of KES {float(r.get('stock_value_kes', 0)):,.0f}. "
            f"Affordability as reported: {status} (trader's budget about KES {float(r.get('monthly_wtp_kes', 0)):,.0f} per month)."
        )

    pay = result.get("payment_recommendation") or {}
    if pay:
        label = f"A{len(labelled) + 1}"
        labelled[label] = SRC_REC
        lines.append(
            f"[{label}] Payment schedule: suggested frequency {pay.get('recommended_frequency')} "
            f"({pay.get('reason')}). The insurer must confirm that this arrangement is allowed."
        )

    if priced and above_budget == priced:
        notes.append("EVERY plan listed is above the trader's stated monthly budget. Say this plainly.")
    notes.append("The prices come from the team's Britam Biashara Lite plan table, which has not yet been checked against the brochure. Tell the trader to confirm prices with Britam.")
    notes.append("Whether the trader's premises qualify must be confirmed in writing by Britam.")
    if profile.get("wants_cover_health") or profile.get("wants_cover_accident"):
        notes.append("The trader also mentioned health or accident cover. These plans cover fire and theft on business stock only. Say that other needs are not covered by this recommendation.")
    return labelled, lines, notes

def collect_sources(text: str, labelled: Dict[str, str]) -> List[str]:
    cited = []
    for group in re.findall(r"\[([^\]]+)\]", text):
        for label in re.findall(r"[SRA]\d+", group):
            if label not in cited:
                cited.append(label)
    return [f"[{c}] {labelled[c]}" for c in cited if c in labelled]


# ----------------- MAIN RECOVER ENGINE CLASS -----------------
class ReCover:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("No Gemini key found. Set GEMINI_API_KEY environment variable.")
        self.client = genai.Client(api_key=key)
        self.embedder = SentenceTransformer(EMBED_MODEL)
        self.chroma = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.chroma.get_or_create_collection(
            COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

        self.profile: Dict[str, Any] = {}
        self.history: List[str] = []
        self.language: str = "en"
        self.awaiting: bool = False

    def clean_profile(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        out = {}
        if raw.get("stall_type") in {"open_air", "temporary_structure", "permanent_building"}:
            out["stall_type"] = raw["stall_type"]
        if isinstance(raw.get("business_type"), str) and raw["business_type"].strip():
            out["business_type"] = raw["business_type"].strip()
        for key in ["stock_value_kes", "budget_amount_kes", "dependents", "monthly_income_kes", "restock_cycle_days", "total_loss_24m_kes"]:
            v = raw.get(key)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
                out[key] = int(v)
        if raw.get("budget_period") in {"day", "week", "month"}:
            out["budget_period"] = raw["budget_period"]
        for key, allowed in {
            "income_receipt_pattern": {"daily", "weekly", "monthly"},
            "income_variability": {"low", "medium", "high"},
            "preferred_premium_frequency": {"daily", "weekly", "monthly", "pay_at_restock"},
            "primary_risk_concern": {"fire", "theft", "health", "weather_flood", "accident", "other"},
        }.items():
            if raw.get(key) in allowed:
                out[key] = raw[key]
        for key in ["wants_cover_fire", "wants_cover_theft", "wants_cover_health", "wants_cover_accident"]:
            if raw.get(key) is True:
                out[key] = True
        return out

    def interpret_message(self, message: str) -> Dict[str, Any]:
        fallback = {"profile": {}, "language": "en", "intent": "information"}
        try:
            resp = self.client.models.generate_content(
                model=MODEL,
                contents=f"{PROFILE_PROMPT}\n\nTrader message: {message}",
                config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
            )
            raw = json.loads(resp.text)
            if not isinstance(raw, dict):
                return fallback
            return {
                "profile": self.clean_profile(raw),
                "language": raw.get("language") if raw.get("language") in {"en", "sw", "sheng"} else "en",
                "intent": raw.get("intent") if raw.get("intent") in {"recommendation", "information"} else "information",
            }
        except Exception:
            return fallback

    def make_queries(self, question: str) -> List[str]:
        rewrites = []
        try:
            resp = self.client.models.generate_content(
                model=MODEL,
                contents=f"{REWRITE_PROMPT}\n\nTrader message: {question}",
                config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
            )
            parsed = json.loads(resp.text)
            if isinstance(parsed, list):
                rewrites = [q for q in parsed if isinstance(q, str)][:2]
        except Exception:
            pass
        return [question] + [q for q in rewrites if q != question]

    def retrieve(self, question: str) -> List[Dict[str, Any]]:
        best = {}
        for query in self.make_queries(question):
            vec = self.embedder.encode(query, normalize_embeddings=True).tolist()
            res = self.collection.query(
                query_embeddings=[vec], n_results=TOP_K, include=["documents", "metadatas", "distances"]
            )
            if not res["ids"] or not res["ids"][0]:
                continue
            for cid, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
                sim = 1 - dist
                if sim >= MIN_SIMILARITY and (cid not in best or sim > best[cid]["similarity"]):
                    best[cid] = {"source": meta["source"], "page": meta["page"], "text": doc, "similarity": sim}
        return sorted(best.values(), key=lambda h: h["similarity"], reverse=True)[:MAX_RESULTS]

    def say(self, instruction: str, language: str, fallback: str, context: str = "") -> str:
        try:
            prompt = (
                f"{LANG_RULE[language]}\n"
                f"Context so far: {context}\n\n"
                f"Write ONE short, friendly message that does this: {instruction}\n"
                "Do not add facts, prices, product names or promises."
            )
            resp = self.client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are 'ReCover', a plain-spoken insurance assistant for Kenyan market traders.",
                    temperature=0.3,
                ),
            )
            return resp.text.strip()
        except Exception:
            return fallback

    def search_text(self, message: str) -> str:
        if self.history and len(message.split()) < 8:
            return f"{self.history[-1]} {message}"
        return message

    def inform(self, message: str) -> Tuple[str, List[str]]:
        hits = self.retrieve(self.search_text(message))
        if not hits:
            return UNAVAILABLE, []

        results, budget_note = run_rules(self.profile) if self.profile else ([], None)
        labelled = {}
        rule_lines, excerpt_lines = [], []

        for i, r in enumerate(results, start=1):
            sources = list(dict.fromkeys(src for _, src in r["reasons"]))
            labelled[f"R{i}"] = f"rules check: {r['product']} (based on {'; '.join(sources)})"
            lines = "\n".join(f"  - {text} ({src})" for text, src in r["reasons"])
            rule_lines.append(f"[R{i}] {r['product']}: status = {r['status']}\n{lines}")

        for i, h in enumerate(hits, start=1):
            labelled[f"S{i}"] = f"{h['source']}, p.{h['page']}"
            excerpt_lines.append(f"[S{i}] ({h['source']}, p.{h['page']})\n{h['text']}")

        prompt = (
            f"ACTIVE LANGUAGE: {LANG_RULE[self.language]}\n\n"
            f"WHAT THE TRADER HAS TOLD US SO FAR: {self.profile or 'nothing yet'}\n\n"
            f"TRADER'S EARLIER MESSAGES: {self.history[-3:] or 'none'}\n\n"
            "RULE RESULTS:\n" + ("\n\n".join(rule_lines) or "(none)") + "\n\n"
            f"BUDGET NOTE: {budget_note or '(none)'}\n\n"
            "EXCERPTS:\n" + "\n\n".join(excerpt_lines) + "\n\n"
            f"TRADER QUESTION: {message}"
        )

        resp = self.client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INFO, temperature=0.2),
        )
        return resp.text, collect_sources(resp.text, labelled)

    def recommend(self, message: str) -> Tuple[str, List[str]]:
        missing = missing_fields(self.profile)
        if missing:
            self.awaiting = True
            recent_context = " | ".join(self.history[-2:]) if self.history else "New conversation"
            fields = next_question_fields(missing)
            wanted = "; ".join(FIELD_QUESTIONS[f] for f in fields)
            instruction = f"say you will suggest insurance plans once you know a bit more about their business, and ask for ONLY these things: {wanted}"
            fallback = f"To suggest a plan I need a few more details. Please tell me {wanted}."
            return self.say(instruction, self.language, fallback, context=recent_context), []

        self.awaiting = False
        result = call_recommender(build_payload(self.profile))
        if result is None:
            return (
                self.say(
                    "tell the trader the recommendation service is not responding right now and ask them to try again in a few minutes",
                    self.language,
                    "Sorry, the recommendation service is not responding right now. Please try again in a few minutes.",
                ),
                [],
            )

        labelled, lines, notes = recommendation_facts(result, self.profile)
        prompt = (
            f"ACTIVE LANGUAGE: {LANG_RULE[self.language]}\n\n"
            f"WHAT THE TRADER HAS TOLD US: {self.profile}\n\n"
            "RECOMMENDATION RESULTS:\n" + "\n".join(lines) + "\n\n"
            "NOTES:\n" + "\n".join(f"- {n}" for n in notes) + "\n\n"
            f"TRADER MESSAGE: {message}"
        )
        resp = self.client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_REC, temperature=0.2),
        )
        return resp.text, collect_sources(resp.text, labelled)

    def ask(self, message: str) -> Tuple[str, List[str]]:
        meta = self.interpret_message(message)
        before = dict(self.profile)
        self.profile.update(meta["profile"])
        self.language = meta["language"]
        gained = [k for k, v in self.profile.items() if before.get(k) != v]

        if meta["intent"] == "recommendation" or (self.awaiting and gained):
            text, sources = self.recommend(message)
        else:
            text, sources = self.inform(message)

        self.history.append(message)
        return text, sources