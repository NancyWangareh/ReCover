
from typing import List, Dict, Any
from google import genai
from .config import GEMINI_MODEL, get_api_key


LOCALIZED_FALLBACKS = {
    "en": (
        "I don't have verified information about that topic "
        "in the approved microinsurance documents. "
        "I can help explain insurance terms, policy conditions "
        "and claims procedures."
    ),

    "sw": (
        "Samahani, sina maelezo yaliyothibitishwa kuhusu "
        "swali hilo kwenye nyaraka rasmi za bima. "
        "Naweza kukusaidia kuelewa masharti ya bima, "
        "malipo na taratibu za kudai fidia."
    ),

    "sheng": (
        "Sina hiyo info kwa ma-doc rasmi za bima, "
        "so sitaki kukupea story za jaba. "
        "Naweza kukusaidia kuelewa vile bima inawork "
        "na vile unaclaim ukipata loss."
    )
}


EDUCATIONAL_SYSTEM_PROMPT = """
You are ReCover, a friendly and knowledgeable
microinsurance educational assistant for informal
traders in Kenya.

YOUR PERSONALITY:

You communicate like a helpful, approachable
insurance consultant who understands the realities
of informal businesses.

You are warm, empathetic, respectful and conversational.

CONVERSATION STYLE:

1. Speak naturally, not like a textbook or research report.
2. Mirror the trader's language: English, Kiswahili or Sheng.
3. Use familiar Kenyan expressions naturally where appropriate.
4. Explain complicated insurance terminology using
   simple everyday examples.
5. Use short paragraphs and numbered lists only when useful.
6. Avoid unnecessarily long responses.
7. Avoid repeating information already explained.
8. Ask at most ONE relevant follow-up question at a time.
9. Never ask for information the trader has already provided.

CONTEXT AWARENESS:

Use conversation history to understand the trader's
business, previous questions and information already shared.

When the trader refers to something mentioned earlier,
retrieve the relevant information from conversation history.

Do not ask the trader to repeat previously provided details.

GROUNDING AND ACCURACY:

1. Use ONLY the supplied document excerpts for
   insurance-specific factual claims.
2. Do not invent premiums, coverage limits, exclusions,
   waiting periods or eligibility conditions.
3. Do not guarantee insurance approval or compensation.
4. Do not imply that a trader automatically qualifies
   for insurance.
5. Do not present general insurance practices as
   confirmed conditions of a specific policy.
6. Preserve source citations using labels such as [S1], [S2].
7. If information is unavailable, communicate that honestly.

EDUCATIONAL APPROACH:

Your purpose is to improve insurance literacy.

Use familiar analogies such as:
- Chama for risk pooling.
- Mitumba bales for explaining stock losses.
- Daily business expenses for explaining premiums.

Avoid sounding like an insurance salesperson.

CONVERSATION FLOW:

When a trader asks a question:
- Answer the question directly.
- Explain what it means for their business.
- Ask a relevant follow-up only when necessary.

When a trader provides information:
- Acknowledge it.
- Connect it to previously shared information.
- Continue naturally.

When a trader says thank you:
- Respond warmly and briefly.
- Do not unnecessarily introduce another question.

Return ONLY the response intended for the trader.
"""


def generate_educational_answer(
    message: str,
    interpretation: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    history: List[Dict[str, Any]]
) -> str:

    lang = interpretation.get("detected_language", "en")

    if lang == "mixed":
        lang = "sw"

    intent = interpretation.get("intent", "definition")

    # Handle greetings and casual conversation
    if intent == "general_conversation":
        text = message.lower().strip()

        if lang == "sw":
            if any(word in text for word in ["asante", "shukrani"]):
                return "Karibu! 😊 Kuna jambo lingine kuhusu bima ungependa kufahamu?"
            return (
                "Habari! Karibu ReCover. 😊 "
                "Naweza kukusaidia kuelewa bima ya biashara, "
                "masharti ya sera, malipo na madai. Ungependa kujua nini?"
            )

        if lang == "sheng":
            if any(word in text for word in ["asante", "thanks"]):
                return "Karibu! 😊 Kuna kitu ingine kuhusu bima unataka kujua?"
            return (
                "Niaje! Karibu ReCover. 😊 "
                "Naweza kukuexplainia vile bima ya biashara inawork, "
                "malipo na claims. Unataka kujua nini?"
            )

        if any(word in text for word in ["thank you", "thanks"]):
            return (
                "You're welcome! 😊 Is there anything else about "
                "business insurance I can help you understand?"
            )

        return (
            "Hello! Welcome to ReCover. 😊 "
            "I can help you understand business microinsurance, "
            "policy terms, premiums, exclusions and claims. "
            "What would you like to know?"
        )

    if intent == "out_of_domain" or not evidence:
        return LOCALIZED_FALLBACKS.get(
            lang,
            LOCALIZED_FALLBACKS["en"]
        )

    client = genai.Client(api_key=get_api_key())

    evidence_text = "\n\n".join(
        f"[S{i+1}] Source: {e['source']}, "
        f"Page {e['page']}\n{e['text']}"
        for i, e in enumerate(evidence)
    )

    history_text = "\n".join(
        f"{'Trader' if t['role'] == 'user' else 'ReCover'}: "
        f"{t['text']}"
        for t in history[-8:]
    ) if history else "This is the beginning of the conversation."

    user_prompt = f"""
CONVERSATION HISTORY:

{history_text}

RETRIEVED INSURANCE DOCUMENTS:

{evidence_text}

LATEST TRADER MESSAGE:

{message}

INTERPRETATION:

Detected language: {lang}

Core concept: {interpretation.get('core_concept', '')}

Resolved query: {interpretation.get('resolved_query', message)}

YOUR TASK:

Respond to the trader's latest message.

Consider the conversation history when formulating
your response.

Do not repeat questions that have already been answered.

Be natural, conversational and informative.

Use the retrieved documents as your factual source.

If appropriate, ask ONE relevant follow-up question.

Remember that you are helping the trader understand
microinsurance, not selling an insurance policy.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config={
            "temperature": 0.4,
            "system_instruction": EDUCATIONAL_SYSTEM_PROMPT
        }
    )

    return response.text.strip()
