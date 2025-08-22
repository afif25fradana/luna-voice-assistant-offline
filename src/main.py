"""
This is the main entry point for the Luna Voice Assistant application.
It handles logging setup, environment configuration, and launches the GUI.
"""
import sys
import logging
from pathlib import Path

import customtkinter as ctk

from .config import Config
from .gui import AssistantApp

def setup_logging():
    """Configures logging to file and console."""
    Config.setup_directories() # Ensure logs directory exists
    
    logging.basicConfig(
        level=logging.DEBUG, # Change to DEBUG to capture all detailed logs
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('httpx').setLevel(logging.WARNING) # Suppress noisy httpx logs
    logging.getLogger('urllib3').setLevel(logging.WARNING) # Suppress noisy urllib3 logs

def main():
    """
    The sole entry point for the Luna Voice Assistant application.
    Initializes configuration, sets up the environment, and launches the GUI.
    """
    setup_logging() # Setup logging first

    try:
        logging.info("🚀 Starting Luna Assistant...")

        # 1. Setup environment
        logging.info("⚙️ Setting up environment...")

        # 2. Configure GUI appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 3. Launch the application window
        logging.info("🖼️ Launching GUI...")
        app = AssistantApp()
        app.mainloop()

        logging.info("✅ Luna Assistant shut down gracefully.")

    except FileNotFoundError as err:
        logging.critical("❌ CRITICAL ERROR: A required file was not found. Details: %s", err)
        logging.critical("   Please ensure all model files are correctly placed.")
        sys.exit(1)
    except Exception as err: # pylint: disable=broad-exception-caught
        logging.critical("❌ An unexpected critical error occurred: %s", err, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
