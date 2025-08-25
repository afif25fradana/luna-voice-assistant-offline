"""
Unit tests for the config_validator module.
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path so we can import config_validator
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_validator import validate_config, validate_model_files

class TestConfigValidator(unittest.TestCase):
    """Test cases for the config_validator module."""

    @patch('config_validator.Config')
    def test_validate_config_with_valid_config(self, mock_config):
        """Test that valid configuration passes validation."""
        # Mock a valid configuration
        mock_config.TEMP_DIR = Path("/tmp")
        mock_config.LOGS_DIR = Path("/var/log")
        mock_config.LOG_FILE = Path("/var/log/app.log")
        mock_config.MEMORY_FILE = Path("/var/lib/memory.json")
        mock_config.LONG_TERM_MEMORY_FILE = Path("/var/lib/long_term_memory.json")
        mock_config.TTS_MODEL_PATH = "/models/tts/model.onnx"
        mock_config.STT_SAMPLE_RATE = 16000
        mock_config.CONTEXT_WINDOW = 4096
        mock_config.MAX_MEMORY_SIZE = 10
        mock_config.MODEL_NAME = "test-model"
        mock_config.STT_MODEL_SIZE = "medium"
        mock_config.STT_COMPUTE_TYPE = "int8"
        mock_config.OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
        mock_config.OLLAMA_HEALTH_CHECK = "http://localhost:11434/api/tags"
        mock_config.GUI_COLORS = {
            'background': '#000000', 'input_bg': '#111111', 'user_msg': '#222222',
            'assistant_msg': '#333333', 'text_primary': '#FFFFFF', 'text_secondary': '#CCCCCC',
            'accent': '#444444', 'accent_hover': '#555555', 'listening': '#666666',
            'thinking': '#777777', 'error': '#888888'
        }
        mock_config.SECURITY_COMMAND_BLACKLIST = ["rm -rf"]
        mock_config.INTERPRETER_AUTO_RUN = True
        
        issues = validate_config()
        self.assertEqual(len(issues), 0)

    @patch('config_validator.Config')
    def test_validate_config_with_invalid_paths(self, mock_config):
        """Test that invalid paths are caught by validation."""
        # Mock an invalid configuration with non-Path objects
        mock_config.TEMP_DIR = "/tmp"  # String instead of Path
        mock_config.LOGS_DIR = Path("/var/log")
        mock_config.LOG_FILE = Path("/var/log/app.log")
        mock_config.MEMORY_FILE = Path("/var/lib/memory.json")
        mock_config.LONG_TERM_MEMORY_FILE = Path("/var/lib/long_term_memory.json")
        mock_config.TTS_MODEL_PATH = "/models/tts/model.onnx"
        mock_config.STT_SAMPLE_RATE = 16000
        mock_config.CONTEXT_WINDOW = 4096
        mock_config.MAX_MEMORY_SIZE = 10
        mock_config.MODEL_NAME = "test-model"
        mock_config.STT_MODEL_SIZE = "medium"
        mock_config.STT_COMPUTE_TYPE = "int8"
        mock_config.OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
        mock_config.OLLAMA_HEALTH_CHECK = "http://localhost:11434/api/tags"
        mock_config.GUI_COLORS = {
            'background': '#000000', 'input_bg': '#111111', 'user_msg': '#222222',
            'assistant_msg': '#333333', 'text_primary': '#FFFFFF', 'text_secondary': '#CCCCCC',
            'accent': '#444444', 'accent_hover': '#555555', 'listening': '#666666',
            'thinking': '#777777', 'error': '#888888'
        }
        mock_config.SECURITY_COMMAND_BLACKLIST = ["rm -rf"]
        mock_config.INTERPRETER_AUTO_RUN = True
        
        issues = validate_config()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0][0], "CONFIG")
        self.assertIn("TEMP_DIR is not a Path object", issues[0][1])

    @patch('config_validator.Config')
    def test_validate_config_with_invalid_urls(self, mock_config):
        """Test that invalid URLs are caught by validation."""
        # Mock an invalid configuration with non-URL strings
        mock_config.TEMP_DIR = Path("/tmp")
        mock_config.LOGS_DIR = Path("/var/log")
        mock_config.LOG_FILE = Path("/var/log/app.log")
        mock_config.MEMORY_FILE = Path("/var/lib/memory.json")
        mock_config.LONG_TERM_MEMORY_FILE = Path("/var/lib/long_term_memory.json")
        mock_config.TTS_MODEL_PATH = "/models/tts/model.onnx"
        mock_config.STT_SAMPLE_RATE = 16000
        mock_config.CONTEXT_WINDOW = 4096
        mock_config.MAX_MEMORY_SIZE = 10
        mock_config.MODEL_NAME = "test-model"
        mock_config.STT_MODEL_SIZE = "medium"
        mock_config.STT_COMPUTE_TYPE = "int8"
        mock_config.OLLAMA_ENDPOINT = "not-a-url"  # Invalid URL
        mock_config.OLLAMA_HEALTH_CHECK = "http://localhost:11434/api/tags"
        mock_config.GUI_COLORS = {
            'background': '#000000', 'input_bg': '#111111', 'user_msg': '#222222',
            'assistant_msg': '#333333', 'text_primary': '#FFFFFF', 'text_secondary': '#CCCCCC',
            'accent': '#444444', 'accent_hover': '#555555', 'listening': '#666666',
            'thinking': '#777777', 'error': '#888888'
        }
        mock_config.SECURITY_COMMAND_BLACKLIST = ["rm -rf"]
        mock_config.INTERPRETER_AUTO_RUN = True
        
        issues = validate_config()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0][0], "CONFIG")
        self.assertIn("OLLAMA_ENDPOINT is not a valid URL", issues[0][1])

if __name__ == '__main__':
    unittest.main()