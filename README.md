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

# Retrochat Command Reference

## Available Commands and Arguments

### Configuration Commands

1. **/config**
   - **Description**: Update or retrieve configuration settings.
   - **Usage**: `/config <key> <value>`
   - **Available Keys**:
     - `fontsize`: Set the font size.
       - Example: `/config fontsize 18`
     - `baseurl`: Set the base URL for API requests.
       - Example: `/config baseurl http://new-url.com`
     - `openaiapikey`: Set the OpenAI API key.
       - Example: `/config openaiapikey YOUR_API_KEY`
     - `umc`: Set the color of user messages.
       - Example: `/config umc #00FF00`
     - `amc`: Set the color of assistant messages.
       - Example: `/config amc #FFBF00`
     - `system_prompt`: Set a custom system prompt.
       - Example: `/config system_prompt "Your prompt here"`

### Chat Management Commands

2. **/chat**
   - **Description**: Manage chat sessions.
   - **Usage**: `/chat <action> <filename> [new_name]`
   - **Available Actions**:
     - `new <filename>`: Create and switch to a new chat file.
       - Example: `/chat new my_chat.json`
     - `save <filename>`: Save the current chat history to a specified file.
       - Example: `/chat save my_chat_backup.json`
     - `delete <filename>`: Permanently delete a specified chat file.
       - Example: `/chat delete old_chat.json`
     - `reset`: Clear the current chat history.
       - Example: `/chat reset`
     - `rename <old_filename> <new_filename>`: Rename a chat file.
       - Example: `/chat rename chat_1.json new_chat_name.json`
     - `open <filename>`: Open and load an existing chat file.
       - Example: `/chat open my_chat.json`
     - `list`: List all JSON chat files in the current directory.
       - Example: `/chat list`

### Model Management Commands

3. **/models**
   - **Description**: List available models from Ollama or OpenAI (depending on the current mode).
   - **Usage**: `/models`

4. **/selectmodel**
   - **Description**: Select a model for the current mode.
   - **Usage**: `/selectmodel <model_name>`
   - **Example**: `/selectmodel gpt-4-turbo`

5. **/resetmodel**
   - **Description**: Switch between available modes (`llama.cpp`, `ollama`, `openai`).
   - **Usage**: `/resetmodel`

### Utility Commands

6. **/help**
   - **Description**: Display help message with available commands and their usage.
   - **Usage**: `/help`

7. **/system_prompt**
   - **Description**: Set a custom system prompt for the chat session.
   - **Usage**: `/system_prompt <prompt_message>`
   - **Example**: `/system_prompt "Your custom prompt message"`

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
