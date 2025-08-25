"""
This is the main entry point for the Luna Voice Assistant application.
It handles logging setup, environment configuration, and launches the GUI.
"""
import sys
import logging
from pathlib import Path

import customtkinter as ctk

from .config import Config
from .logging_config import setup_logging
from .config_validator import run_validations
from .gui import AssistantApp

def setup_logging_wrapper():
    """Configures logging to file and console."""
    Config.setup_directories() # Ensure logs directory exists
    setup_logging(Config.LOG_FILE, logging.DEBUG) # Setup logging with DEBUG level

def main():
    """
    The sole entry point for the Luna Voice Assistant application.
    Initializes configuration, sets up the environment, and launches the GUI.
    """
    setup_logging_wrapper() # Setup logging first

    try:
        logging.info("🚀 Starting Luna Assistant...")

        # 1. Setup environment
        logging.info("⚙️ Setting up environment...")
        
        # 2. Validate configuration
        logging.info("🔍 Validating configuration...")
        if not run_validations():
            logging.warning("⚠️  Configuration validation issues found. Continuing anyway.")

        # 3. Configure GUI appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 4. Launch the application window
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
