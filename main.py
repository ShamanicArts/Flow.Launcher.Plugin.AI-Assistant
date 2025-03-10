import sys
import os
from pathlib import Path

# Add lib directory to path for external modules
plugindir = Path.absolute(Path(__file__).parent)
paths = (".", "lib", "plugin")
sys.path = [str(plugindir / p) for p in paths] + sys.path

import json
import webbrowser
import requests
from flowlauncher import FlowLauncher

class AIPlugin(FlowLauncher):
    def __init__(self):
        # Initialize variables before calling super().__init__()
        self.api_key = ""
        self.default_model = "deepseek/deepseek-chat:free"
        self.models = []
        self.settings = {}
        
        # Now call the parent's __init__ which might call query()
        super().__init__()
        
        # Load settings after initialization
        self._load_settings()
        self.models = self._load_models()

    def _load_settings(self):
        """Load settings from settings.json file."""
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        try:
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    self.settings = json.load(f)
                    self.api_key = self.settings.get("api_key", "")
                    self.default_model = self.settings.get("default_model", "deepseek/deepseek-chat:free")
            else:
                # Create default settings
                self.settings = {
                    "api_key": "",
                    "default_model": "deepseek/deepseek-chat:free"
                }
                self._save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")

    def _save_settings(self):
        """Save settings to settings.json file."""
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        try:
            # Update settings dict with current values
            self.settings["api_key"] = self.api_key
            self.settings["default_model"] = self.default_model
            
            with open(settings_path, "w") as f:
                json.dump(self.settings, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def _load_models(self):
        """Load available models from OpenRouter."""
        try:
            if not self.api_key:
                return []
                
            response = requests.get("https://openrouter.ai/api/v1/models")
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            return []
        except Exception:
            return []

    def query(self, query):
        """Main entry point for the plugin."""
        if not query:
            return self._welcome_results()
        
        # Filter queries containing the '||' delimiter
        if '||' in query:
            query = query.split('||', 1)[0].strip()
            return self._ask_ai(query)
        
        # Show thinking indicator when user is typing
        return [{
            "Title": f"Ask AI: {query}",
            "SubTitle": f"Press Enter or add '||' to send to {self.default_model}",
            "IcoPath": "Images\\app.png",
            "JsonRPCAction": {
                "method": "ask_openrouter",
                "parameters": [query]
            }
        }]
    
    def _ask_ai(self, query):
        """Format a query for asking the AI."""
        if not self.api_key:
            return [{
                "Title": "API Key not set",
                "SubTitle": "Configure your OpenRouter API key in Flow Launcher settings",
                "IcoPath": "Images\\app.png",
                "JsonRPCAction": {
                    "method": "open_plugin_settings",
                    "parameters": []
                }
            }]
            
        return [{
            "Title": f"Asking: {query}",
            "SubTitle": f"Sending to {self.default_model}...",
            "IcoPath": "Images\\app.png",
            "JsonRPCAction": {
                "method": "ask_openrouter",
                "parameters": [query]
            }
        }]
    
    def _welcome_results(self):
        """Return welcome results when no query is provided."""
        results = [
            {
                "Title": "AI Assistant",
                "SubTitle": "Type a question followed by || to ask the AI",
                "IcoPath": "Images\\app.png"
            }
        ]
        
        if not self.api_key:
            results.append({
                "Title": "Configure API Key",
                "SubTitle": "Configure your OpenRouter API key in Flow Launcher settings",
                "IcoPath": "Images\\app.png",
                "JsonRPCAction": {
                    "method": "open_plugin_settings",
                    "parameters": []
                }
            })
        
        results.append({
            "Title": "Visit OpenRouter",
            "SubTitle": "Open OpenRouter website to get an API key",
            "IcoPath": "Images\\app.png",
            "JsonRPCAction": {
                "method": "open_url",
                "parameters": ["https://openrouter.ai/keys"]
            }
        })
        
        return results
    
    def ask_openrouter(self, query):
        """Ask a question to OpenRouter API."""
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "flow-launcher-plugin",
                    "X-Title": "AI Assistant Flow Launcher Plugin"
                },
                json={
                    "model": self.default_model,
                    "messages": [
                        {"role": "user", "content": query}
                    ]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                
                # Copy the answer to clipboard
                self._copy_to_clipboard(answer)
                
                return {
                    "Title": "Answer copied to clipboard",
                    "SubTitle": answer[:100] + "..." if len(answer) > 100 else answer,
                    "IcoPath": "Images\\app.png"
                }
            else:
                error_data = response.json().get("error", {})
                error_message = error_data.get("message", "Unknown error")
                return {
                    "Title": f"Error: {response.status_code}",
                    "SubTitle": error_message,
                    "IcoPath": "Images\\app.png"
                }
        except Exception as e:
            return {
                "Title": "Error",
                "SubTitle": str(e),
                "IcoPath": "Images\\app.png"
            }
    
    def open_plugin_settings(self):
        """Open the Flow Launcher plugin settings for this plugin."""
        return {
            "Title": "Opening plugin settings",
            "SubTitle": "Configure your API key and model preferences",
            "IcoPath": "Images\\app.png"
        }
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except ImportError:
            return False
    
    def context_menu(self, data):
        """Context menu for results."""
        return [
            {
                "Title": "Configure Settings",
                "SubTitle": "Open plugin settings",
                "IcoPath": "Images\\app.png",
                "JsonRPCAction": {
                    "method": "open_plugin_settings",
                    "parameters": []
                }
            },
            {
                "Title": "Visit OpenRouter",
                "SubTitle": "Open OpenRouter website",
                "IcoPath": "Images\\app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": ["https://openrouter.ai"]
                }
            }
        ]
    
    def open_url(self, url):
        """Open a URL in the default browser."""
        webbrowser.open(url)

    # Plugin settings interface
    def get_plugin_settings_json(self):
        return {
            "api_key": {
                "displayName": "OpenRouter API Key",
                "description": "Your API key from openrouter.ai",
                "value": self.api_key,
                "type": "input",
                "inputType": "password"
            },
            "default_model": {
                "displayName": "Default AI Model",
                "description": "The AI model to use (e.g., deepseek/deepseek-chat:free)",
                "value": self.default_model,
                "type": "input"
            }
        }

    def set_plugin_settings(self, settings_json):
        try:
            settings = json.loads(settings_json)
            if "api_key" in settings:
                self.api_key = settings["api_key"]
            if "default_model" in settings:
                self.default_model = settings["default_model"]
            self._save_settings()
            
            # Reload models if API key is set
            if self.api_key:
                self.models = self._load_models()
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

if __name__ == "__main__":
    AIPlugin()