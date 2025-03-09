# Flow.Launcher.Plugin.OpenRouter

A Flow Launcher plugin that allows you to query OpenRouter AI models directly from Flow Launcher.

## Features

- Ask questions to AI models directly from Flow Launcher
- Support for all models available on OpenRouter
- Set your preferred default model
- Results are automatically copied to clipboard
- Easy configuration with simple commands

## Installation

### From Flow Launcher

1. Open Flow Launcher
2. Type `pm install OpenRouter AI`
3. Press Enter to install the plugin

### Manual Installation

1. Download the latest release from the [Releases page](https://github.com/yourusername/Flow.Launcher.Plugin.OpenRouter/releases)
2. Extract the zip file to `%APPDATA%\FlowLauncher\Plugins`
3. Restart Flow Launcher

## Usage

The default action keyword is `ortr`. Here's how to use the plugin:

### Setting up

1. Get your API key from [OpenRouter](https://openrouter.ai/keys)
2. Set your API key with:
   ```
   ortr setkey YOUR_API_KEY
   ```

### Commands

- `ortr` - Show welcome screen with available commands
- `ortr setkey YOUR_API_KEY` - Set your OpenRouter API key
- `ortr models` - List available models
- `ortr setmodel MODEL_ID` - Set your preferred model (e.g., `ortr setmodel openai/gpt-4o`)
- `ortr your question here` - Ask a question to the AI

### Example Usage

- `ortr What is the capital of France?`
- `ortr Explain quantum computing in simple terms`
- `ortr How do I create a Flow Launcher plugin?`

## Development

### Requirements

- Python 3.7+
- Flow Launcher
- Required Python packages: flowlauncher, requests, pyperclip

### Setup for Development

1. Clone the repository
2. Install the required packages: `pip install -r requirements.txt`
3. Copy the project to Flow Launcher plugins directory or create a symbolic link

### Building

The plugin is built and packaged automatically via GitHub Actions when changes are pushed to the main branch.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Flow Launcher](https://github.com/Flow-Launcher/Flow.Launcher)
- [OpenRouter](https://openrouter.ai/)