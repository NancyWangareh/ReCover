from typing import List, Dict, Any, Tuple
from google import genai
from .config import GEMINI_MODEL, get_api_key

LOCALIZED_FALLBACKS = {
    "en": "I don't have verified information about that topic in the approved microinsurance documents. I am here to help explain insurance terms, claims steps, and policy rules.",
    "sw": "Sina maelezo yaliyothibitishwa kuhusu swali hilo kwenye nyaraka rasmi za bima. Niko hapa kukusaidia kuelewa maana ya bima, jinsi ya kulipa, na jinsi ya kudai fidia.",
    "sheng": "Sina hiyo info kwa ma-doc rasmi za bima, so sitaki kukupea story za jaba. Naweza kukusaidia kuelewa vile bima inawork, madeductibles, na vile unaclaim ukipata loss."
}

EDUCATIONAL_SYSTEM_PROMPT = """You are ReCover's Educational Assistant for informal traders in Kenya.
Your mission is to build genuine insurance literacy with empathy and clarity.

Core Behavioral Rules:
1. Grounding: Rely strictly on provided excerpts for rates, percentages, waiting periods, and formal conditions. Cite them using bracketed labels like [S1], [S2].
2. Intuitive Explanations: Use everyday Kenyan analogies (e.g., comparing risk pooling to a chama, or explaining deductibles using a damaged bale of mitumba clothes).
3. Objective Guidance: You are an educator, not an insurance broker. Do not state whether the trader qualifies or does not qualify for a product unless explicitly requested.
4. Tone & Language: Mirror the user's detected language (English, Kiswahili, or Sheng) naturally without stiff direct translations.
"""

def generate_educational_answer(
    message: str,
    interpretation: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    history: List[Dict[str, Any]]
) -> str:
    lang = interpretation.get("detected_language", "en")
    intent = interpretation.get("intent", "definition")

    if intent == "out_of_domain" or not evidence:
        return LOCALIZED_FALLBACKS.get(lang, LOCALIZED_FALLBACKS["en"])

    client = genai.Client(api_key=get_api_key())

    evidence_text = "\n\n".join(
        f"[S{i+1}] Source: {e['source']}, Page {e['page']}\n{e['text']}"
        for i, e in enumerate(evidence)
    )

    history_text = "\n".join(
        f"{'Trader' if t['role'] == 'user' else 'Educator'}: {t['text']}"
        for t in history[-4:]
    ) if history else "None"

    user_prompt = f"""Conversation Context:
{history_text}

Retrieved Document Excerpts:
{evidence_text}

User Question: "{message}"
Detected Language: {lang}

Explain the answer clearly to the trader following the system rules."""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            {"role": "user", "parts": [{"text": EDUCATIONAL_SYSTEM_PROMPT + "\n\n" + user_prompt}]}
        ],
        config={"temperature": 0.2}
    )
    return response.text.strip()