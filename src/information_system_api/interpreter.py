import json
from typing import Dict, Any, List
from google import genai
from .config import GEMINI_MODEL, get_api_key

INTERPRET_PROMPT = """You are an intent and query interpreter for ReCover, an educational microinsurance chatbot for Kenyan informal traders.
Analyze the user's message in the context of recent turns.

Recent Conversation:
__HISTORY_CONTEXT__

Current User Message: "__MESSAGE__"

Output strict JSON with these keys:
{
  "detected_language": "en" | "sw" | "sheng" | "mixed",
  "intent": "definition" | "process" | "condition_or_exclusion" | "claims" | "out_of_domain",
  "core_concept": "Short summary of the core insurance topic",
  "resolved_query": "The question rephrased clearly to resolve any pronouns (like 'it', 'that')",
  "search_queries": ["1 to 2 targeted English search queries for retrieving policy documents"]
}
"""

def interpret_user_intent(message: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = genai.Client(api_key=get_api_key())
    
    lines = []
    for turn in history[-4:]:
        role = "Trader" if turn["role"] == "user" else "ReCover"
        lines.append(f"{role}: {turn['text']}")
    history_context = "\n".join(lines) if lines else "No previous turns."

    prompt = (
        INTERPRET_PROMPT
        .replace("__HISTORY_CONTEXT__", history_context)
        .replace("__MESSAGE__", message)
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    try:
        return json.loads(response.text)
    except Exception:
        return {
            "detected_language": "en",
            "intent": "definition",
            "core_concept": message,
            "resolved_query": message,
            "search_queries": [message]
        }