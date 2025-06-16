import sys
import os
from pathlib import Path
import glob # New import

# Add lib directory to path for external modules
plugindir = Path.absolute(Path(__file__).parent)
paths = (".", "lib", "plugin")
sys.path = [str(plugindir / p) for p in paths] + sys.path

import json
import webbrowser
import tempfile
import subprocess
import requests
from pyflowlauncher import Plugin, Result, send_results
from pyflowlauncher.result import ResultResponse
from pyflowlauncher.settings import settings
from flowlauncher.FlowLauncherAPI import FlowLauncherAPI

DEFAULT_MODEL = "deepseek/deepseek-chat:free"
DEFAULT_DELIMITER = "||"

# New constants for system prompts
PROMPTS_DIR = plugindir / "prompts"
DEFAULT_SYSTEM_PROMPT_FILE = "default.txt"

# Flag to force settings API key test - set to True when testing
FORCE_SETTINGS_API_KEY = False

# Cache for settings to handle inconsistent settings() behavior
_settings_cache = {}

def get_env_api_key():
    """
    Get the API key from environment variable, respecting the test flag.
    When FORCE_SETTINGS_API_KEY is True, this will return None as if no env var exists.
    """
    if FORCE_SETTINGS_API_KEY:
        return None
    return os.environ.get("OPENROUTER_API_KEY")

def get_settings(key=None, default=None):
    """
    Get settings with environment variable priority for API key.
    """
    global _settings_cache
    
    # Try to get current settings
    current_settings = settings()
    
    # If settings is available, update cache
    if current_settings is not None:
        _settings_cache.update(current_settings)
    
    # Special case for API key - prioritize environment variable
    if key == "api_key":
        env_api_key = get_env_api_key()
        if env_api_key:
            return env_api_key
    
    # If a specific key is requested
    if key is not None:
        return _settings_cache.get(key, default)
    
    # Return all settings
    return _settings_cache


# Run at module load to initialize settings
try:
    settings_obj = settings()
    if settings_obj is not None:
        _settings_cache.update(settings_obj)
except Exception:
    pass


plugin = Plugin()

def flow_show_msg(title: str, sub_title: str, ico_path: str = ""):
    """Helper to create a JsonRPCAction for Flow.Launcher.ShowMsg."""
    return {
        "method": "Flow.Launcher.ShowMsg",
        "parameters": [title, sub_title, ico_path]
    }

def get_prompt_files():
    """Lists all .txt files in the prompts directory."""
    if not PROMPTS_DIR.exists():
        PROMPTS_DIR.mkdir(exist_ok=True)
    return [f.name for f in PROMPTS_DIR.glob("*.txt") if f.is_file()]

def read_prompt_file(filename: str) -> str:
    """Reads the content of a specified prompt file."""
    file_path = PROMPTS_DIR / filename
    if file_path.is_file():
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "" # Return empty string if file not found

@plugin.on_method
def get_system_prompt_options() -> list[str]:
    """Returns a list of available system prompt files for the settings dropdown."""
    prompt_files = get_prompt_files()
    # Ensure default.txt is always an option if it exists
    if DEFAULT_SYSTEM_PROMPT_FILE not in prompt_files:
        prompt_files.insert(0, DEFAULT_SYSTEM_PROMPT_FILE)
    return prompt_files

@plugin.on_method
def query(query: str) -> ResultResponse:
    """Main entry point for the plugin."""
    # Get settings using our cache mechanism
    api_key = get_settings("api_key", "")
    default_model = get_settings("default_model", DEFAULT_MODEL)
    editor_path = get_settings("editor_path", "notepad.exe")
    delimiter = get_settings("delimiter", DEFAULT_DELIMITER)
    system_prompt_file = get_settings("system_prompt_file", DEFAULT_SYSTEM_PROMPT_FILE)
    system_prompt_content = read_prompt_file(system_prompt_file)
    
    if not query.strip():
        return send_results([
            Result(
                Title="AI Assistant",
                SubTitle=f"Type a question followed by {delimiter} to ask {default_model}",
                IcoPath="Images/app.png"
            )
        ])
    
    # Execute only if delimiter is present
    if delimiter in query:
        query = query.split(delimiter, 1)[0].strip()
        
        if not api_key:
            return send_results([
                Result(
                    Title="API Key not set",
                    SubTitle="Set OPENROUTER_API_KEY environment variable",
                    IcoPath="Images/app.png"
                )
            ])
        
        # Make the API call
        try:
            messages = []
            if system_prompt_content:
                messages.append({"role": "system", "content": system_prompt_content})
            messages.append({"role": "user", "content": query})

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "flow-launcher-plugin",
                    "X-Title": "AI Assistant Flow Launcher Plugin"
                },
                json={
                    "model": default_model,
                    "messages": messages
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                
                # Show result with actions
                preview = answer[:100] + "..." if len(answer) > 100 else answer
                return send_results([
                    Result(
                        Title="AI Response",
                        SubTitle=preview,
                        IcoPath="Images/app.png",
                        JsonRPCAction={
                            "method": "copy_to_clipboard",
                            "parameters": [answer]
                        },
                        ContextData=answer
                    ),
                    Result(
                        Title="Open in Editor",
                        SubTitle="Open the full response in your preferred editor",
                        IcoPath="Images/app.png",
                        JsonRPCAction={
                            "method": "open_in_editor",
                            "parameters": [answer,  editor_path]
                        }
                    )
                ])
            else:
                error_data = response.json().get("error", {})
                error_message = error_data.get("message", "Unknown error")
                return send_results([
                    Result(
                        Title=f"Error: {response.status_code}",
                        SubTitle=error_message,
                        IcoPath="Images/app.png"
                    )
                ])
        except Exception as e:
            return send_results([
                Result(
                    Title="Error",
                    SubTitle=str(e),
                    IcoPath="Images/app.png"
                )
            ])
    
    # Just preview when typing, no Enter execution
    return send_results([
        Result(
            Title=f"Ask AI: {query}",
            SubTitle=f"Add '{delimiter}' to send to {default_model}",
            IcoPath="Images/app.png"
        )
    ])


@plugin.on_method
def copy_to_clipboard(text: str) -> ResultResponse:
    """Copy text to clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        
        return send_results([
            Result(
                Title="Copied to clipboard",
                SubTitle=text[:100] + "..." if len(text) > 100 else text,
                IcoPath="Images/app.png"
            )
        ])
    except ImportError:
        return send_results([
            Result(
                Title="Error: Could not copy to clipboard",
                SubTitle="The pyperclip module is not installed properly",
                IcoPath="Images/app.png"
            )
        ])


@plugin.on_method
def open_in_editor(text: str, editor_path: str) -> None:
    """Open text in the user's configured editor."""

    # Step 3: Check if the editor_path was actually found and is not empty.
    if not editor_path or editor_path == "notepad.exe":
        # If the setting is missing, empty, or still the default, show an error message.
        # This uses Flow Launcher's own message box API.
        FlowLauncherAPI.show_msg(
            "Editor Not Configured",
            f"Your custom editor path is not set correctly. The plugin received: '{editor_path}'. Please check the plugin settings.",
            "Images/app.png"
        )
        return # Stop execution here.

    # Step 4: If we get here, it means a custom editor path WAS found. Try to use it.
    try:
        # Create a temporary file with the text content
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="ai_response_")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Open the file with the user's specified editor
        subprocess.Popen([editor_path, path])
    except Exception as e:
        # If opening the editor fails (e.g., bad path), show a detailed error.
        FlowLauncherAPI.show_msg(
            "Error Opening Editor",
            f"Could not open the editor at '{editor_path}'. Please ensure the path is correct. Error: {e}",
            "Images/app.png"
        )





@plugin.on_method
def context_menu(data: str) -> ResultResponse:
    """Context menu for showing additional actions on results."""
    editor_path = get_settings("editor_path", "notepad.exe")
    return send_results([
        Result(
            Title="Copy to clipboard",
            SubTitle="Copy the full response to clipboard",
            IcoPath="Images/app.png",
            JsonRPCAction={
                "method": "copy_to_clipboard",
                "parameters": [data]
            }
        ),
        Result(
            Title="Open in Editor",
            SubTitle="Open the full response in your preferred editor for viewing/editing",
            IcoPath="Images/app.png",
            JsonRPCAction={
                "method": "open_in_editor",
                "parameters": [data, editor_path]
            }
        ),

    ])


if __name__ == "__main__":
    plugin.run()