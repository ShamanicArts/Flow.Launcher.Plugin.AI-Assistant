# Flow.Launcher.Plugin.ai
A Flow Launcher plugin that connects to OpenRouter AI models, allowing you to quickly query AI models directly from your launcher.

## Features
- Query AI models directly from Flow Launcher
- Uses delimiter-based command pattern (`||`) to trigger queries
- API key can be set via environment variable for security
- Results can be copied to clipboard or opened in Notepad
- Supports multiple AI models through OpenRouter

## Installation
### Method 1: Via Flow Launcher
1. Open Flow Launcher
2. Type the following command:
   ```
   pm install AI Assistant
   ```
3. Press Enter to install

### Method 2: Plugin Store
1. Open Flow Launcher Settings
2. Navigate to the "Plugin Store" tab
3. Search for "AI Assistant"
4. Click "Install"

### Method 3: Manual Installation
1. Download the latest release from the [Releases page](https://github.com/yourusername/Flow.Launcher.Plugin.ai/releases)
2. Extract the zip file to `%APPDATA%\FlowLauncher\Plugins`
3. Restart Flow Launcher

## Configuration
### Setting the API Key
For security, your OpenRouter API key should be set as an environment variable:
1. Create an environment variable named `OPENROUTER_API_KEY` with your API key from [OpenRouter](https://openrouter.ai/keys)
2. Restart Flow Launcher to apply the changes

### Settings
The plugin supports the following settings:
- `default_model`: The AI model to use (default: "deepseek/deepseek-chat:free")
- `delimiter`: Symbol that indicates when to send a prompt (default: "||")

## Usage
### Entering a Prompt
1. Type `ai` followed by your question and the delimiter:
   ```
   ai What is quantum computing? ||
   ```

### Receiving Results
2. The plugin will display the AI's response with two options:
   - **AI Response**: Click to copy the full response to clipboard
   - **Open in Notepad**: Click to open the response in Notepad for viewing or editing

### Example Queries
- `ai Explain the theory of relativity in simple terms ||`
- `ai Write a short Python script to calculate Fibonacci numbers ||`
- `ai What's the capital of France? ||`

## Troubleshooting
- **API Key not set**: Make sure the `OPENROUTER_API_KEY` environment variable is set correctly
- **No response**: Ensure you're adding the delimiter (`||`) at the end of your query
- **Models not loading**: Check your internet connection and API key validity

## Development
### Requirements
- Flow Launcher

### Building
The plugin is built and packaged automatically via GitHub Actions when changes are pushed to the main branch.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements
- [Flow Launcher](https://github.com/Flow-Launcher/Flow.Launcher)
- [OpenRouter](https://openrouter.ai/)
