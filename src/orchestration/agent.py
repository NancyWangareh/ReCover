
import sys
import threading
from pathlib import Path

# Add src to Python's import path
SRC_DIR = Path(__file__).resolve().parent.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from information_system_api.chatbot import ReCoverChatbot
from information_system_api.memory import ConversationManager

from orchestration.intent_detector import detect_intent

from orchestration.recommendation_generator import (
    generate_recommendation_response
)

from orchestration.recommendation_processor import (
    process_recommendations
)

from orchestration.recommendation_intake import (
    start_intake,
    process_intake_message,
    get_intake_status,
    reset_intake
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


def _generate_recommendations(trader_data, session_id=None):
    """
    Pass collected trader information to the recommendation engine
    and generate a conversational response.
    """

    try:
        result = process_recommendations(trader_data)

        conversational_answer = generate_recommendation_response(
            result
        )

        return {
            "success": True,
            "intent": "recommendation",
            "session_id": session_id,
            "requires_trader_information": False,
            "trader_data": trader_data,
            "answer": conversational_answer,
            "result": result,
            "sources": []
        }

    except Exception as e:
        print(f"Recommendation generation error: {e}")

        return {
            "success": False,
            "intent": "recommendation",
            "session_id": session_id,
            "requires_trader_information": False,
            "trader_data": trader_data,
            "answer": (
                "Your business information has been collected, "
                "but I encountered a problem generating your "
                "recommendations. Please try again shortly."
            ),
            "error": str(e),
            "sources": []
        }


def handle_message(
    message,
    session_id=None,
    trader_data=None,
    intent=None
):
    """
    Route messages to the appropriate ReCover system.

    Active recommendation questionnaires take priority over
    intent detection so that individual answers are not
    mistakenly routed to the information system.
    """

    if not message or not message.strip():
        return {
            "success": False,
            "intent": None,
            "answer": "Please enter a message.",
            "sources": []
        }

    if not session_id:
        return {
            "success": False,
            "intent": None,
            "answer": "A session ID is required to continue.",
            "sources": []
        }

    # -------------------------------------------------
    # 1. CHECK WHETHER A RECOMMENDATION INTAKE IS ACTIVE
    # -------------------------------------------------

    intake_status = get_intake_status(session_id)

    if intake_status and not intake_status["completed"]:

        intake_result = process_intake_message(
            session_id,
            message
        )

        # More information is required
        if intake_result["status"] in ("collecting", "invalid"):

            return {
                "success": intake_result["success"],
                "intent": "recommendation",
                "session_id": session_id,
                "requires_trader_information": True,
                "intake_status": intake_result["status"],
                "answer": intake_result["answer"],
                "collected_fields": intake_result.get(
                    "collected_fields", []
                ),
                "sources": []
            }

        # All 11 fields have been collected
        if intake_result["status"] == "completed":

            collected_data = intake_result["trader_data"]

            recommendation_result = _generate_recommendations(
                collected_data,
                session_id
            )

            return recommendation_result

    # -------------------------------------------------
    # 2. DETECT MESSAGE INTENT
    # -------------------------------------------------

    selected_intent = intent or detect_intent(message)

    # -------------------------------------------------
    # 3. INFORMATION SYSTEM
    # -------------------------------------------------

    if selected_intent in (
        "information",
        "general_conversation"
    ):

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

    # -------------------------------------------------
    # 4. RECOMMENDATION SYSTEM
    # -------------------------------------------------

    if selected_intent == "recommendation":

        # If trader information was supplied directly,
        # skip the conversational questionnaire.
        if trader_data is not None:

            return _generate_recommendations(
                trader_data,
                session_id
            )

        # Otherwise, start the conversational intake.
        intake_result = start_intake(session_id)

        return {
            "success": True,
            "intent": "recommendation",
            "session_id": session_id,
            "requires_trader_information": True,
            "intake_status": "collecting",
            "answer": intake_result["answer"],
            "sources": []
        }

    # -------------------------------------------------
    # 5. FALLBACK
    # -------------------------------------------------

    return {
        "success": False,
        "intent": selected_intent,
        "session_id": session_id,
        "answer": (
            "I could not identify how to handle your request."
        ),
        "sources": []
    }


def reset_information_session(session_id):
    """
    Clear the specified trader's information memory
    and recommendation questionnaire.
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

    reset_intake(session_id)

    return {
        "success": True,
        "session_id": session_id,
        "message": (
            "Conversation memory and recommendation "
            "intake reset successfully."
        )
    }
