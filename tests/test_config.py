"""
Unit tests for the config module.
"""
import unittest
import os
import sys
from pathlib import Path

# Add src to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config

class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""

    def test_config_paths_exist(self):
        """Test that all configured paths are properly set."""
        self.assertIsInstance(Config.BASE_DIR, Path)
        self.assertIsInstance(Config.TEMP_DIR, Path)
        self.assertIsInstance(Config.LOGS_DIR, Path)
        self.assertIsInstance(Config.LOG_FILE, Path)
        self.assertIsInstance(Config.MEMORY_FILE, Path)
        self.assertIsInstance(Config.LONG_TERM_MEMORY_FILE, Path)

    def test_config_paths_are_absolute(self):
        """Test that all paths are absolute."""
        self.assertTrue(Config.BASE_DIR.is_absolute())
        self.assertTrue(Config.TEMP_DIR.is_absolute())
        self.assertTrue(Config.LOGS_DIR.is_absolute())
        self.assertTrue(Config.LOG_FILE.is_absolute())
        self.assertTrue(Config.MEMORY_FILE.is_absolute())
        self.assertTrue(Config.LONG_TERM_MEMORY_FILE.is_absolute())

    def test_config_setup_directories(self):
        """Test that setup_directories creates required directories."""
        # Store original state
        temp_exists = Config.TEMP_DIR.exists()
        logs_exists = Config.LOGS_DIR.exists()
        
        # Run setup
        Config.setup_directories()
        
        # Check that directories exist
        self.assertTrue(Config.TEMP_DIR.exists())
        self.assertTrue(Config.LOGS_DIR.exists())
        
        # Cleanup if they didn't exist before
        if not temp_exists:
            Config.TEMP_DIR.rmdir()
        if not logs_exists:
            Config.LOGS_DIR.rmdir()

    def test_config_values(self):
        """Test that configuration values are properly set."""
        self.assertEqual(Config.MODEL_NAME, "gemma3:4b-it-q4_K_M")
        self.assertEqual(Config.STT_MODEL_SIZE, "medium")
        self.assertEqual(Config.STT_SAMPLE_RATE, 16000)
        self.assertEqual(Config.INTERPRETER_AUTO_RUN, True)
        self.assertIsInstance(Config.SECURITY_COMMAND_BLACKLIST, list)
        self.assertIsInstance(Config.GUI_COLORS, dict)

if __name__ == '__main__':
    unittest.main()