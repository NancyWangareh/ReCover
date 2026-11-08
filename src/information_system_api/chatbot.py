from typing import Dict, Any, List
from pathlib import Path
from .config import DOCS_DIR
from .primer import ensure_educational_primer
from .ocr import extract_pdf_pages, run_gemini_ocr_if_needed, split_ocr_pages
from .chunking import chunk_pages
from .indexer import VectorIndexer
from .memory import ConversationManager
from .interpreter import interpret_user_intent
from .retriever import retrieve_evidence
from .generator import generate_educational_answer
from .validator import validate_and_extract_citations

class ReCoverChatbot:
    def __init__(self):
        self.memory = ConversationManager()
        self.indexer = VectorIndexer()
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self) -> None:
        ensure_educational_primer()
        all_pages = []

        for file_path in DOCS_DIR.iterdir():
            if file_path.suffix.lower() == ".txt":
                content = file_path.read_text(encoding="utf-8")
                all_pages.extend(split_ocr_pages(file_path, file_path.name))
            elif file_path.suffix.lower() == ".pdf":
                resolved = run_gemini_ocr_if_needed(file_path)
                if resolved.suffix.lower() == ".txt":
                    all_pages.extend(split_ocr_pages(resolved, file_path.name))
                else:
                    all_pages.extend(extract_pdf_pages(file_path))

        chunks = chunk_pages(all_pages)
        self.indexer.build_index(chunks)

    def ask(
        self,
        user_message: str,
        memory: ConversationManager = None
    ) -> Dict[str, Any]:

        session_memory = memory if memory is not None else self.memory

        cleaned = user_message.strip()

        if not cleaned:
            return {
                "answer": "Please ask an insurance question to get started.",
                "sources": [],
                "interpretation": {},
                "evidence": []
            }

        history = session_memory.get_history()

        interpretation = interpret_user_intent(cleaned, history)

        evidence = retrieve_evidence(
            interpretation,
            self.indexer
        )

        answer = generate_educational_answer(
            cleaned,
            interpretation,
            evidence,
            history
        )

        sources = validate_and_extract_citations(
            answer,
            evidence
        )

        session_memory.add_user_message(cleaned)

        session_memory.add_assistant_response(
            answer,
            [s["reference"] for s in sources]
        )

        return {
            "answer": answer,
            "sources": sources,
            "interpretation": interpretation,
            "evidence": evidence
        }

    def reset(self, memory: ConversationManager = None) -> None:

        session_memory = memory if memory is not None else self.memory

        session_memory.clear()
