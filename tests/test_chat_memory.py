"""
Unit tests for the ChatMemory class.
"""
import unittest
import sys
import os
import tempfile
from pathlib import Path

# Add src to path so we can import modul_memory
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the ChatMemory class directly to avoid relative import issues
import modul_memory

class TestChatMemory(unittest.TestCase):
    """Test cases for the ChatMemory class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
            
    def test_chat_memory_initialization(self):
        """Test that ChatMemory initializes correctly."""
        chat_memory = modul_memory.ChatMemory(self.temp_file.name, 10)
        self.assertEqual(chat_memory.memory_file, self.temp_file.name)
        self.assertEqual(chat_memory.max_memory_size, 10)
        self.assertIsInstance(chat_memory.history, list)
        
    def test_add_message(self):
        """Test that messages can be added to chat memory."""
        chat_memory = modul_memory.ChatMemory(self.temp_file.name, 10)
        chat_memory.add_message("user", "Hello")
        chat_memory.add_message("assistant", "Hi there!")
        
        history = chat_memory.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Hello")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Hi there!")
        
    def test_get_history(self):
        """Test that chat history can be retrieved."""
        chat_memory = modul_memory.ChatMemory(self.temp_file.name, 10)
        chat_memory.add_message("user", "Hello")
        
        history = chat_memory.get_history()
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 1)
        
        # Test that returned history is a copy
        history.append({"role": "test", "content": "test"})
        self.assertEqual(len(chat_memory.get_history()), 1)  # Original should be unchanged
        
    def test_memory_limit(self):
        """Test that memory size is limited."""
        chat_memory = modul_memory.ChatMemory(self.temp_file.name, 3)
        
        # Add more messages than the limit
        for i in range(5):
            chat_memory.add_message("user", f"Message {i}")
            
        history = chat_memory.get_history()
        self.assertEqual(len(history), 3)  # Should only keep the last 3
        
        # Check that these are the last 3 messages
        self.assertEqual(history[0]["content"], "Message 2")
        self.assertEqual(history[1]["content"], "Message 3")
        self.assertEqual(history[2]["content"], "Message 4")
        
    def test_clear_memory(self):
        """Test that chat memory can be cleared."""
        chat_memory = modul_memory.ChatMemory(self.temp_file.name, 10)
        chat_memory.add_message("user", "Hello")
        chat_memory.add_message("assistant", "Hi there!")
        
        self.assertEqual(len(chat_memory.get_history()), 2)
        
        chat_memory.clear_memory()
        self.assertEqual(len(chat_memory.get_history()), 0)

if __name__ == '__main__':
    unittest.main()