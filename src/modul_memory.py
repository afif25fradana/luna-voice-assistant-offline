"""
This module handles the short-term and long-term memory for the assistant.
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# Use absolute imports for better testability
try:
    from .config import Config
except ImportError:
    # Fallback for when running tests
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import Config

class ChatMemory:
    """
    Manages chat history in memory with a maximum size limit.
    """
    def __init__(self, memory_file: str, max_memory_size: int):
        self.memory_file = memory_file
        self.max_memory_size = max_memory_size
        self.history: List[Dict[str, str]] = []
        self._load_memory()

    def _load_memory(self) -> None:
        """Load chat history from file."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as file:
                self.history = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = []

    def _save_memory(self) -> None:
        """Save chat history to file."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as file:
                json.dump(self.history, file, indent=4, ensure_ascii=False)
        except IOError as e:
            logging.error("[Memory] Error saving chat memory: %s", e)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to chat history."""
        self.history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        # Keep only the most recent messages
        if len(self.history) > self.max_memory_size:
            self.history = self.history[-self.max_memory_size:]
        self._save_memory()

    def get_history(self) -> List[Dict[str, str]]:
        """Get chat history."""
        return self.history.copy()

    def clear_memory(self) -> None:
        """Clear all chat history."""
        self.history.clear()
        self._save_memory()

def save_conversation_turn(user_message: str, assistant_message: str) -> None:
    """
    Saves a user-assistant conversation turn to the long-term memory file in JSON format.
    """
    turn: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "assistant": assistant_message
    }

    try:
        # Read existing history
        try:
            with open(Config.LONG_TERM_MEMORY_FILE, "r", encoding="utf-8") as file:
                history: List[Dict[str, Any]] = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        # Append new turn and write back
        history.append(turn)
        with open(Config.LONG_TERM_MEMORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)

    except IOError as e:
        logging.error("[Memory] Error saving to long-term memory: %s", e)

def load_long_term_memory() -> List[Dict[str, Any]]:
    """
    Loads the conversation history from the long-term memory file.
    """
    try:
        with open(Config.LONG_TERM_MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []