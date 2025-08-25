"""
This module handles Speech-to-Text (STT) functionality using Faster Whisper and WebRTCVAD.
It provides a SpeechListener class to capture audio, detect speech, and transcribe it.
"""
import logging
import os
import queue
import sys
import threading
from typing import Callable, Optional, Any, cast
import webrtcvad

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel

from .config import Config

class SpeechListener:
    """
    Manages audio input, Voice Activity Detection (VAD), and speech transcription.
    """
    def __init__(self, on_transcription_result: Callable[[str], None]):
        self.on_transcription_result = on_transcription_result
        self.is_listening = False
        self.stream: Optional[sd.RawInputStream] = None
        self.audio_queue: queue.Queue = queue.Queue()
        self.voiced_frames_buffer: list = []
        self.silent_frames_count = 0
        self.is_speaking = False
        self.whisper_model: Optional[WhisperModel] = None
        self.vad: Optional[webrtcvad.Vad] = None
        self._initialize_models()

    def _initialize_models(self) -> None:
        logging.info("[STT] Loading Whisper model '%s'...", Config.STT_MODEL_SIZE)
        local_model_path = str(Config.BASE_DIR / "models/stt/faster-whisper-medium")
        self.whisper_model = WhisperModel(
            local_model_path,
            device="cpu",
            compute_type=Config.STT_COMPUTE_TYPE
        )
        logging.info("[STT] Initializing VAD...")
        self.vad = webrtcvad.Vad(Config.STT_VAD_AGGRESSIVENESS)
        logging.info("[STT] Model loaded successfully.")

    def _audio_callback(self, indata: np.ndarray, frames: int, callback_time: Any, status: Any) -> None:
        """Callback function for the audio stream."""
        if status:
            logging.warning("[STT] Audio callback status: %s", status)
        
        # Calculate RMS to check if audio has sufficient volume
        # Using numpy as audioop is not available
        audio_array = np.frombuffer(indata, dtype=np.int16)
        if audio_array.size > 0: # Ensure array is not empty
            # Convert to float32 before squaring to prevent overflow
            audio_array_float = audio_array.astype(np.float32)
            mean_squared = np.mean(audio_array_float**2)
            # Add a small epsilon to prevent sqrt of negative/zero if mean_squared is problematic
            rms = np.sqrt(mean_squared + 1e-9) 
            logging.debug("[STT] Audio callback - indata size: %d, audio_array size: %d, mean_squared: %.2f, RMS: %.2f", len(indata), audio_array.size, mean_squared, rms)
            if rms > Config.STT_MIN_VOLUME:
                self.audio_queue.put(bytes(indata))
        else:
            logging.debug("[STT] Audio callback received empty audio_array.")

    def start_listening(self) -> None:
        """Starts the audio stream and VAD processing."""
        if self.is_listening: return
        logging.info("[STT] Starting to listen (Hybrid Mode: VAD + PTT)...")
        self.is_listening = True
        self.voiced_frames_buffer.clear()
        self.silent_frames_count = 0
        self.is_speaking = False
        
        frame_size = int(Config.STT_SAMPLE_RATE * Config.STT_FRAME_DURATION_MS / 1000)
        self.stream = sd.RawInputStream(
            samplerate=Config.STT_SAMPLE_RATE, 
            blocksize=frame_size,
            channels=1, 
            dtype='int16', 
            callback=self._audio_callback
        )
        self.stream.start()
        threading.Thread(target=self._process_vad, daemon=True).start()

    def stop_listening(self) -> None:
        """Stops the audio stream and processes any remaining audio."""
        if not self.is_listening: return
        logging.info("[STT] PTT: Stopping recording manually.")
        self.is_listening = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.audio_queue.put(None)
        if self.voiced_frames_buffer:
            logging.info("[STT] PTT: Processing audio from buffer...")
            self._process_and_transcribe_buffer()

    def _process_vad(self) -> None:
        silence_threshold = int(Config.STT_SILENCE_THRESHOLD_MS / Config.STT_FRAME_DURATION_MS)
        min_voiced_frames = int(Config.STT_MIN_VOICED_MS / Config.STT_FRAME_DURATION_MS)
        max_voiced_frames = int(Config.STT_MAX_VOICED_MS / Config.STT_FRAME_DURATION_MS)

        # Ensure VAD is initialized before use
        if self.vad is None:
            logging.error("[STT] VAD not initialized")
            return

        while self.is_listening:
            try:
                frame = self.audio_queue.get(timeout=1.0)
                if frame is None or not self.is_listening: # Added check for self.is_listening
                    break
                
                # Check if frame has sufficient energy
                # Using numpy as audioop is not available
                audio_array = np.frombuffer(frame, dtype=np.int16)
                if audio_array.size == 0: # Ensure array is not empty
                    logging.debug("[VAD] VAD process received empty audio_array, skipping frame.")
                    continue
                # Convert to float32 before squaring to prevent overflow
                audio_array_float = audio_array.astype(np.float32)
                mean_squared = np.mean(audio_array_float**2)
                # Add a small epsilon to prevent sqrt of negative/zero if mean_squared is problematic
                rms = np.sqrt(mean_squared + 1e-9)
                logging.debug("[VAD] VAD process - frame size: %d, audio_array size: %d, mean_squared: %.2f, RMS: %.2f", len(frame), audio_array.size, mean_squared, rms)
                if rms < Config.STT_MIN_VOLUME:
                    continue
                
                # Use cast to tell Pylance that self.vad is not None here
                is_speech = cast(webrtcvad.Vad, self.vad).is_speech(frame, Config.STT_SAMPLE_RATE)
                
                if is_speech:
                    if not self.is_speaking:
                        self.is_speaking = True
                        logging.info("[VAD] Speech detected!")
                    self.voiced_frames_buffer.append(frame)
                    self.silent_frames_count = 0
                    
                    # Safety check: prevent buffer from growing too large
                    if len(self.voiced_frames_buffer) > max_voiced_frames:
                        logging.info("[VAD] Maximum speech duration reached. Processing audio...")
                        self._process_and_transcribe_buffer()
                        self.is_speaking = False
                        self.voiced_frames_buffer.clear()
                        
                elif self.is_speaking:
                    self.voiced_frames_buffer.append(frame)
                    self.silent_frames_count += 1
                    if self.silent_frames_count > silence_threshold:
                        logging.info("[VAD] Silence detected. Processing audio...")
                        if len(self.voiced_frames_buffer) > min_voiced_frames:
                            self._process_and_transcribe_buffer()
                        else:
                            logging.info("[VAD] Audio too short, ignoring.")
                        self.is_speaking = False
                        self.voiced_frames_buffer.clear()
                        self.silent_frames_count = 0
                        
            except queue.Empty:
                continue

    def _process_and_transcribe_buffer(self) -> None:
        recording_bytes = b"".join(self.voiced_frames_buffer)
        # Ensure we don't process an empty buffer or too short audio
        if not recording_bytes or len(recording_bytes) < 2000:  # ~125ms of audio
            return
            
        wav.write(Config.TEMP_AUDIO_FILE, Config.STT_SAMPLE_RATE, np.frombuffer(recording_bytes, dtype=np.int16))
        self._transcribe_audio(str(Config.TEMP_AUDIO_FILE))
        self.voiced_frames_buffer.clear()

    def _transcribe_audio(self, filepath: str) -> None:
        """Transcribes the audio file using Whisper model."""
        # Ensure whisper_model is initialized before use
        if self.whisper_model is None:
            logging.error("[STT] Whisper model not initialized")
            return
            
        try:
            logging.info("[STT] Transcribing audio...")
            # Enhanced initial prompt for Indonesian language
            initial_prompt = """
            Afif, Luna, EndeavourOS, Hyprland, KDE, Ollama, Python, Firefox, browser, terminal, 
            buka, jalankan, buka firefox, buka terminal, kode, program, python, java, c++, 
            kamu masih ingat, kamu tahu aku, terima kasih, hai, halo, assalamualaikum, 
            terimakasih, apakah, bagaimana, kenapa, dimana, kapan, siapa, mengapa, 
            tolong, bantu, help, assist, open, run, execute, code, programming.
            """

            # Use cast to tell Pylance that self.whisper_model is not None here
            segments, _ = cast(WhisperModel, self.whisper_model).transcribe(
                filepath,
                beam_size=10, # Increased beam size for potentially better accuracy
                language="id",
                initial_prompt=initial_prompt,
                condition_on_previous_text=False,
                temperature=0.0,
                compression_ratio_threshold=2.2,
                log_prob_threshold=-0.8,
                no_speech_threshold=0.7,
                word_timestamps=False,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500, "speech_pad_ms": 200} # Used dict literal
            )

            text = "".join(segment.text for segment in segments).strip()

            # Additional filters for strange results
            if not text or len(text) < 2:
                logging.info("[STT] Detected text ignored (too short): '%s'", text)
                return
                
            # Filter out common hallucinations specifically for Indonesian
            common_hallucinations = [
                "terima kasih sudah menonton",
                "selamat menonton",
                "hai guys",
                "halo guys",
                "like dan subscribe",
                "thank you for watching",
                "jangan lupa like",
                "jangan lupa subscribe"
            ]
            
            if any(hallucination in text.lower() for hallucination in common_hallucinations):
                logging.info("[STT] Detected common hallucination: '%s'", text)
                return

            logging.info("[STT] Detected text: '%s'", text)
            self.on_transcription_result(text)
        except Exception as err: # pylint: disable=broad-exception-caught
            logging.error("Error during transcription: %s", err, exc_info=True)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
