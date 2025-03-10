import sys
import os
from pathlib import Path

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

DEFAULT_MODEL = "deepseek/deepseek-chat:free"
DEFAULT_DELIMITER = "||"

# Cache for settings to handle inconsistent settings() behavior
_settings_cache = {}

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
        env_api_key = os.environ.get("OPENROUTER_API_KEY")
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


@plugin.on_method
def query(query: str) -> ResultResponse:
    """Main entry point for the plugin."""
    # Get settings using our cache mechanism
    api_key = get_settings("api_key", "")
    default_model = get_settings("default_model", DEFAULT_MODEL)
    delimiter = get_settings("delimiter", DEFAULT_DELIMITER)
    
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
                    "messages": [
                        {"role": "user", "content": query}
                    ]
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
                        Title="Open in Notepad",
                        SubTitle="Open the full response in Notepad",
                        IcoPath="Images/app.png",
                        JsonRPCAction={
                            "method": "open_in_notepad",
                            "parameters": [answer]
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
def open_in_notepad(text: str) -> None:
    """Open text in notepad - properly implemented to actually open notepad."""
    try:
        # Create a temporary file with the text content
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="ai_response_")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Open the file with notepad using subprocess
        subprocess.Popen(["notepad.exe", path])
    except Exception as e:
        print(f"Error opening notepad: {e}")


@plugin.on_method
def context_menu(data: str) -> ResultResponse:
    """Context menu for showing additional actions on results."""
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
            Title="Open in Notepad",
            SubTitle="Open the full response in Notepad for viewing/editing",
            IcoPath="Images/app.png",
            JsonRPCAction={
                "method": "open_in_notepad",
                "parameters": [data]
            }
        )
    ])


if __name__ == "__main__":
    plugin.run()