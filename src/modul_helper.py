"""
This module provides helper functions for the Luna Voice Assistant,
primarily for executing personal shortcuts.
"""
import urllib.parse
import subprocess
import shlex
import logging
from typing import Dict, List, Any

# Use absolute imports for better testability
try:
    from .personal_shortcuts import PERSONAL_SHORTCUTS
    from .config import Config
except ImportError:
    # Fallback for when running tests
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from personal_shortcuts import PERSONAL_SHORTCUTS
    from config import Config

# Predefined safe commands that can be executed
SAFE_COMMANDS: set = {
    'xdg-open', 'firefox', 'google-chrome', 'chromium', 
    'code', 'subl', 'gedit', 'nano', 'vim', 'emacs'
}

def _is_command_safe(command_list: List[str]) -> bool:
    """
    Validate that a command is safe to execute.
    Returns True if safe, False otherwise.
    """
    # Dangerous patterns to check
    DANGEROUS_PATTERNS: list = [
        'rm -rf', 'format', 'shutdown', ':(){:|:&};',
        'sudo', 'su', 'chmod 777', 'chown root',
        'mkfs', 'dd if=', 'wget .* -O /', 'curl .* | sh',
        'cat /etc/passwd', 'cat /etc/shadow'
    ]
    
    if not command_list:
        return False
    
    command_name = command_list[0]
    
    # If it's a known safe command, allow it
    if command_name in SAFE_COMMANDS:
        return True
    
    # Check for dangerous patterns in the entire command
    command_str = ' '.join(command_list).lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command_str:
            return False
    
    return True

def run_shortcut(command_key: str, **kwargs: Any) -> str:
    """
    Finds and executes a command from PERSONAL_SHORTCUTS based on the key.
    Substitutes placeholders like {query}, {pkg}, {term}, etc.
    Returns the command string that was executed.
    """
    if command_key not in PERSONAL_SHORTCUTS:
        raise ValueError(f"No shortcut found for key: {command_key}")
    
    cmd_template = PERSONAL_SHORTCUTS[command_key]
    
    # URL-encode all keyword arguments before formatting
    encoded_kwargs: Dict[str, str] = {k: urllib.parse.quote(str(v)) for k, v in kwargs.items()}
    
    cmd = cmd_template.format(**encoded_kwargs)
    
    # Use subprocess.Popen with shlex.split for safer execution
    try:
        # Split the command properly to avoid shell=True
        cmd_list = shlex.split(cmd)
        
        # Validate command safety before execution
        if not _is_command_safe(cmd_list):
            raise PermissionError(f"Command '{cmd}' is not allowed for security reasons.")
        
        # Execute the command
        subprocess.Popen(cmd_list, 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)
        logging.info("[Helper] Executed safe command: %s", cmd)
        return cmd
    except FileNotFoundError:
        raise FileNotFoundError(f"Command '{cmd.split()[0]}' not found. Please ensure it's installed and in your system's PATH.")
    except Exception as e:
        logging.error("[Helper] Error executing command '%s': %s", cmd, e)
        raise Exception(f"An unexpected error occurred during shortcut execution: {e}")
