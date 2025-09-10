# Hey there! Meet Luna Voice Assistant v5.1! 👋
> [!WARNING]
> **🚨 This Project is Discontinued 🚨**
>
> This project was created for learning basic functions. The new, improved project with a better foundation is available at: **[Lyra Voice Assistant](https://github.com/afif25fradana/lyra-voice-assistant.git)**

I'm so excited to introduce you to Luna, my secure, offline-capable AI voice assistant! I've poured a lot of effort into building her with a super robust, modular architecture, making sure she's got enhanced security features, and a really responsive, user-friendly interface.

## ✨ What makes Luna awesome? (My favorite features!)

-   **🤖 My Brain (Intelligent & Versatile AI)**: Luna is powered by a custom Ollama model (`gemma3:4b-it-q4_K_M`) that I've set up for both casual chats and executing code. She's pretty smart!
-   **🗣️ She Listens! (High-Accuracy Speech-to-Text)**: I've integrated `faster-whisper` with VAD (Voice Activity Detection) so Luna can understand you with incredible accuracy and respond quickly. It's almost like magic!
-   **🔒 Keeping You Safe (Secure by Design)**: Your security is super important to me. That's why Luna features a command blacklist and safe parsing of interpreter output to prevent any naughty or malicious actions.
-   **💬 Her Voice (Natural Text-to-Speech)**: Luna speaks using `piper`, and I think her voice sounds really clear and natural. It's a pleasure to listen to!
-   **🚀 Speedy & Smooth (Optimized Performance)**: I've made sure Luna includes a non-blocking warm-up for the Ollama model. This means no annoying initial request timeouts – she's ready when you are!
-   **🧠 Smarty Pants (Smart Intent Routing)**: Luna has a dedicated AI router that's great at figuring out what you want to do, seamlessly switching between just chatting and running code for you.
-   **🖥️ Pretty Face (Modern & Responsive GUI)**: I designed her interface with `customtkinter` to be clean, intuitive, and a joy to use. I hope you like it!
-   **⚙️ Easy to Tweak (Centralized Configuration)**: I've made it super easy for you to manage all of Luna's settings from one simple `config.py` file. Customize away!

## 🏗️ How I Built Luna (Her Architecture)

I designed Luna with a clear separation of concerns, which makes her really easy for me (and hopefully you!) to maintain and extend. It's like building with LEGOs – each part has its job!

```
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│   GUI Layer       │       │   Audio Layer     │       │   AI Layer        │
│ (gui.py)          │       │ (modul_stt.py)    │       │ (modul_ai.py)     │
├───────────────────┤       ├───────────────────┤       ├───────────────────┤
│ • CustomTkinter   │◄─────►│ • STT (Whisper)   │◄─────►│ • Intent Router   │
│ • Message Bubbles │       │ • TTS (Piper)     │       │ • Ollama Client   │
│ • Status Updates  │       │ • VAD             │       │ • Open Interpreter│
│ • Input Handling  │       │                   │       │ • Security Filter │
└───────────────────┘       └───────────────────┘       └───────────────────┘
         ▲                           ▲                           ▲
         │                           │                           │
         └───────────────────────────┬───────────────────────────┘
                                     │
                                     │
                         ┌─────────────────────────┐
                         │      Core Services      │
                         │ (config.py, main.py)    │
                         ├─────────────────────────┤
                         │ • App Configuration     │
                         │ • Directory Setup       │
                         │ • Application Entrypoint│
                         │ • Chat Memory           │
                         └─────────────────────────┘
```

## 🚀 Ready to Get Started? (Installation Guide)

Want to try Luna out yourself? Here's how you can get her up and running!

### What You'll Need (Prerequisites)

-   **Python 3.11+**: Make sure you have a recent version of Python.
-   **Ollama**: You'll need Ollama installed and running to power Luna's brain.
-   An audio backend like **PulseAudio** or **ALSA**: For Luna to hear and speak!

### My Step-by-Step Setup Guide

1.  **Grab the Code (Clone the Repository)**
    ```bash
    git clone https://github.com/afif25fradana/luna-voice-assistant-offline.git
    cd luna-voice-assistant-offline
    ```

2.  **Create a Cozy Space (Virtual Environment)**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install Her Tools (Install Dependencies)**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Luna's Brain (Set Up the Ollama Model)**
    I've included a `Modelfile.example` in the project root. You can either:
    *   Rename `Modelfile.example` to `Modelfile` and use it directly.
    *   Create your own `Modelfile` based on `Modelfile.example`, customizing Luna's persona as you like! Just be mindful of any personal information you include if you plan to share your project.

    Once you have your `Modelfile` ready, create the custom model:
    ```bash
    ollama create gemma3:4b-it-q4_K_M -f Modelfile
    ```
    You can verify the model is available by running:
    ```bash
    ollama list
    ```

5.  **Give Her a Voice (Download the TTS Model)**
    The voice model Luna uses is `en_US-amy-medium.onnx`. Here's how to get it:
    ```bash
    mkdir -p models/tts
    wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx -O models/tts/en_US-amy-medium.onnx
    wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json -O models/tts/en_US-amy-medium.onnx.json
    ```

6.  **Bring Her to Life! (Run the Application)**
    ```bash
    python main.py
    ```

## ⚙️ How to Customize Luna (Configuration)

I've made it super easy to tweak Luna to your liking! All the key settings can be adjusted in `config.py`:

```python
# config.py

class Config:
    # --- Model Configuration ---
    MODEL_NAME = "gemma3:4b-it-q4_K_M"
    OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

    # --- STT Configuration ---
    STT_MODEL_SIZE = "medium"  # e.g., "tiny", "base", "small", "medium"

    # --- TTS Configuration ---
    TTS_MODEL_PATH = str(BASE_DIR / "models/tts/en_US-amy-medium.onnx")

    # --- Security Settings ---
    INTERPRETER_AUTO_RUN = True
    SECURITY_COMMAND_BLACKLIST = ["rm -rf", "format", "shutdown", ":(){:|:&};"]
 SECURITY_COMMAND_BLACKLIST = ["rm -rf", "format", "shutdown", ":(){:|:&};"]
```

## 🔧 Recent Improvements

### Security Enhancements
- Enhanced command validation with comprehensive safety checks
- Improved permission handling for dangerous operations
- Better subprocess execution with `shlex.split` for safer command parsing

### Reliability Improvements
- Added comprehensive unit test suite with 14 test cases
- Implemented configuration validation at startup
- Enhanced error handling and recovery mechanisms
- Added graceful shutdown handling with signal handlers

### Developer Experience
- Added type hints to all modules for better IDE support
- Improved code documentation with detailed docstrings
- Centralized logging configuration
- Better code organization and modularity

### Fixed Issues
- Resolved unterminated f-string literals that would cause syntax errors
- Fixed relative import issues that prevented proper module loading
- Corrected timeout values for better performance
- Improved error messages and logging
