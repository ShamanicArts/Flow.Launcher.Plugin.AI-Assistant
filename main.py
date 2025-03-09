import sys
from pathlib import Path

plugindir = Path.absolute(Path(__file__).parent)
paths = (".", "lib", "plugin")
sys.path = [str(plugindir / p) for p in paths] + sys.path

# Add lib directory to path for external modules
plugindir = Path.absolute(Path(__file__).parent)
paths = (".", "lib", "plugin")
sys.path = [str(plugindir / p) for p in paths] + sys.path

from flowlauncher import FlowLauncher

class OpenRouterPlugin(FlowLauncher):
    def __init__(self):
        super().__init__()
        self.api_key = self._load_api_key()
        self.default_model = "openai/gpt-3.5-turbo"
        self.models = self._load_models()

    def _load_api_key(self):
        """Load API key from settings file."""
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        try:
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    settings = json.load(f)
                    return settings.get("api_key", "")
            return ""
        except Exception:
            return ""

    def _save_api_key(self, api_key):
        """Save API key to settings file."""
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        try:
            settings = {}
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    settings = json.load(f)
            
            settings["api_key"] = api_key
            
            with open(settings_path, "w") as f:
                json.dump(settings, f)
            
            return True
        except Exception:
            return False

    def _load_models(self):
        """Load available models from OpenRouter."""
        try:
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
        
        # Check if it's a command
        if query.startswith("setkey "):
            _, api_key = query.split("setkey ", 1)
            success = self._save_api_key(api_key)
            if success:
                self.api_key = api_key
                return [{
                    "Title": "API Key saved successfully",
                    "SubTitle": "Your OpenRouter API key has been saved",
                    "IcoPath": "Images/app.png"
                }]
            else:
                return [{
                    "Title": "Failed to save API key",
                    "SubTitle": "There was an error saving your API key",
                    "IcoPath": "Images/app.png"
                }]
        
        if query.startswith("setmodel "):
            _, model = query.split("setmodel ", 1)
            if model in self.models:
                self.default_model = model
                return [{
                    "Title": f"Model set to {model}",
                    "SubTitle": "This model will be used for your queries",
                    "IcoPath": "Images/app.png"
                }]
            else:
                return [{
                    "Title": "Invalid model",
                    "SubTitle": "The specified model is not available",
                    "IcoPath": "Images/app.png"
                }]
        
        if query.startswith("models"):
            return self._list_models()
        
        # If not a command, treat as a question for the AI
        if not self.api_key:
            return [{
                "Title": "API Key not set",
                "SubTitle": "Use 'ortr setkey YOUR_API_KEY' to set your OpenRouter API key",
                "IcoPath": "Images/app.png"
            }]
        
        return [{
            "Title": f"Ask: {query}",
            "SubTitle": f"Press Enter to ask using {self.default_model}",
            "IcoPath": "Images/app.png",
            "JsonRPCAction": {
                "method": "ask_openrouter",
                "parameters": [query]
            }
        }]
    
    def _welcome_results(self):
        """Return welcome results when no query is provided."""
        results = [
            {
                "Title": "OpenRouter AI",
                "SubTitle": "Type a question to ask the AI",
                "IcoPath": "Images/app.png"
            }
        ]
        
        if not self.api_key:
            results.append({
                "Title": "Set API Key",
                "SubTitle": "Use 'ortr setkey YOUR_API_KEY' to set your OpenRouter API key",
                "IcoPath": "Images/app.png"
            })
        
        results.extend([
            {
                "Title": "List Models",
                "SubTitle": "Type 'ortr models' to see available models",
                "IcoPath": "Images/app.png"
            },
            {
                "Title": "Set Model",
                "SubTitle": "Use 'ortr setmodel MODEL_ID' to set your preferred model",
                "IcoPath": "Images/app.png"
            }
        ])
        
        return results
    
    def _list_models(self):
        """List available models from OpenRouter."""
        if not self.models:
            return [{
                "Title": "No models found",
                "SubTitle": "Failed to retrieve models from OpenRouter",
                "IcoPath": "Images/app.png"
            }]
        
        results = []
        for model in self.models:
            results.append({
                "Title": model,
                "SubTitle": f"Set as default model by typing 'ortr setmodel {model}'",
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "set_model",
                    "parameters": [model]
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
                    "X-Title": "OpenRouter Flow Launcher Plugin"
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
                    "IcoPath": "Images/app.png"
                }
            else:
                error_data = response.json().get("error", {})
                error_message = error_data.get("message", "Unknown error")
                return {
                    "Title": f"Error: {response.status_code}",
                    "SubTitle": error_message,
                    "IcoPath": "Images/app.png"
                }
        except Exception as e:
            return {
                "Title": "Error",
                "SubTitle": str(e),
                "IcoPath": "Images/app.png"
            }
    
    def set_model(self, model):
        """Set the default model."""
        self.default_model = model
        return {
            "Title": f"Model set to {model}",
            "SubTitle": "This model will be used for your queries",
            "IcoPath": "Images/app.png"
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
                "Title": "Visit OpenRouter website",
                "SubTitle": "Open OpenRouter in your browser",
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": ["https://openrouter.ai"]
                }
            }
        ]
    
    def open_url(self, url):
        """Open a URL in the default browser."""
        webbrowser.open(url)

if __name__ == "__main__":
    OpenRouterPlugin()