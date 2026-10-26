
import os
from google import genai
from google.genai import types

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


def generate_answer(question, context):
    """
    Generate a grounded answer using Gemini and retrieved evidence.
    """

    system_prompt = """
    You are ReCover, a microinsurance information assistant
    for users in Kenya.

    Answer using only the supplied document excerpts.

    For product questions:
    - Prioritize product names and providers.
    - Explain coverage where the evidence supports it.
    - Include exclusions, eligibility and premiums when available.
    - Do not invent missing information.
    - Cite the source document names.
    - If the evidence is insufficient, say so.
    - Prefer concise lists or tables over long background summaries.
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"""
        Question:
        {question}

        Retrieved document excerpts:
        {context}
        """,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            max_output_tokens=1200
        )
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text

