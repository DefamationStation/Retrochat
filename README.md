# Retrochat

## Overview

Retrochat is a simple and lightweight chatbox application running a **single .py** that leverages your local [llama.cpp](https://github.com/ggerganov/llama.cpp),[Kobolt.cpp](https://github.com/LostRuins/koboldcpp) or [https://ollama.com/](Ollama)  server.  This app is designed for easy configuration and seamless communication through a classic chat interface.

![image](https://github.com/DefamationStation/Retrochat/assets/82258900/e3609f2f-779d-4609-b60e-450ced1ca64f)

**Please note:** Llama.cpp or any sort of inference isn't included with this app, you will need to run your own server.

## Development
This application is being actively developed using [Aider](https://aider.chat/),

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

### Configuration
- To set or change the `llama.cpp` endpoint server, type:
  ```bash
  /config host your_host_ip:port
  ```
- Any parameter in the `config.json` file can be modified similarly using the `/config` command followed by the parameter name and its new value.

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
