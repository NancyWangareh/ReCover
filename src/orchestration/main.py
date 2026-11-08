from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from information_system_api.config import DOCS_DIR

from orchestration.agent import (
    handle_message,
    reset_information_session
)

from information_system_api.whatsapp import router as whatsapp_router

app = FastAPI(
    title="ReCover Orchestration API",
    description=(
        "Unified microinsurance information and "
        "recommendation system for Kenyan mitumba traders."
    ),
    version="1.0.0"
)


app.include_router(whatsapp_router)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    intent: Optional[str] = None
    trader_data: Optional[Dict[str, Any]] = None


@app.get("/")
def home():
    return {
        "project": "ReCover",
        "service": "Orchestration API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ReCover Orchestration API"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    try:
        result = handle_message(
            message=request.message,
            session_id=request.session_id,
            trader_data=request.trader_data,
            intent=request.intent
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )




@app.post("/api/chat")
def frontend_chat(request: ChatRequest):

    try:
        result = handle_message(
            message=request.message,
            session_id=request.session_id,
            trader_data=request.trader_data,
            intent=request.intent
        )

        if isinstance(result, dict):
            text = (
                result.get("answer")
                or result.get("reply")
                or result.get("response")
                or result.get("text")
                or str(result)
            )

            return {
                "reply": text,
                "answer": text,
                "sources": result.get("sources", []),
                "session_id": request.session_id
            }

        return {
            "reply": str(result),
            "answer": str(result),
            "sources": [],
            "session_id": request.session_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/reset/{session_id}")
def reset_session(session_id: str):

    return reset_information_session(session_id)


# Allow requests from the ReCover frontend.
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

# Serve original PDF documents for clickable citations.
app.mount(
    "/documents",
    StaticFiles(directory=str(DOCS_DIR)),
    name="documents"
)
