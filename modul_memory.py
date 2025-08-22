"""
This module manages the chat memory for the Luna Voice Assistant.
It stores chat history in a JSON file and provides methods to add, retrieve, and clear messages.
"""
import json
import os
import logging
from datetime import datetime

class ChatMemory:
    """
    Manages the storage and retrieval of chat messages.
    """
    def __init__(self, memory_file="memory.json", max_memory_size=10):
        self.memory_file = memory_file
        self.max_memory_size = max_memory_size
        self.memory = self._load_memory()

    def _load_memory(self):
        """Loads chat history from the memory file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                logging.warning("Could not decode JSON from %s. Starting with empty memory.", self.memory_file)
                return []
            except IOError as err:
                logging.error("Error loading memory file %s: %s", self.memory_file, err)
                return []
        return []

    def _save_memory(self):
        """Saves the current chat history to the memory file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as file:
                json.dump(self.memory, file, indent=4)
        except IOError as err:
            logging.error("Error saving memory file %s: %s", self.memory_file, err)

    def add_message(self, role, content):
        """Adds a new message to the chat history."""
        timestamp = datetime.now().isoformat()
        self.memory.append({"role": role, "content": content, "timestamp": timestamp})
        # Keep only the most recent messages up to max_memory_size
        if len(self.memory) > self.max_memory_size:
            self.memory = self.memory[-self.max_memory_size:]
        self._save_memory()

    def get_history(self):
        """Retrieves the current chat history."""
        return self.memory

    def clear_memory(self):
        """Clears all messages from the chat history."""
        self.memory = []
        self._save_memory()
