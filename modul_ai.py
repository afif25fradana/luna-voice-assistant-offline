"""
This module provides the core AI functionalities for the Luna Voice Assistant,
including intent detection, interaction with Ollama, command execution,
and chat memory management.
"""
import json
import logging
import re
import subprocess
import threading
import urllib.parse

import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

# Using a generic client for Ollama's OpenAI-compatible API
# This avoids confusion with the 'openai' library being used for OpenAI's official API.
from openai import OpenAI as OllamaClient

from config import Config
from interpreter import interpreter
from modul_helper import run_shortcut
from modul_memory import ChatMemory
from personal_shortcuts import PERSONAL_SHORTCUTS

# Initialize chat memory
chat_memory = ChatMemory(memory_file=str(Config.MEMORY_FILE), max_memory_size=Config.MAX_MEMORY_SIZE)

# --- Interpreter Configuration ---
# Configure LLM interpreter
try:
    # For open-interpreter 0.2.1, configure LLM via an OpenAI client instance
    interpreter.llm = OllamaClient(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )
except Exception as err:
    logging.warning("Could not configure LLM: %s", err)

interpreter.auto_run = Config.INTERPRETER_AUTO_RUN

# Pre-compile regex patterns for filtering responses
_FILTER_PATTERNS = [
    re.compile(r'### Instruction:.+', re.DOTALL | re.IGNORECASE),
    re.compile(r'---\n*.+', re.DOTALL | re.IGNORECASE),
    re.compile(r'## New Constraints:.+', re.DOTALL | re.IGNORECASE),
    re.compile(r'Your response should include.+', re.DOTALL | re.IGNORECASE),
    re.compile(r'Respond with ONLY.+', re.DOTALL | re.IGNORECASE),
    re.compile(r'Increase Diff\d+ complexity by.+', re.DOTALL | re.IGNORECASE),
    re.compile(r'Format the response as JSON.+', re.DOTALL | re.IGNORECASE),
    re.compile(r'Add at least \d+ more constraints.+', re.DOTALL | re.IGNORECASE)
]

def _filter_response(text):
    """Remove any instruction-like content from responses"""
    for pattern in _FILTER_PATTERNS:
        text = pattern.sub('', text)
    return text.strip()

# --- Non-Blocking Warm-up Function ---
def warm_up_ollama():
    """
    Sends a silent, non-blocking request to load the Ollama model into memory.
    This prevents timeouts on the user's first request without freezing the GUI.
    """
    def task():
        logging.info("Starting Ollama model warm-up...")
        try:
            payload = {
                "model": Config.MODEL_NAME,
                "prompt": "Hello!", # Lightweight prompt just to trigger loading
                "stream": False
            }
            # Longer timeout specifically for warm-up
            with requests.post(Config.OLLAMA_ENDPOINT, json=payload, timeout=120) as response:
                response.raise_for_status()
            logging.info("Ollama model loaded and ready.")
        except (ConnectionError, Timeout) as err:
            logging.error("Failed to warm up model (connection/timeout error): %s", err)
            logging.warning("Application will continue, but the first request might be slow.")
        except RequestException as err:
            logging.error("Failed to warm up model (general request error): %s", err)
            logging.warning("Application will continue, but the first request might be slow.")

    threading.Thread(target=task, daemon=True).start()

# --- Smart Router Function ---
def get_intent(prompt_text: str) -> dict:
    """
    Uses the LLM to classify the user's intent and generate a structured response.
    Returns a dictionary like {"action": "chat"} or {"action": "execute", "command": "..."}.
    """
    # Dynamically generate shortcut examples for the prompt
    shortcut_examples = []
    # Include a few examples of each type of shortcut
    example_keys = [
        "ytm: hyperpop",
        "ytm search: {query}",
        "aur search: {pkg}",
        "arch wiki search: {term}",
        "youtube music home",
        "github afif"
    ]
    
    for key in example_keys:
        cmd_template = PERSONAL_SHORTCUTS.get(key, "")
        if '{query}' in cmd_template:
            example_query_phrase = key.replace('{query}', 'python')
            shortcut_examples.append(f"- '{key}' (e.g., 'cari {example_query_phrase}')")
        elif '{pkg}' in cmd_template:
            example_pkg_phrase = key.replace('{pkg}', 'nvm')
            shortcut_examples.append(f"- '{key}' (e.g., 'cari {example_pkg_phrase}')")
        elif '{term}' in cmd_template:
            example_term_phrase = key.replace('{term}', 'tutorial')
            shortcut_examples.append(f"- '{key}' (e.g., 'cari {example_term_phrase}')")
        else:
            shortcut_examples.append(f"- '{key}'")
    
    shortcut_list_str = "\n".join(shortcut_examples)

    router_prompt = f"""
    Analyze the user's request below. Classify the intent as one of the following: 'chat', 'open_url', 'search_google', 'open_shortcut'.
    Respond ONLY with a JSON object.

    If the intent is 'chat':
    ```json
    {{"action": "chat"}}
    ```

    If the intent is 'open_url':
    ```json
    {{"action": "open_url", "url": "[full URL, e.g., https://www.youtube.com or file:///path/to/file.txt or application name like 'firefox']"}}
    ```
    IMPORTANT:
    - For common websites (e.g., "youtube", "github", "facebook", "twitter"), ALWAYS convert to a full URL (e.g., "https://www.youtube.com", "https://github.com").
    - For local applications (e.g., "firefox", "calculator"), use the application name directly.
    - For local files, use the format `file:///path/to/file.txt`.
    Examples:
    - "open youtube" -> {{"action": "open_url", "url": "https://www.youtube.com"}}
    - "open github" -> {{"action": "open_url", "url": "https://github.com"}}
    - "open firefox" -> {{"action": "open_url", "url": "firefox"}}
    - "open file.txt" -> {{"action": "open_url", "url": "file:///home/user/documents/file.txt"}}

    If the intent is 'search_google':
    ```json
    {{"action": "search_google", "query": "[search term]"}}
    ```
    Example: "search python tutorial" -> {{"action": "search_google", "query": "python tutorial"}}

    If the intent is 'open_shortcut':
    ```json
    {{"action": "open_shortcut", "key": "[most relevant shortcut key from the list below]", "params": {{ "[param_name]": "[param_value]" }}}}
    ```
    IMPORTANT:
    - Choose the MOST SUITABLE `key` from the `PERSONAL_SHORTCUTS` list below, even if the user's request is phrased naturally and not an exact match to the shortcut key.
    - If there are parameters like `{{query}}`, `{{pkg}}`, or `{{term}}` in the chosen shortcut key, extract their values from the user's request and put them into `params`.

    Available `PERSONAL_SHORTCUTS` keys (partial list for examples):
    {shortcut_list_str}

    Examples of `open_shortcut` based on `PERSONAL_SHORTCUTS` and natural requests:
    - Request: "please open youtube music hyperpop"
      Output: {{"action": "open_shortcut", "key": "ytm: hyperpop", "params": {{}}}}
    - Request: "can you search for ado live on youtube music?"
      Output: {{"action": "open_shortcut", "key": "ytm search: {{{{query}}}}", "params": {{"query": "Ado live"}}}}
    - Request: "I want to see arch wiki about nvidia"
      Output: {{"action": "open_shortcut", "key": "arch wiki nvidia", "params": {{}}}}
    - Request: "open my github"
      Output: {{"action": "open_shortcut", "key": "github afif", "params": {{}}}}
    - Request: "search for nvm package on aur"
      Output: {{"action": "open_shortcut", "key": "aur search: {{pkg}}", "params": {{"pkg": "nvm"}}}}
    - Request: "open youtube music home page"
      Output: {{"action": "open_shortcut", "key": "youtube music home", "params": {{}}}}
    - Request: "open youtube"
      Output: {{"action": "open_url", "url": "https://www.youtube.com"}}
    - Request: "open youtube and play something"
      Output: {{"action": "open_url", "url": "https://www.youtube.com"}}

    User request: "{prompt_text}"
    """
    logging.info("Analyzing user intent with LLM...")
    try:
        payload = {
            "model": Config.MODEL_NAME,
            "prompt": router_prompt,
            "stream": False,
            "options": {"temperature": 0.0}  # Force deterministic output
        }
        with requests.post(Config.OLLAMA_ENDPOINT, json=payload, timeout=120) as response:
            response.raise_for_status()

            full_response_text = response.json().get("response", "").strip()
            logging.info("LLM raw response: %s", full_response_text)

            # Attempt to parse as JSON
            try:
                # Remove markdown code block fences if present
                if full_response_text.startswith("```json") and full_response_text.endswith("```"):
                    json_str = full_response_text[len("```json"):-len("```")].strip()
                else:
                    json_str = full_response_text
                
                parsed_response = json.loads(json_str)
                
                action = parsed_response.get("action")
                
                if action == "chat":
                    logging.info("Intent detected: CHAT")
                    return {"action": "chat"}
                if action == "open_url" and "url" in parsed_response:
                    logging.info("Intent detected: OPEN_URL. URL: '%s'", parsed_response['url'])
                    return {"action": "open_url", "url": parsed_response["url"]}
                if action == "search_google" and "query" in parsed_response:
                    logging.info("Intent detected: SEARCH_GOOGLE. Query: '%s'", parsed_response['query'])
                    return {"action": "search_google", "query": parsed_response["query"]}
                if action == "open_shortcut" and "key" in parsed_response:
                    params = parsed_response.get("params", {})
                    logging.info("Intent detected: OPEN_SHORTCUT. Key: '%s', Params: %s", parsed_response['key'], params)
                    return {"action": "open_shortcut", "key": parsed_response["key"], "params": params}
                
                logging.warning("Invalid JSON structure or unknown action from LLM: %s. Defaulting to chat.", parsed_response)
                return {"action": "chat"} # Default to chat on JSON decode error

            except json.JSONDecodeError:
                logging.warning("LLM response was not valid JSON. Raw: '%s'. Falling back to chat.", full_response_text)
                return {"action": "chat"} # Default to chat on JSON decode error

    except (ConnectionError, Timeout) as err:
        logging.error("Error: Failed to classify intent (connection/timeout error): %s", err)
        return {"action": "chat"} # Default to chat on error
    except RequestException as err:
        logging.error("Error: Failed to classify intent (general request error): %s", err)
        return {"action": "chat"} # Default to chat on error


# --- Direct Command Execution Function ---
def execute_command_directly(intent_data: dict):
    """Executes a command based on the detected intent."""
    logging.info("Executing action based on intent: %s", intent_data)

    # 1. Security Feature: Blacklist Dangerous Commands (from config)
    blacklist = Config.SECURITY_COMMAND_BLACKLIST
    
    action = intent_data.get("action")

    if action == "open_url":
        url = intent_data.get("url")
        if url:
            # Check if it's a local application/file or a web URL
            command_string = f"xdg-open '{url}'" if url.startswith(("http://", "https://", "file:///")) else url

            if any(cmd in command_string.lower() for cmd in blacklist):
                yield "⚠️ This action is restricted for security reasons."
                return
            try:
                subprocess.Popen(command_string, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("Command '%s' launched successfully in the background.", command_string)
                yield "Okay, I opened it."
            except FileNotFoundError:
                yield f"**Error:** Command '{command_string.split()[0]}' not found. Please ensure it's installed and in your system's PATH."
            except subprocess.CalledProcessError as err:
                yield f"**Error executing command:**\n{err}"
            except Exception as err:
                yield f"**An unexpected error occurred during URL/application opening:**\n{err}"
        else:
            yield "Error: No URL provided for open_url action."
    
    elif action == "search_google":
        query = intent_data.get("query")
        if query:
            encoded_query = urllib.parse.quote(query)
            command_string = f"xdg-open 'https://www.google.com/search?q={encoded_query}'"
            if any(cmd in command_string.lower() for cmd in blacklist):
                yield "⚠️ This action is restricted for security reasons."
                return
            try:
                subprocess.Popen(command_string, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("Command '%s' launched successfully in the background.", command_string)
                yield "Okay, I searched for it."
            except FileNotFoundError:
                yield "**Error:** Command 'xdg-open' not found. Please ensure it's installed and in your system's PATH."
            except subprocess.CalledProcessError as err:
                yield f"**Error executing command:**\n{err}"
            except Exception as err:
                yield f"**An unexpected error occurred during Google search:**\n{err}"
        else:
            yield "Error: No query provided for search_google action."

    elif action == "open_shortcut":
        command_key = intent_data.get("key")
        params = intent_data.get("params", {})
        if command_key:
            try:
                executed_cmd = run_shortcut(command_key, **params)
                logging.info("Shortcut '%s' executed: %s", command_key, executed_cmd)
                yield "Okay, I opened it."
            except ValueError as err:
                yield f"Error: {err}"
            except FileNotFoundError as err:
                yield f"**Error:** {err}"
            except subprocess.CalledProcessError as err:
                yield f"**Error executing shortcut command:**\n{err}"
            except Exception as err:
                yield f"**An unexpected error occurred during shortcut execution:**\n{err}"
        else:
            yield "Error: No shortcut key provided for open_shortcut action."
    
    else:
        # Fallback for direct CLI commands if LLM still outputs them directly
        # This case should ideally be handled by 'open_url' or 'open_shortcut'
        command_string = intent_data.get("command") # Assuming 'command' key for direct CLI
        if command_string:
            if any(cmd in command_string.lower() for cmd in blacklist):
                yield "⚠️ This action is restricted for security reasons."
                return
            try:
                subprocess.Popen(command_string, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("Command '%s' launched successfully in the background.", command_string)
                yield "Okay, I executed that command."
            except FileNotFoundError:
                yield f"**Error:** Command '{command_string.split()[0]}' not found. Please ensure it's installed and in your system's PATH."
            except subprocess.CalledProcessError as err:
                yield f"**Error executing command:**\n{err}"
            except Exception as err:
                yield f"**An unexpected error occurred during command execution:**\n{err}"
        else:
            yield "Error: Unknown action or missing command in intent data."


# --- Chat Function with Response Filtering ---
def ask_ollama_chat(prompt_text):
    """Sends a chat prompt to Ollama and yields the filtered response."""
    logging.info("Thinking (streaming) with model %s...", Config.MODEL_NAME)
    
    chat_memory.add_message("user", prompt_text)

    history = chat_memory.get_history()
    messages = [f"{msg['role']}: {msg['content']}" for msg in history]
    
    full_prompt_with_history = "\n".join(messages) + f"\nuser: {prompt_text}"

    try:
        payload = {
            "model": Config.MODEL_NAME,
            "prompt": full_prompt_with_history,
            "stream": True
        }
        full_raw_response = ""
        
        with requests.post(Config.OLLAMA_ENDPOINT, json=payload, stream=True, timeout=180) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    full_raw_response += token
                    yield token
                    if chunk.get("done"):
                        break
        
        filtered_response_for_memory = _filter_response(full_raw_response)
        if not filtered_response_for_memory:
            filtered_response_for_memory = "I'm sorry, I encountered an issue with that response or it was filtered. Could you ask something else?"
        
        logging.info("Final AI response (filtered for memory): '%s'", filtered_response_for_memory)
        
        chat_memory.add_message("assistant", filtered_response_for_memory)
            
    except (ConnectionError, Timeout) as err:
        logging.error("Error: Failed to connect to Ollama (connection/timeout error): %s", err)
        yield f"Error: Failed to connect to Ollama. {err}"
    except RequestException as err:
        logging.error("Error: Failed to connect to Ollama (general request error): %s", err)
        yield f"Error: Failed to connect to Ollama. {err}"

# --- Entry Point Function ---
def ask_ollama(prompt_text):
    """
    Main entry point for asking Ollama.
    Routes the request based on detected intent.
    """
    intent_data = get_intent(prompt_text)
    if intent_data["action"] == "chat":
        yield from ask_ollama_chat(prompt_text)
    else:
        yield from execute_command_directly(intent_data)
