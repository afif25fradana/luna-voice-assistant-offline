"""
Configuration validation for Luna Voice Assistant.
"""
import os
import logging
from pathlib import Path
from typing import List, Tuple

# Use absolute imports for better testability
try:
    from .config import Config
except ImportError:
    # Fallback for when running tests
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import Config

def validate_config() -> List[Tuple[str, str]]:
    """
    Validate the configuration settings.
    
    Returns:
        List of tuples containing (validation_type, message) for any issues found
    """
    issues = []
    
    # Validate required directories
    required_dirs = [
        ("TEMP_DIR", Config.TEMP_DIR),
        ("LOGS_DIR", Config.LOGS_DIR)
    ]
    
    for dir_name, dir_path in required_dirs:
        if not isinstance(dir_path, Path):
            issues.append(("CONFIG", f"{dir_name} is not a Path object"))
        elif not dir_path.is_absolute():
            issues.append(("CONFIG", f"{dir_name} is not an absolute path"))
    
    # Validate required files
    required_files = [
        ("LOG_FILE", Config.LOG_FILE),
        ("MEMORY_FILE", Config.MEMORY_FILE),
        ("LONG_TERM_MEMORY_FILE", Config.LONG_TERM_MEMORY_FILE)
    ]
    
    for file_name, file_path in required_files:
        if not isinstance(file_path, Path):
            issues.append(("CONFIG", f"{file_name} is not a Path object"))
        elif not file_path.is_absolute():
            issues.append(("CONFIG", f"{file_name} is not an absolute path"))
    
    # Validate model paths
    if not isinstance(Config.TTS_MODEL_PATH, str):
        issues.append(("CONFIG", "TTS_MODEL_PATH is not a string"))
    
    # Validate numeric values
    numeric_configs = [
        ("STT_SAMPLE_RATE", Config.STT_SAMPLE_RATE, 8000, 192000),
        ("CONTEXT_WINDOW", Config.CONTEXT_WINDOW, 1024, 32768),
        ("MAX_MEMORY_SIZE", Config.MAX_MEMORY_SIZE, 1, 100)
    ]
    
    for config_name, value, min_val, max_val in numeric_configs:
        if not isinstance(value, int):
            issues.append(("CONFIG", f"{config_name} is not an integer"))
        elif not min_val <= value <= max_val:
            issues.append(("CONFIG", f"{config_name} ({value}) is outside valid range [{min_val}, {max_val}]"))
    
    # Validate string values
    string_configs = [
        ("MODEL_NAME", Config.MODEL_NAME),
        ("STT_MODEL_SIZE", Config.STT_MODEL_SIZE),
        ("STT_COMPUTE_TYPE", Config.STT_COMPUTE_TYPE)
    ]
    
    for config_name, value in string_configs:
        if not isinstance(value, str) or not value:
            issues.append(("CONFIG", f"{config_name} is not a valid string"))
    
    # Validate URLs
    url_configs = [
        ("OLLAMA_ENDPOINT", Config.OLLAMA_ENDPOINT),
        ("OLLAMA_HEALTH_CHECK", Config.OLLAMA_HEALTH_CHECK)
    ]
    
    for config_name, value in url_configs:
        if not isinstance(value, str) or not value:
            issues.append(("CONFIG", f"{config_name} is not a valid string"))
        elif not (value.startswith("http://") or value.startswith("https://")):
            issues.append(("CONFIG", f"{config_name} is not a valid URL"))
    
    # Validate GUI colors
    if not isinstance(Config.GUI_COLORS, dict):
        issues.append(("CONFIG", "GUI_COLORS is not a dictionary"))
    else:
        required_colors = ['background', 'input_bg', 'user_msg', 'assistant_msg', 
                          'text_primary', 'text_secondary', 'accent', 'accent_hover', 
                          'listening', 'thinking', 'error']
        for color_name in required_colors:
            if color_name not in Config.GUI_COLORS:
                issues.append(("CONFIG", f"Missing GUI color: {color_name}"))
    
    # Validate security settings
    if not isinstance(Config.SECURITY_COMMAND_BLACKLIST, list):
        issues.append(("CONFIG", "SECURITY_COMMAND_BLACKLIST is not a list"))
    
    if not isinstance(Config.INTERPRETER_AUTO_RUN, bool):
        issues.append(("CONFIG", "INTERPRETER_AUTO_RUN is not a boolean"))
    
    return issues

def validate_model_files() -> List[Tuple[str, str]]:
    """
    Validate that required model files exist.
    
    Returns:
        List of tuples containing (validation_type, message) for any issues found
    """
    issues = []
    
    # Check TTS model file
    tts_model_path = Path(Config.TTS_MODEL_PATH)
    if not tts_model_path.exists():
        issues.append(("MODEL", f"TTS model file not found: {tts_model_path}"))
    
    # Check TTS model config file
    tts_config_path = tts_model_path.with_suffix('.onnx.json')
    if not tts_config_path.exists():
        issues.append(("MODEL", f"TTS model config file not found: {tts_config_path}"))
    
    # Check STT model directory
    stt_model_dir = Config.BASE_DIR / "models/stt" / f"faster-whisper-{Config.STT_MODEL_SIZE}"
    if not stt_model_dir.exists():
        issues.append(("MODEL", f"STT model directory not found: {stt_model_dir}"))
    
    return issues

def run_validations() -> bool:
    """
    Run all validations and log any issues.
    
    Returns:
        True if all validations pass, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Run configuration validation
    config_issues = validate_config()
    model_issues = validate_model_files()
    
    all_issues = config_issues + model_issues
    
    if all_issues:
        logger.warning("Configuration validation found %d issues:", len(all_issues))
        for issue_type, message in all_issues:
            logger.warning("  [%s] %s", issue_type, message)
        return False
    else:
        logger.info("All configuration validations passed")
        return True