import torch
from dotenv import load_dotenv
load_dotenv()
import os
import gc
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from google import genai

# 1. Initialize FastAPI app
app = FastAPI(title="ReCover Microinsurance Advisor API")

# 2. Permissive CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Persistent ChromaDB Client (Loaded ONCE at process startup, NOT inside endpoints)
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

# Retrieve the existing collection
try:
    collection = chroma_client.get_collection(name="recover_knowledge")
except Exception:
    collection = chroma_client.get_or_create_collection(name="recover_knowledge")

# 4. Initialize Gemini Client for Generation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable is not set.")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# 5. Request & Response Schemas (Preserved for Next.js frontend)
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Source(BaseModel):
    tag: str
    document: str
    page: int
    reference: str
    url: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []


# 6. Chat Endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    user_query = payload.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Retrieve top 3 relevant chunks from ChromaDB
        results = collection.query(
            query_texts=[user_query],
            n_results=3
        )

        documents = results.get("documents", [[]])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

        context_blocks = []
        sources = []

        for idx, doc in enumerate(documents):
            tag = f"[S{idx+1}]"
            context_blocks.append(f"{tag}: {doc}")

            # Extract metadata safely with fallbacks
            meta = metadatas[idx] if idx < len(metadatas) and isinstance(metadatas[idx], dict) else {}

            doc_title = (
                meta.get("document") 
                or meta.get("title") 
                or meta.get("source") 
                or f"ReCover Insurance Guide {idx+1}"
            )
            
            ref_info = meta.get("reference") or meta.get("section") or f"Section {idx+1}"
            doc_url = meta.get("url") or meta.get("link") or None

            sources.append(
                Source(
                    tag=tag,
                    document=str(doc_title),
                    page=int(meta.get("page", 1)),
                    reference=str(ref_info),
                    url=doc_url
                )
            )

        # If Chroma returned no documents, provide at least one general reference
        if not sources:
            sources.append(
                Source(
                    tag="[S1]",
                    document="ReCover Microinsurance Knowledge Base",
                    page=1,
                    reference="General Guidelines",
                    url=None
                )
            )
        context_str = "\n\n".join(context_blocks)

        system_instruction = (
            "You are ReCover, an empathetic microinsurance advisor for Kenyan informal market traders.\n\n"
            "CRITICAL LANGUAGE RULE:\n"
            "- Mirror the user's language EXACTLY:\n"
            "  * If the user asks in English, answer strictly and completely in English.\n"
            "  * If the user asks in Kiswahili, answer in Kiswahili.\n"
            "  * If the user asks in Sheng or mixed Sheng/English/Swahili, code-switch naturally.\n"
            "- Do not default to Kiswahili if the user writes in English, even if the reference documents contain Kiswahili.\n\n"
            "STYLE & GROUNDING:\n"
            "- Explain microinsurance policies clearly, simply, and without heavy financial jargon.\n"
            "- Never produce blank bullet points, empty dashes, or orphaned numbers (e.g., do not output '- \\n- ' or '2. \\n3. ').\n"
            "- Always bold the title of each item (e.g., '- **Hospital Cash Cover:** ...').\n"
            "- Do not use horizontal divider lines ('---') or markdown headers ('###').\n"
            "- Keep responses conversational, concise, and structured with short bullet points.\n"
            "- Ground your answer in the provided context and cite references using [S1], [S2] tags where appropriate."
        )

        prompt = f"Context:\n{context_str}\n\nUser Question: {user_query}"

        # Generate response using gemini-2.5-flash (fastest latency and lowest RAM)
        response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config={"system_instruction": system_instruction}
        )

        answer_text = response.text or "Samahani, I could not generate a response at this moment."

        # Force Python garbage collection after each request to release memory
        gc.collect()

        return ChatResponse(answer=answer_text, sources=sources)

    except Exception as e:
        # Force cleanup even on error
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset/{session_id}")
async def reset_session(session_id: str):
    # Session reset endpoint to satisfy handleResetConversation in chat/page.tsx
    gc.collect()
    return {"status": "reset", "session_id": session_id}


@app.get("/health")
@app.get("/")
async def health_check():
    return {"status": "ok", "service": "ReCover Advisor API"}