"""
This module handles Text-to-Speech (TTS) functionality using Piper.
It provides a TTSManager class to synthesize speech from text.
"""
import logging
import threading
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
from piper import PiperVoice

from .config import Config

class TTSManager:
    """
    Manages Text-to-Speech synthesis using the Piper voice model.
    """
    def __init__(self, on_speaking_start: Optional[Callable[[], None]] = None, 
                 on_speaking_stop: Optional[Callable[[], None]] = None):
        self.voice_model: Optional[PiperVoice] = None
        self.audio_lock = threading.Lock()
        self.on_speaking_start = on_speaking_start
        self.on_speaking_stop = on_speaking_stop
        self._load_voice_model()

    def _load_voice_model(self) -> None:
        """Loads the Piper voice model."""
        try:
            logging.info("[TTS] Loading voice model: %s", Config.TTS_MODEL_PATH)
            self.voice_model = PiperVoice.load(Config.TTS_MODEL_PATH)
            logging.info("[TTS] Voice model loaded successfully.")
        except Exception as err:  # Catching general Exception for now, can be refined if PiperVoice exposes specific errors
            logging.critical("[TTS] FATAL: Failed to load voice model: %s", err, exc_info=True)
            raise

    def _speak_task(self, text_to_speak: str) -> None:
        """Synthesizes and plays the given text in a separate thread."""
        if not self.voice_model:
            logging.error("[TTS] Voice model not loaded. Cannot speak.")
            return
            
        with self.audio_lock:
            if self.on_speaking_start:
                self.on_speaking_start()
            logging.info("[*] Speaking: '%s'", text_to_speak)
            try:
                audio_generator = self.voice_model.synthesize(text_to_speak)
                audio_bytes = b"".join(chunk.audio_int16_bytes for chunk in audio_generator)
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
                sd.play(audio_np, self.voice_model.config.sample_rate)
                sd.wait()
            except Exception as err:  # Catching general Exception for now, can be refined
                logging.error("[TTS] Error during speech synthesis or playback: %s", err, exc_info=True)
            finally:
                if self.on_speaking_stop:
                    self.on_speaking_stop()

    def speak(self, text_to_speak: str) -> None:
        """Initiates speech synthesis in a new thread."""
        if text_to_speak:
            threading.Thread(target=self._speak_task, args=(text_to_speak,), daemon=True).start()

def stop_speaking() -> None:
    """Stops any currently playing audio."""
    sd.stop()
