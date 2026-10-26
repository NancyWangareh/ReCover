
import sys
from pathlib import Path

PROJECT_DIR = Path("/content/drive/MyDrive/ReCover")
SRC_DIR = PROJECT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from rag_pipeline import ask_recover


if __name__ == "__main__":
    question = input("Ask ReCover: ")

    answer = ask_recover(question)

    print("\nReCover:")
    print(answer)
