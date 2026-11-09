
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ------------------------------------------------------------
# FASTAPI
# ------------------------------------------------------------

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ------------------------------------------------------------
# IMPORT ORCHESTRATION
# ------------------------------------------------------------

from orchestration.agent import (
    handle_message,
    reset_information_session
)


# ------------------------------------------------------------
# IMPORT WHATSAPP ROUTER
# ------------------------------------------------------------

from information_system_api.whatsapp import (
    router as whatsapp_router
)


# ------------------------------------------------------------
# INITIALIZE APPLICATION
# ------------------------------------------------------------

app = FastAPI(
    title="ReCover Microinsurance Advisor API",
    description=(
        "Unified microinsurance information and "
        "recommendation system for Kenyan traders."
    ),
    version="2.0.0"
)


# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ------------------------------------------------------------
# REGISTER WHATSAPP ROUTER
# ------------------------------------------------------------

app.include_router(whatsapp_router)


# ------------------------------------------------------------
# REQUEST SCHEMA
# ------------------------------------------------------------

class ChatRequest(BaseModel):

    message: str = Field(min_length=1)

    session_id: str = Field(min_length=1)

    intent: Optional[str] = None

    trader_data: Optional[Dict[str, Any]] = None


# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------

@app.get("/")
async def home():

    return {
        "project": "ReCover",
        "service": "Unified Advisor API",
        "status": "running",
        "architecture": "orchestration"
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "ReCover",
        "information_system": "connected",
        "recommendation_system": "connected",
        "orchestration": "active"
    }


# ------------------------------------------------------------
# UNIFIED CHAT ENDPOINT
# ------------------------------------------------------------

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):

    user_query = payload.message.strip()

    if not user_query:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:

        # All requests now go through orchestration.

        result = handle_message(
            message=user_query,
            session_id=payload.session_id,
            trader_data=payload.trader_data,
            intent=payload.intent
        )

        if not isinstance(result, dict):

            raise ValueError(
                "Invalid response from orchestration."
            )

        answer = (
            result.get("answer")
            or result.get("reply")
            or result.get("response")
            or result.get("text")
            or ""
        )

        # Preserve all orchestration metadata.
        return {
            **result,
            "answer": answer,
            "reply": answer,
            "sources": result.get("sources", []),
            "session_id": payload.session_id
        }

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"Orchestration error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request."
        )


# ------------------------------------------------------------
# CHAT ENDPOINT ALIAS
# ------------------------------------------------------------

@app.post("/chat")
async def chat_alias(payload: ChatRequest):

    return await chat_endpoint(payload)


# ------------------------------------------------------------
# RESET CONVERSATION
# ------------------------------------------------------------

@app.post("/reset/{session_id}")
async def reset_session(session_id: str):

    try:

        result = reset_information_session(
            session_id
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ------------------------------------------------------------
# SERVE INSURANCE DOCUMENTS
# ------------------------------------------------------------

from information_system_api.config import DOCS_DIR
from fastapi.staticfiles import StaticFiles

if Path(DOCS_DIR).exists():

    app.mount(
        "/documents",
        StaticFiles(directory=str(DOCS_DIR)),
        name="documents"
    )


print("ReCover unified server initialized.")
print("Orchestration connected.")
print("Information system connected.")
print("Recommendation system connected.")
print("WhatsApp router registered.")
