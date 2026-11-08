import re
import threading


# --------------------------------------------------
# RECOMMENDATION INTAKE CONFIGURATION
# --------------------------------------------------

QUESTIONS = [
    {
        "field": "stock_value_kes",
        "question": (
            "Approximately how much is your current business "
            "stock worth in KES?"
        ),
        "type": "number",
        "minimum": 1
    },
    {
        "field": "total_loss_24m_kes",
        "question": (
            "Approximately how much have you lost through "
            "business-related incidents in the last two years? "
            "You can enter 0 if you have experienced no losses."
        ),
        "type": "number",
        "minimum": 0
    },
    {
        "field": "monthly_income_kes",
        "question": (
            "What is your average monthly business income in KES?"
        ),
        "type": "number",
        "minimum": 1
    },
    {
        "field": "wtp_monthly_kes",
        "question": (
            "How much could you comfortably afford to spend "
            "on insurance per month in KES?"
        ),
        "type": "number",
        "minimum": 0
    },
    {
        "field": "restock_cycle_days",
        "question": (
            "How often do you restock your business? "
            "Please indicate the number of days. "
            "For example, 7 for weekly."
        ),
        "type": "number",
        "minimum": 1
    },
    {
        "field": "primary_risk_concern",
        "question": (
            "What is your biggest business risk?\n"
            "1. Fire\n"
            "2. Theft\n"
            "3. Health-related risks\n"
            "4. Accidents\n"
            "5. Enforcement or confiscation\n"
            "6. Weather or flooding\n\n"
            "You can also type your answer."
        ),
        "type": "risk"
    },
    {
        "field": "wants_cover_fire",
        "question": (
            "Would you like insurance protection against fire? "
            "Please answer Yes or No."
        ),
        "type": "boolean"
    },
    {
        "field": "wants_cover_theft",
        "question": (
            "Would you like insurance protection against theft? "
            "Please answer Yes or No."
        ),
        "type": "boolean"
    },
    {
        "field": "income_variability",
        "question": (
            "How predictable is your business income?\n"
            "1. Low variability - relatively stable\n"
            "2. Medium variability - changes sometimes\n"
            "3. High variability - changes significantly"
        ),
        "type": "variability"
    },
    {
        "field": "preferred_premium_frequency",
        "question": (
            "How frequently would you prefer to pay your "
            "insurance premium?\n"
            "1. Daily\n"
            "2. Weekly\n"
            "3. Monthly\n"
            "4. When restocking"
        ),
        "type": "frequency"
    },
    {
        "field": "income_receipt_pattern",
        "question": (
            "How frequently do you normally receive income "
            "from your business?\n"
            "1. Daily\n"
            "2. Weekly\n"
            "3. Monthly\n"
            "4. Irregularly"
        ),
        "type": "income_pattern"
    }
]


# --------------------------------------------------
# SESSION STORAGE
# --------------------------------------------------

_intake_sessions = {}
_intake_lock = threading.Lock()


# --------------------------------------------------
# RESPONSE PARSING
# --------------------------------------------------

def parse_number(message):

    value = message.lower().strip()

    value = value.replace(",", "")
    value = value.replace("kes", "")
    value = value.replace("ksh", "")
    value = value.replace("kshs", "")
    value = value.replace("ksh.", "")
    value = value.strip()

    # Support values such as 150k or 1.5k
    multiplier = 1

    if value.endswith("k"):
        multiplier = 1000
        value = value[:-1].strip()

    elif value.endswith("m"):
        multiplier = 1000000
        value = value[:-1].strip()

    # Extract numeric value
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", value)

    if not match:
        return None

    number = float(match.group(1)) * multiplier

    if number < 0:
        return None

    return int(number) if number.is_integer() else number


def normalize_message(message):

    return message.strip().lower()


def parse_boolean(message):

    value = normalize_message(message)

    yes_values = [
        "yes", "y", "yeah", "yep",
        "ndio", "ndio kabisa", "naam"
    ]

    no_values = [
        "no", "n", "nope",
        "hapana", "la", "sihitaji"
    ]

    if value in yes_values:
        return True

    if value in no_values:
        return False

    return None


def parse_category(message, category):

    value = normalize_message(message)

    options = {

        "risk": {
            "1": "fire",
            "fire": "fire",
            "moto": "fire",

            "2": "theft",
            "theft": "theft",
            "stealing": "theft",
            "wizi": "theft",

            "3": "health",
            "health": "health",
            "illness": "health",
            "ugonjwa": "health",

            "4": "accident",
            "accident": "accident",
            "ajali": "accident",

            "5": "enforcement",
            "enforcement": "enforcement",
            "confiscation": "enforcement",
            "eviction": "enforcement",

            "6": "weather_flood",
            "weather": "weather_flood",
            "flood": "weather_flood",
            "flooding": "weather_flood"
        },

        "variability": {
            "1": "low",
            "low": "low",
            "stable": "low",

            "2": "medium",
            "medium": "medium",
            "moderate": "medium",

            "3": "high",
            "high": "high",
            "unpredictable": "high"
        },

        "frequency": {
            "1": "daily",
            "daily": "daily",
            "kila siku": "daily",

            "2": "weekly",
            "weekly": "weekly",
            "kila wiki": "weekly",

            "3": "monthly",
            "monthly": "monthly",
            "kila mwezi": "monthly",

            "4": "pay_at_restock",
            "restock": "pay_at_restock",
            "when restocking": "pay_at_restock",
            "when i restock": "pay_at_restock"
        },

        "income_pattern": {
            "1": "daily",
            "daily": "daily",

            "2": "weekly",
            "weekly": "weekly",

            "3": "monthly",
            "monthly": "monthly",

            "4": "irregular",
            "irregular": "irregular",
            "varies": "irregular",
            "not fixed": "irregular"
        }
    }

    return options.get(category, {}).get(value)


# --------------------------------------------------
# FIELD VALIDATION
# --------------------------------------------------

def validate_answer(question, message):

    field_type = question["type"]

    if field_type == "number":

        value = parse_number(message)

        if value is None:
            return None, (
                "Please enter a valid numerical amount or "
                "number of days."
            )

        if value < question["minimum"]:
            return None, (
                f"Please enter a value of at least "
                f"{question['minimum']}."
            )

        return value, None

    if field_type == "boolean":

        value = parse_boolean(message)

        if value is None:
            return None, (
                "Please answer Yes or No. "
                "You can also use Ndiyo or Hapana."
            )

        return value, None

    if field_type in [
        "risk",
        "variability",
        "frequency",
        "income_pattern"
    ]:

        value = parse_category(message, field_type)

        if value is None:
            return None, (
                "I couldn't identify that option. "
                "Please select one of the options provided."
            )

        return value, None

    return None, "Unsupported response type."


# --------------------------------------------------
# INTAKE MANAGEMENT
# --------------------------------------------------

def start_intake(session_id):

    if not session_id:
        raise ValueError("A session ID is required.")

    with _intake_lock:

        _intake_sessions[session_id] = {
            "data": {},
            "current_question": 0,
            "completed": False
        }

    return {
        "success": True,
        "status": "collecting",
        "session_id": session_id,
        "answer": (
            "I'd be happy to help you identify suitable "
            "microinsurance products for your business.\n\n"
            "I'll ask a few questions about your business "
            "to understand your needs.\n\n"
            + QUESTIONS[0]["question"]
        )
    }


def process_intake_message(session_id, message):

    if not session_id:
        raise ValueError("A session ID is required.")

    if not message or not message.strip():
        return {
            "success": False,
            "status": "invalid",
            "answer": "Please provide an answer."
        }

    with _intake_lock:

        session = _intake_sessions.get(session_id)

        if session is None:

            return {
                "success": False,
                "status": "not_started",
                "answer": (
                    "Let's first start your business "
                    "insurance assessment."
                )
            }

        if session["completed"]:

            return {
                "success": True,
                "status": "completed",
                "trader_data": session["data"],
                "answer": (
                    "Your business information has already "
                    "been collected."
                )
            }

        index = session["current_question"]
        question = QUESTIONS[index]

        value, error = validate_answer(question, message)

        if error:

            return {
                "success": False,
                "status": "invalid",
                "answer": error + "\n\n" + question["question"]
            }

        # Save validated response
        session["data"][question["field"]] = value

        # Move to next question
        session["current_question"] += 1

        # Check whether collection is complete
        if session["current_question"] >= len(QUESTIONS):

            session["completed"] = True

            trader_data = session["data"].copy()

            return {
                "success": True,
                "status": "completed",
                "session_id": session_id,
                "trader_data": trader_data,
                "answer": (
                    "Thank you! I have collected your "
                    "business information successfully.\n\n"
                    "I'm now preparing your insurance "
                    "recommendations."
                )
            }

        next_question = QUESTIONS[
            session["current_question"]
        ]

        return {
            "success": True,
            "status": "collecting",
            "session_id": session_id,
            "collected_fields": list(session["data"].keys()),
            "answer": (
                "Thank you for that information.\n\n"
                + next_question["question"]
            )
        }


def get_intake_status(session_id):

    with _intake_lock:

        session = _intake_sessions.get(session_id)

        if session is None:
            return None

        return {
            "completed": session["completed"],
            "current_question": session["current_question"],
            "total_questions": len(QUESTIONS),
            "collected_fields": list(session["data"].keys()),
            "data": session["data"].copy()
        }


def reset_intake(session_id):

    with _intake_lock:

        _intake_sessions.pop(session_id, None)

    return {
        "success": True,
        "message": "Recommendation intake reset successfully."
    }
