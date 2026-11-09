import torch
from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path

# Add src directory to Python path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import the actual unified orchestration FastAPI app
from orchestration.main import app