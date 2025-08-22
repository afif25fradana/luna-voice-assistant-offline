"""
This module provides a centralized configuration for the Luna Voice Assistant.
It defines various settings, file paths, model parameters, and GUI colors.
"""
from pathlib import Path

class Config:
    """Centralized configuration for Luna Assistant"""

    # --- Core Paths ---
    BASE_DIR = Path(__file__).parent.resolve()
    TEMP_DIR = BASE_DIR / "temp"
    LOGS_DIR = BASE_DIR / "logs"
    LOG_FILE = LOGS_DIR / "luna_assistant.log"

    # --- Model Configuration ---
    MODEL_NAME = "gemma3:4b-it-q4_K_M"
    CONTEXT_WINDOW = 4096
    OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
    OLLAMA_HEALTH_CHECK = "http://localhost:11434/api/tags"

    # --- STT Configuration ---
    STT_MODEL_SIZE = "medium" # Upgraded for better accuracy
    STT_SAMPLE_RATE = 16000
    STT_COMPUTE_TYPE = "int8"
    STT_VAD_AGGRESSIVENESS = 3
    STT_FRAME_DURATION_MS = 30
    STT_SILENCE_THRESHOLD_MS = 800
    STT_MIN_VOICED_MS = 1000
    STT_MAX_VOICED_MS = 10000  # Maksimum 10 detik
    STT_MIN_VOLUME = 300       # Minimum RMS volume
    TEMP_AUDIO_FILE = TEMP_DIR / "temp_recording.wav"

    # --- TTS Configuration ---
    TTS_MODEL_PATH = str(BASE_DIR / "models/tts/en_US-amy-medium.onnx")

    # --- Security Settings ---
    INTERPRETER_AUTO_RUN = True
    SECURITY_COMMAND_BLACKLIST = ["rm -rf", "format", "shutdown", ":(){:|:&};"]

    # --- Memory Configuration ---
    MEMORY_FILE = BASE_DIR / "memory.json"
    MAX_MEMORY_SIZE = 10 # Number of past messages to remember

    # --- GUI Configuration ---
    GUI_COLORS = {
        'background': '#0f0f0f', 'input_bg': '#2a2a2a', 'user_msg': '#4c1d95',
        'assistant_msg': '#222222', 'text_primary': '#ffffff', 'text_secondary': '#999999',
        'accent': '#6b46c1', 'accent_hover': '#7c3aed', 'listening': '#2f855a',
        'thinking': '#d69e2e', 'error': '#e53e3e'
    }

    @classmethod
    def setup_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
