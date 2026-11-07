from typing import List, Dict, Any
from .config import MAX_MEMORY_TURNS

class ConversationManager:
    def __init__(self, max_turns: int = MAX_MEMORY_TURNS):
        self.max_turns = max_turns
        self.history: List[Dict[str, Any]] = []

    def add_user_message(self, message: str) -> None:
        self.history.append({"role": "user", "text": message})
        self._trim()

    def add_assistant_response(self, text: str, sources: List[str]) -> None:
        self.history.append({"role": "assistant", "text": text, "sources": sources})
        self._trim()

    def _trim(self) -> None:
        max_messages = self.max_turns * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self.history)

    def get_formatted_turns(self) -> str:
        if not self.history:
            return "No previous conversation context."
        lines = []
        for msg in self.history:
            role = "Trader" if msg["role"] == "user" else "ReCover Educator"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)

    def clear(self) -> None:
        self.history.clear()