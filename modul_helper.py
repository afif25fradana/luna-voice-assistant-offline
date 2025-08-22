"""
This module provides helper functions for the Luna Voice Assistant,
primarily for executing personal shortcuts.
"""
import urllib.parse
import subprocess
from personal_shortcuts import PERSONAL_SHORTCUTS

def run_shortcut(command_key: str, **kwargs) -> str:
    """
    Finds and executes a command from PERSONAL_SHORTCUTS based on the key.
    Substitutes placeholders like {query}, {pkg}, {term}, etc.
    Returns the command string that was executed.
    """
    if command_key not in PERSONAL_SHORTCUTS:
        raise ValueError(f"No shortcut found for key: {command_key}")
    
    cmd_template = PERSONAL_SHORTCUTS[command_key]
    
    # URL-encode all keyword arguments before formatting
    encoded_kwargs = {k: urllib.parse.quote(str(v)) for k, v in kwargs.items()}
    
    cmd = cmd_template.format(**encoded_kwargs)
    
    # Use subprocess.Popen for non-blocking execution
    try:
        subprocess.Popen(cmd, shell=True, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        return cmd
    except FileNotFoundError:
        raise FileNotFoundError(f"Command '{cmd.split()[0]}' not found. Please ensure it's installed and in your system's PATH.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during shortcut execution: {e}")
