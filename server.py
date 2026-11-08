import torch
from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.orchestration.agent import handle_message

app = FastAPI(title="ReCover Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_trader_session"  # Must stay consistent per conversation

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    # Pass the exact persistent session_id into the orchestrator
    response = handle_message(
        message=req.message,
        session_id=req.session_id
    )
    
    if isinstance(response, dict):
        text = (
            response.get("answer")
            or response.get("reply")
            or response.get("response")
            or response.get("text")
            or str(response)
        )
        return {
            "reply": text,
            "answer": text,  # <--- Add this line!
            "sources": response.get("sources", []),
            "session_id": req.session_id
        }
    
    return {"reply": str(response), "answer": str(response), "session_id": req.session_id}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)