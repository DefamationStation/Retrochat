# Retrochat

## Overview
Retrochat is a simple and lightweight chatbox application that leverages your local [llama.cpp](https://github.com/ggerganov/llama.cpp) server. This app is designed for easy configuration and seamless communication through a classic chat interface.

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
![Retrochat Screenshot 1](https://github.com/DefamationStation/Retrochat/assets/82258900/8cfc0087-aa33-4e58-9903-0abe049387da)
![Retrochat Screenshot 2](https://github.com/DefamationStation/Retrochat/assets/82258900/1ada054d-de2f-4f6d-9eb4-a0a34f3214da)
![Retrochat Screenshot 3](https://github.com/DefamationStation/Retrochat/assets/82258900/f9f9cfa9-e81e-4d3a-963a-6e7eeb3f90d9)
![Retrochat in Action](https://github.com/DefamationStation/Retrochat/assets/82258900/0e0b9b75-3c21-4c94-83ae-e22a0e34fe84)

## Usage Tips
- The chatbox can be resized by clicking and dragging near the edges of the app at the bottom right corner.

## Contribution
Contributions are welcome! Feel free to fork the project, make changes, and submit a pull request.

---
