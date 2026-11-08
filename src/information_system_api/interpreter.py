
import json
from typing import Dict, Any, List
from google import genai
from .config import GEMINI_MODEL, get_api_key


INTERPRET_PROMPT = """
You are the intent and query interpreter for ReCover,
a conversational microinsurance assistant for Kenyan
informal traders.

Your responsibility is to understand what the trader
wants and interpret their message using conversation history.

RECENT CONVERSATION:
__HISTORY_CONTEXT__

CURRENT USER MESSAGE:
__MESSAGE__

AVAILABLE INTENTS:

1. recommendation:
The trader wants to find, compare or receive recommendations
for insurance products suitable for their business.

Examples:
- Which insurance is suitable for my stock?
- Nataka insurance ya moto.
- I have 150k stock, what cover can I get?
- Which insurance can I afford?

2. definition:
The trader wants to understand insurance concepts.

Examples:
- What is microinsurance?
- What does risk pooling mean?
- Explain insurance premiums.

3. process:
The trader wants to understand how an insurance process works.

Examples:
- How do I register?
- How do I pay premiums?
- How does insurance work?

4. condition_or_exclusion:
The trader asks about policy conditions, eligibility
or exclusions.

5. claims:
The trader asks about reporting losses or receiving
insurance compensation.

6. general_conversation:
Greetings, acknowledgements, appreciation and ordinary
conversation related to the ongoing interaction.

Examples:
- Hello.
- Thank you.
- Sawa.
- Okay.
- That's helpful.

7. out_of_domain:
Questions unrelated to ReCover's microinsurance purpose.

IMPORTANT CLASSIFICATION RULES:

- Consider conversation history before classifying.
- A short response such as "fire", "yes", "monthly"
  or "200" should be interpreted using previous turns.
- If the trader is answering a question asked by ReCover,
  maintain the context of the ongoing conversation.
- Do not classify every short response as out_of_domain.
- If the trader expresses interest in finding an insurance
  product, use recommendation.
- If the trader asks for an explanation of an insurance
  concept, use the appropriate educational intent.

LANGUAGE DETECTION:

Identify whether the trader is communicating in:
- en: English
- sw: Kiswahili
- sheng: Sheng
- mixed: A natural combination of languages.

OUTPUT:

Return strict JSON with these keys:

{
    "detected_language": "en",
    "intent": "recommendation",
    "core_concept": "Short description",
    "resolved_query": "The trader's complete interpreted request",
    "search_queries": [
        "First targeted English search query",
        "Second targeted English search query"
    ]
}

For general_conversation and out_of_domain,
search_queries can be an empty list.

Return JSON only.
"""


def interpret_user_intent(
    message: str,
    history: List[Dict[str, Any]]
) -> Dict[str, Any]:

    client = genai.Client(api_key=get_api_key())

    lines = []

    for turn in history[-8:]:

        role = (
            "Trader"
            if turn["role"] == "user"
            else "ReCover"
        )

        lines.append(f"{role}: {turn['text']}")

    history_context = (
        "\n".join(lines)
        if lines
        else "No previous conversation."
    )

    prompt = (
        INTERPRET_PROMPT
        .replace("__HISTORY_CONTEXT__", history_context)
        .replace("__MESSAGE__", message)
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    )

    try:

        interpretation = json.loads(response.text)

        valid_intents = {
            "recommendation",
            "definition",
            "process",
            "condition_or_exclusion",
            "claims",
            "general_conversation",
            "out_of_domain"
        }

        if interpretation.get("intent") not in valid_intents:
            raise ValueError("Invalid intent returned.")

        return interpretation

    except Exception:

        return {
            "detected_language": "en",
            "intent": "general_conversation",
            "core_concept": message,
            "resolved_query": message,
            "search_queries": []
        }
