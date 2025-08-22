"""
This module defines the graphical user interface (GUI) for the Luna Voice Assistant.
It uses CustomTkinter for the UI elements and integrates with other modules
for speech-to-text, text-to-speech, AI processing, and memory management.
"""
import re
import time
import logging

import customtkinter as ctk
from PIL import Image, ImageDraw

from config import Config
from modul_stt import SpeechListener
from modul_ai import ask_ollama, warm_up_ollama, chat_memory
from modul_tts import TTSManager, stop_speaking

class MessageBubble(ctk.CTkFrame):
    """
    A custom Tkinter frame to display chat messages as bubbles.
    """
    def __init__(self, parent, message, is_user=True, timestamp=None):
        super().__init__(parent, fg_color=Config.GUI_COLORS['user_msg'] if is_user else \
                         Config.GUI_COLORS['assistant_msg'], corner_radius=18)
        
        self.grid_columnconfigure(0, weight=1)

        self.message_label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=16), \
            text_color=Config.GUI_COLORS['text_primary'], wraplength=500, justify="left", anchor="w")
        self.message_label.grid(row=0, column=0, padx=16, pady=(12, 0), sticky="ew")

        if timestamp:
            self.timestamp_label = ctk.CTkLabel(self, text=timestamp, font=ctk.CTkFont(size=10), \
                text_color=Config.GUI_COLORS['text_secondary'], justify="right", anchor="e")
            self.timestamp_label.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="e")

    def update_text(self, new_text):
        """Updates the text displayed in the message bubble."""
        self.message_label.configure(text=new_text)

class AssistantApp(ctk.CTk):
    """
    The main application class for the Luna Voice Assistant GUI.
    """
    def __init__(self):
        super().__init__()
        self.title("Luna Voice Assistant")
        self.geometry("800x700")
        self.minsize(600, 500)
        self.configure(fg_color=Config.GUI_COLORS['background'])

        self.listener = SpeechListener(on_transcription_result=self.handle_stt_result)
        self.tts_manager = TTSManager(on_speaking_start=self._on_speaking_start, on_speaking_stop=self._on_speaking_stop)
        self.is_listening = False
        self.is_speaking = False
        self.current_assistant_bubble: MessageBubble | None = None
        self.sentence_buffer = ""
        self.message_count = 0
        self.is_processing = False
        self.last_input_time = 0

        self._create_widgets()

        # --- BACKGROUND PROCESS INITIALIZATION ---
        self.after(100, self._add_welcome_message)
        warm_up_ollama()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        """Creates and arranges all GUI widgets."""
        # Header
        self.header_frame = ctk.CTkFrame(self, height=60, fg_color=Config.GUI_COLORS['background'], corner_radius=0)
        self.header_frame.pack(fill="x")
        self.title_label = ctk.CTkLabel(self.header_frame, text="Luna", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(side="left", padx=25, pady=15)
        self._set_avatar_image("avatar.png")

        # Chat Frame
        self.chat_frame = ctk.CTkScrollableFrame(self, fg_color=Config.GUI_COLORS['background'])
        self.chat_frame.pack(fill="both", expand=True)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Input Frame
        self.input_frame = ctk.CTkFrame(self, height=80, fg_color=Config.GUI_COLORS['background'], corner_radius=0)
        self.input_frame.pack(fill="x")
        self.input_container = ctk.CTkFrame(self.input_frame, fg_color=Config.GUI_COLORS['input_bg'], \
                                            corner_radius=25, height=50)
        self.input_container.pack(fill="x", padx=25, pady=15)
        self.input_container.grid_columnconfigure(1, weight=1)

        self.text_input = ctk.CTkEntry(self.input_container, placeholder_text="Send a message...", \
                                       font=ctk.CTkFont(size=16), fg_color="transparent", border_width=0)
        self.text_input.grid(row=0, column=1, sticky="ew", pady=12, padx=5)
        self.text_input.bind("<Return>", self.handle_text_input)

        self.mic_button = ctk.CTkButton(self.input_container, text="🎤", width=40, height=40, corner_radius=20, \
                                        fg_color=Config.GUI_COLORS['accent'], hover_color=Config.GUI_COLORS['accent_hover'], \
                                        command=self.toggle_listening)
        self.mic_button.grid(row=0, column=0, padx=(10, 5), pady=5)

        self.send_btn = ctk.CTkButton(self.input_container, text="➤", width=40, height=40, corner_radius=20, \
                                      font=ctk.CTkFont(size=18), fg_color=Config.GUI_COLORS['accent'], \
                                      hover_color=Config.GUI_COLORS['accent_hover'], command=self.handle_text_input)
        self.send_btn.grid(row=0, column=2, padx=(5, 10), pady=5)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=12), text_color=Config.GUI_COLORS['text_secondary'])
        self.status_label.pack(pady=(0, 5))

        # Clear Chat Button
        self.clear_chat_button = ctk.CTkButton(self, text="Clear Chat", command=self._clear_chat_history, \
                                                fg_color="transparent", hover_color=Config.GUI_COLORS['input_bg'], \
                                                text_color=Config.GUI_COLORS['text_secondary'], font=ctk.CTkFont(size=12))
        self.clear_chat_button.pack(pady=(0, 10))

    def set_status(self, text, color):
        """Sets the text and color of the status label."""
        self.status_label.configure(text=text, text_color=color)

    def toggle_listening(self):
        """Toggles the speech-to-text listening state."""
        if self.is_processing:
            logging.info("[GUI] Ignoring mic toggle: AI is busy.")
            return

        if self.is_listening:
            self.listener.stop_listening()
            self.is_listening = False
            self.mic_button.configure(fg_color=Config.GUI_COLORS['accent'])
            self.set_status("Ready", Config.GUI_COLORS['text_secondary'])
        else:
            self.listener.start_listening()
            self.is_listening = True
            self.mic_button.configure(fg_color=Config.GUI_COLORS['listening'])
            self.set_status("Listening...", Config.GUI_COLORS['listening'])

    def handle_stt_result(self, text):
        """Handles the transcription result from the speech-to-text module."""
        current_time = time.time()
        # Prevent processing the same input multiple times in quick succession
        if current_time - self.last_input_time > 1.0:  # At least 1 second between inputs
            self.last_input_time = current_time
            self.after(0, self._process_input, text)

    def _clear_chat_history(self):
        """Clears all messages from the chat history."""
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.message_count = 0
        self.current_assistant_bubble = None
        from modul_ai import chat_memory
        chat_memory.clear_memory()
        self._add_welcome_message()

    def handle_text_input(self, event=None):
        """Handles text input from the entry field."""
        text = self.text_input.get()
        if text:
            self.text_input.delete(0, "end")
            self._process_input(text)

    def _process_input(self, text):
        """Processes user input, either from STT or text entry."""
        if not text or not text.strip():
            logging.info("[GUI] Ignoring empty input.")
            return

        if self.is_processing:
            logging.info("[GUI] Ignoring input '%s': AI is busy.", text)
            return

        if self.is_listening:
            self.is_listening = False
            self.mic_button.configure(fg_color=Config.GUI_COLORS['accent'])

        self._add_message(text, is_user=True, timestamp=time.strftime("%H:%M"))
        self._process_full_cycle(text)

    def _process_full_cycle(self, user_text):
        """Initiates the full AI processing cycle for user input."""
        self.is_processing = True
        self.current_assistant_bubble = self._add_message("...", is_user=False)
        self.set_status("Thinking...", Config.GUI_COLORS['thinking'])
        self._toggle_buttons(disabled=True)
        self.sentence_buffer = ""

        ai_response_generator = ask_ollama(user_text)
        # Pass the newly created bubble directly to the update function
        self._update_assistant_bubble(ai_response_generator, self.current_assistant_bubble)

    def _update_assistant_bubble(self, text_generator, bubble: MessageBubble):
        """Updates the assistant's message bubble with streaming text."""
        # The 'bubble' argument is guaranteed to be a MessageBubble instance here,
        # which resolves the Pylance error about 'None' type.
        if not bubble.winfo_exists():
            logging.warning("[GUI] Warning: Message bubble is invalid or destroyed. Stopping update.")
            self.set_status("Error: UI update interrupted.", Config.GUI_COLORS['error'])
            self._toggle_buttons(disabled=False)
            self.is_processing = False
            return

        try:
            next_token = next(text_generator)
            current_text = bubble.message_label.cget("text")
            if current_text == "...":
                current_text = ""
            new_text = current_text + next_token
            bubble.update_text(new_text)

            self.sentence_buffer += next_token
            match = re.search(r'([.?!])', self.sentence_buffer)
            if match:
                split_point = match.end()
                sentence_to_speak = self.sentence_buffer[:split_point]
                self.sentence_buffer = self.sentence_buffer[split_point:]
                self.speak(sentence_to_speak.strip())

            self.after(10, self._update_assistant_bubble, text_generator, bubble)
        except StopIteration:
            if self.sentence_buffer.strip():
                self.speak(self.sentence_buffer.strip())
            self.set_status("Ready", Config.GUI_COLORS['text_secondary'])
            self._toggle_buttons(disabled=False)
            self.is_processing = False
        except Exception as err: # pylint: disable=broad-exception-caught
            logging.error("[GUI] An unexpected error occurred during assistant bubble update: %s", err, exc_info=True)
            error_message = f"Error: {err}"
            if bubble.winfo_exists(): # Check if widget still exists
                bubble.update_text(error_message)
            self.set_status("Error", Config.GUI_COLORS['error'])
            self._toggle_buttons(disabled=False)
            self.is_processing = False

    def speak(self, text_to_speak):
        """Initiates text-to-speech for the given text."""
        self.tts_manager.speak(text_to_speak)

    def _on_speaking_start(self):
        """Callback when TTS starts speaking."""
        self.is_speaking = True
        self.after(0, lambda: self.set_status("Speaking...", Config.GUI_COLORS['accent']))
        self.after(0, lambda: self._toggle_buttons(disabled=True))

    def _on_speaking_stop(self):
        """Callback when TTS stops speaking."""
        self.is_speaking = False
        if not self.is_processing:
            self.after(0, lambda: self.set_status("Ready", Config.GUI_COLORS['text_secondary']))
            self.after(0, lambda: self._toggle_buttons(disabled=False))

    def _add_message(self, text, is_user=True, timestamp=None):
        """Adds a new message bubble to the chat display."""
        if timestamp is None:
            timestamp = time.strftime("%H:%M")

        bubble = MessageBubble(self.chat_frame, text, is_user=is_user, timestamp=timestamp)
        bubble.grid(row=self.message_count, column=0, sticky="e" if is_user else "w", \
                    padx=(100 if is_user else 20, 20 if is_user else 100), pady=5)
        self.message_count += 1
        self.after(100, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))
        return bubble

    def _toggle_buttons(self, disabled=False):
        """Enables or disables input buttons."""
        state = "disabled" if disabled else "normal"
        self.mic_button.configure(state=state)
        self.send_btn.configure(state=state)
        self.text_input.configure(state=state)

    def _add_welcome_message(self):
        """Adds the initial welcome message to the chat."""
        welcome_text = "Hello! I'm Luna. How can I help you today?"
        self._add_message(welcome_text, is_user=False, timestamp=time.strftime("%H:%M"))
        self.speak(welcome_text)

    def _set_avatar_image(self, image_path):
        """Loads and sets the avatar image in the header."""
        try:
            img = Image.open(image_path).resize((40, 40), Image.Resampling.LANCZOS)
            mask = Image.new('L', (40, 40), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 40, 40), fill=255)
            img.putalpha(mask)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
            avatar = ctk.CTkLabel(self.header_frame, image=ctk_img, text="")
            avatar.pack(side="right", padx=20, pady=10)
        except Exception as err: # pylint: disable=broad-exception-caught
            logging.warning("Could not load avatar image: %s", err)

    def _on_closing(self):
        """Handles actions to perform when the application window is closed."""
        logging.info("[GUI] Shutting down...")
        try:
            logging.info("[GUI] Stopping TTS speaking...")
            stop_speaking()
            logging.info("[GUI] TTS speaking stopped.")
        except Exception as err: # pylint: disable=broad-exception-caught
            logging.error("[GUI] Error stopping TTS: %s", err, exc_info=True)

        try:
            if self.listener and self.listener.is_listening:
                logging.info("[GUI] Stopping STT listener...")
                self.listener.stop_listening()
                logging.info("[GUI] STT listener stopped.")
        except Exception as err: # pylint: disable=broad-exception-caught
            logging.error("[GUI] Error stopping STT listener: %s", err, exc_info=True)
            
        logging.info("[GUI] Destroying GUI window...")
        self.destroy()
        logging.info("[GUI] GUI window destroyed.")
