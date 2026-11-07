import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Navigate up 3 levels to reach the ReCover root:
# config.py -> information_system_api -> src -> ReCover/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Point directly to your existing document folder
DOCS_DIR = BASE_DIR / "data collection"

# Keep generated databases, OCR text, and caches organized in data/
DATA_DIR = BASE_DIR / "data"
OCR_DIR = DATA_DIR / "ocr_text"
DB_DIR = DATA_DIR / "chroma_db"

# Ensure the local output and cache directories exist
DOCS_DIR.mkdir(parents=True, exist_ok=True)
OCR_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# Model & Collection Configuration
GEMINI_MODEL = "gemini-3.8-flash"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "recover_educational_docs"

# Chunking & Retrieval Parameters
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 4
MAX_RESULTS = 5
MIN_SIMILARITY = 0.28
MAX_MEMORY_TURNS = 6


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            from google.colab import userdata

            key = userdata.get("GEMINI_API_KEY")
        except Exception:
            key = None

    if not key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Please export GEMINI_API_KEY in your terminal or .env file."
        )
    return key