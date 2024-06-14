# Retrochat

## Overview

Retrochat is a simple and lightweight chatbox application running a **single .py** that leverages your local [llama.cpp](https://github.com/ggerganov/llama.cpp), [Kobolt.cpp](https://github.com/LostRuins/koboldcpp) or [https://ollama.com](Ollama)  server.  This app is designed for easy configuration and seamless communication through a classic chat interface.

![image](https://github.com/DefamationStation/Retrochat/assets/82258900/e3609f2f-779d-4609-b60e-450ced1ca64f)

**Please note:** Llama.cpp or any sort of inference isn't included with this app, you will need to run your own server.

## Features
- **Local Server Integration**: Easily connect to your local llama.cpp server.
- **Resizable Interface**: Adjust the chatbox size by clicking and dragging near the bottom right corner.
- **Simple Configuration**: Modify settings on-the-fly using straightforward commands or by editing the `config.json` file.

## Getting Started
### Installation
1. **Python Script**:
   - Download the `Retrochat.py` file.
   - Install the required dependencies.
   - Run the script:
     ```bash
     python Retrochat.py
     ```
2. **Executable**:
   - Download the `.exe` file.
   - Run the executable directly from any location.

Available Commands and Arguments
Commands
/config - Update or retrieve configuration settings.

Usage: /config <key> <value>
Available Keys:
fontsize: Set the font size.
baseurl: Set the base URL for API requests.
openaiapikey: Set the OpenAI API key.
umc: Set the color of user messages.
amc: Set the color of assistant messages.
system_prompt: Set a custom system prompt.
/chat - Manage chat sessions.

Usage: /chat <action> <filename> [new_name]
Available Actions:
new <filename>: Create a new chat file and switch to it.
save <filename>: Save the current chat history to a specified file.
delete <filename>: Delete a specified chat file.
reset: Clear the current chat history.
rename <old_filename> <new_filename>: Rename a chat file.
open <filename>: Open an existing chat file.
list: List all JSON chat files in the current directory.
/models - List available models from Ollama or OpenAI.

Usage: /models
/selectmodel - Select a model for the current mode.

Usage: /selectmodel <model_name>
/resetmodel - Switch between available modes (llama.cpp, ollama, openai).

Usage: /resetmodel
/help - Display help message with available commands and their usage.

Usage: /help
/system_prompt - Set a custom system prompt for the chat session.

Usage: /system_prompt <prompt_message>
Arguments
<key>: The configuration setting to update or retrieve.
<value>: The new value for the configuration setting.
<action>: The action to perform on chat files (new, save, delete, reset, rename, open, list).
<filename>: The name of the chat file to act upon.
[new_name]: The new name for the chat file in the rename action.
<model_name>: The name of the model to select.
<prompt_message>: The custom system prompt message.
## Resources
- **Detailed Commands and Documentation**: For a comprehensive list of commands and usage details, visit the [Retrochat Wiki](https://github.com/DefamationStation/Retrochat/wiki).
- **Join Our Community**: Connect with other users and developers on our [Discord](https://discord.gg/dZxjYNyNth).

## Screenshots
![image](https://github.com/DefamationStation/Retrochat/assets/82258900/6f5585c6-2e71-4be9-927c-33b11f92f600)
![image](https://github.com/DefamationStation/Retrochat/assets/82258900/cd8f057d-943e-4e11-ab1b-8a227e969aee)
![Retrochat in Action](https://github.com/DefamationStation/Retrochat/assets/82258900/0e0b9b75-3c21-4c94-83ae-e22a0e34fe84)

## Usage Tips
- The chatbox can be resized by clicking and dragging near the edges of the app at the bottom right corner.

## Contribution
Contributions are welcome! Feel free to fork the project, make changes, and submit a pull request.

---
