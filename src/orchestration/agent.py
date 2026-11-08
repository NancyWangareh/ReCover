import sys
import threading
from pathlib import Path

# Add src to Python's import path
SRC_DIR = Path(__file__).resolve().parent.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from information_system_api.chatbot import ReCoverChatbot
from information_system_api.memory import ConversationManager

from orchestration.recommendation_processor import (
    process_recommendations
)


# One shared chatbot and knowledge base
_chatbot = None

# Separate conversation memory for each session
_sessions = {}

# Protect shared resources
_initialization_lock = threading.Lock()
_sessions_lock = threading.Lock()


def get_chatbot():
    global _chatbot

    if _chatbot is None:
        with _initialization_lock:
            if _chatbot is None:
                print("Initializing ReCover information system...")
                _chatbot = ReCoverChatbot()
                print("Knowledge base initialized successfully.")

    return _chatbot


def get_session_memory(session_id):
    if not session_id:
        raise ValueError("A session ID is required.")

    with _sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = ConversationManager()

        return _sessions[session_id]


def detect_intent(message):
    """
    Basic intent detection for the first orchestration version.
    """

    text = message.lower()

    recommendation_keywords = [
        "recommend a product",
        "recommend products",
        "recommendation",
        "recommend insurance",
        "suggest a product",
        "which insurance should i choose",
        "which product should i choose",
        "suitable insurance",
        "suitable product",
        "get recommendations",
        "what insurance is suitable",
        "find insurance for my business",
        "i need insurance for my stock"
    ]

    if any(keyword in text for keyword in recommendation_keywords):
        return "recommendation"

    return "information"


def handle_message(
    message,
    session_id=None,
    trader_data=None,
    intent=None
):
    """
    Route messages to the appropriate ReCover system.
    """

    if not message or not message.strip():
        return {
            "success": False,
            "intent": None,
            "answer": "Please enter a message.",
            "sources": []
        }

    selected_intent = intent or detect_intent(message)

    # INFORMATION SYSTEM
    if selected_intent == "information":

        if not session_id:
            return {
                "success": False,
                "intent": "information",
                "answer": "A session ID is required to continue your conversation.",
                "sources": []
            }

        chatbot = get_chatbot()
        memory = get_session_memory(session_id)

        result = chatbot.ask(
            message,
            memory=memory
        )

        return {
            "success": True,
            "intent": "information",
            "session_id": session_id,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "interpretation": result.get("interpretation", {})
        }

    # RECOMMENDATION SYSTEM
    if selected_intent == "recommendation":

        if not trader_data:
            return {
                "success": True,
                "intent": "recommendation",
                "requires_trader_information": True,
                "answer": (
                    "I can help identify suitable microinsurance "
                    "products for your business. First, I need "
                    "some information about your business and income."
                ),
                "required_fields": [
                    "stock_value_kes",
                    "total_loss_24m_kes",
                    "monthly_income_kes",
                    "wtp_monthly_kes",
                    "restock_cycle_days",
                    "primary_risk_concern",
                    "wants_cover_fire",
                    "wants_cover_theft",
                    "income_variability",
                    "preferred_premium_frequency",
                    "income_receipt_pattern"
                ],
                "sources": []
            }

        result = process_recommendations(trader_data)

        return {
            "success": True,
            "intent": "recommendation",
            "requires_trader_information": False,
            "answer": (
                "Your ReCover product recommendations "
                "have been generated."
            ),
            "result": result,
            "sources": []
        }

    return {
        "success": False,
        "intent": selected_intent,
        "answer": "I could not identify how to handle your request.",
        "sources": []
    }


def reset_information_session(session_id):
    """
    Clear only the specified trader's conversation memory.
    """

    if not session_id:
        return {
            "success": False,
            "message": "A session ID is required."
        }

    with _sessions_lock:
        memory = _sessions.pop(session_id, None)

    if memory is not None:
        memory.clear()

    return {
        "success": True,
        "session_id": session_id,
        "message": "Information session reset successfully."
    }
