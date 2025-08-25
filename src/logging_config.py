"""
Logging configuration for Luna Voice Assistant.
"""
import logging
import sys
from pathlib import Path

def setup_logging(log_file_path: Path, log_level: int = logging.INFO) -> None:
    """
    Configure logging to file and console.
    
    Args:
        log_file_path: Path to the log file
        log_level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_file_path.parent.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)