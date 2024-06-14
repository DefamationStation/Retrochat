import os
import sys
import json
import requests
import markdown
import shutil
import ctypes
from ctypes import windll, byref, c_int, sizeof
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QTextCursor, QFont, QIcon, QPixmap


def set_amoled_black_title_bar(window):
    if sys.platform == 'win32':
        hwnd = int(window.winId())

        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_BORDER_COLOR = 34
        DWMWA_CAPTION_COLOR = 35
        
        windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(c_int(1)), sizeof(c_int))
        
        black_color = 0x000000
        windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR, byref(c_int(black_color)), sizeof(c_int))
        windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, byref(c_int(black_color)), sizeof(c_int))


class ConfigManager:
    CONFIG_FILENAME = "config.json"
    DEFAULT_CONFIG = {
        "baseurl": "http://",
        "ollamahost": "127.0.0.1:11434",
        "llamacpphost": "127.0.0.1:8080",
        "path": "/v1/chat/completions",
        "umc": "#00FF00",
        "amc": "#FFBF00",
        "fontsize": 18,
        "current_chat_filename": "chat_1.json",
        "selected_model": "",
        "current_mode": "llama.cpp",
        "openaiapikey": ""
    }

    @classmethod
    def load_config(cls):
        config_path = os.path.join(os.getcwd(), cls.CONFIG_FILENAME)
        if not os.path.exists(config_path):
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                return cls.check_and_update_config(config)
        except (json.JSONDecodeError, Exception):
            cls.rename_old_file(cls.CONFIG_FILENAME)
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG

    @classmethod
    def save_config(cls, config):
        config_path = os.path.join(os.getcwd(), cls.CONFIG_FILENAME)
        with open(config_path, 'w') as config_file:
            json.dump(config, config_file, indent=4)

    @classmethod
    def save_config_value(cls, key, value):
        config = cls.load_config()
        config[key] = value
        cls.save_config(config)

    @classmethod
    def check_and_update_config(cls, config):
        if isinstance(config, dict):
            updated_config = cls.update_to_match_default(config, cls.DEFAULT_CONFIG)
            if updated_config != config:
                cls.save_config(updated_config)
            return updated_config
        else:
            cls.rename_old_file(cls.CONFIG_FILENAME)
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG

    @classmethod
    def update_to_match_default(cls, data, default_structure):
        if not isinstance(data, dict) or not isinstance(default_structure, dict):
            return default_structure

        updated_data = data.copy()
        for key, default_value in default_structure.items():
            if key not in updated_data:
                updated_data[key] = default_value
            elif isinstance(default_value, dict):
                updated_data[key] = cls.update_to_match_default(updated_data[key], default_value)
        return updated_data

    @staticmethod
    def rename_old_file(filename):
        old_file_path = os.path.join(os.getcwd(), filename)
        new_file_path = os.path.join(os.getcwd(), f"OLD_{filename}")
        if os.path.exists(old_file_path):
            shutil.move(old_file_path, new_file_path)

class ChatHistoryManager:
    def __init__(self, chat_filename="chat_1.json"):
        self.chat_filename = chat_filename

    def save_chat_history(self, chat_history, system_prompt):
        chat_data = {
            "system_prompt": system_prompt,
            "conversation_history": chat_history
        }
        chat_history_path = os.path.join(os.getcwd(), self.chat_filename)
        with open(chat_history_path, 'w') as file:
            json.dump(chat_data, file, indent=4)
        ConfigManager.save_config_value('current_chat_filename', self.chat_filename)

    def load_chat_history(self):
        chat_history_path = os.path.join(os.getcwd(), self.chat_filename)
        if os.path.exists(chat_history_path):
            try:
                with open(chat_history_path, 'r') as file:
                    chat_data = json.load(file)
                    if isinstance(chat_data, dict):
                        return chat_data.get("conversation_history", []), chat_data.get("system_prompt", "")
                    else:
                        raise json.JSONDecodeError("Invalid format", chat_history_path, 0)
            except json.JSONDecodeError:
                self.rename_old_file(self.chat_filename)
                self.create_new_chat_file()
                return [], ""
        return [], ""

    def check_and_update_json_file(self, filename, expected_structure):
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            if isinstance(data, dict):
                updated_data = self.update_json_structure(data, expected_structure)

                if updated_data != data:
                    with open(file_path, 'w') as file:
                        json.dump(updated_data, file, indent=4)
            else:
                raise json.JSONDecodeError("Invalid format", file_path, 0)

        except json.JSONDecodeError:
            self.rename_old_file(filename)
            self.create_new_file_with_structure(filename, expected_structure)

    def update_json_structure(self, data, expected_structure):
        if not isinstance(data, dict) or not isinstance(expected_structure, dict):
            return expected_structure

        updated_data = data.copy()
        for key, default_value in expected_structure.items():
            if key not in updated_data:
                updated_data[key] = default_value
            elif isinstance(default_value, dict):
                updated_data[key] = self.update_json_structure(updated_data[key], default_value)
        return updated_data

    def ensure_chat_files_are_up_to_date(self, expected_structure):
        json_files = [f for f in os.listdir(os.getcwd()) if f.endswith('.json') and f != ConfigManager.CONFIG_FILENAME]
        for file in json_files:
            self.check_and_update_json_file(file, expected_structure)

    def rename_old_file(self, filename):
        old_file_path = os.path.join(os.getcwd(), filename)
        new_file_path = os.path.join(os.getcwd(), f"OLD_{filename}")
        if os.path.exists(old_file_path):
            shutil.move(old_file_path, new_file_path)

    def create_new_file_with_structure(self, filename, structure):
        new_file_path = os.path.join(os.getcwd(), filename)
        with open(new_file_path, 'w') as file:
            json.dump(structure, file, indent=4)

    def create_new_chat_file(self):
        default_structure = {
            "system_prompt": "",
            "conversation_history": []
        }
        self.create_new_file_with_structure(self.chat_filename, default_structure)

    def set_chat_filename(self, filename):
        self.chat_filename = filename

    def get_next_available_filename(self):
        index = 1
        while True:
            filename = f"chat_{index}.json"
            if not os.path.exists(filename):
                return filename
            index += 1

class NetworkWorker(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversation_history, endpoint, data, headers=None):
        super().__init__()
        self.conversation_history = conversation_history
        self.endpoint = endpoint
        self.data = data
        self.headers = headers if headers else {"Content-Type": "application/json"}

    def run(self):
        try:
            response = requests.post(self.endpoint, headers=self.headers, json=self.data)
            if response.status_code == 200:
                bot_message = response.json()["choices"][0]["message"]["content"].strip()
                self.response_received.emit(bot_message)
            else:
                self.error_occurred.emit(f"{response.status_code} - {response.text}")
        except requests.RequestException as e:
            self.error_occurred.emit(str(e))

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager.load_config()
        self.chat_manager = ChatHistoryManager(chat_filename=self.config.get('current_chat_filename', 'chat_1.json'))
        self.fontsize = int(self.config.get("fontsize", 18))
        self.conversation_history, self.system_prompt = self.chat_manager.load_chat_history()
        self.command_history = []
        self.command_index = -1
        self.is_moving = False
        self.startPos = QPoint(0, 0)
        self.help_message_displayed = False
        self.resizing = False
        self.resize_direction = None
        self.oldPos = QPoint(0, 0)
        self.selected_model = self.config.get('selected_model')
        self.available_models = []
        self.mode = self.config.get('current_mode', 'llama.cpp')
        self.ollama_online, self.llamacpp_online = self.server_is_reachable()

        self.initUI()

        if self.ollama_online:
            self.load_models_from_ollama()

        self.load_chat_to_display()

        if not self.conversation_history:
            self.display_welcome_message()

        self.setWindowIcon(self.create_transparent_icon())

    def list_models(self, parts=None):
        if self.mode == 'ollama':
            if not self.available_models:
                self.chat_history.append("<b style='color: yellow;'>No models are available from Ollama.</b>")
            else:
                self.chat_history.append("<b style='color: yellow;'>Available models from Ollama:</b>")
                for model in self.available_models:
                    self.chat_history.append(f"/selectmodel <b style='color: green;'>{model['name']}</b>")
        elif self.mode == 'openai':
            self.chat_history.append("<b style='color: yellow;'>gpt-4-o</b>")
        elif self.mode == 'llama.cpp':
            self.chat_history.append("<b style='color: yellow;'>Llama.cpp does not list models dynamically in this setup. Please specify the model manually if needed.</b>")
        else:
            self.chat_history.append("<b style='color: red;'>Unknown mode. Cannot list models.</b>")

        self.chat_history.moveCursor(QTextCursor.End)

    def create_transparent_icon(self):
        """Creates a transparent QIcon to replace the default window icon."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        return QIcon(pixmap)

    def send_openai_message(self, user_message):
        api_key = self.config.get('openaiapikey')
        if not api_key:
            self.handle_error("OpenAI API key is not set. Please update your configuration.")
            return

        openai_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        system_prompt = {"role": "system", "content": self.system_prompt if self.system_prompt else "You are a helpful assistant."}
        selected_model = self.selected_model if self.selected_model else "gpt-4o"

        data = {
            "model": selected_model,
            "messages": [system_prompt] + [{"role": "user", "content": user_message}] + self.conversation_history
        }

        self.worker = NetworkWorker(self.conversation_history, openai_url, data, headers)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def server_is_reachable(self):
        ollama_online = self.check_server_status(self.config.get("ollamahost", "127.0.0.1:11434"))
        llamacpp_online = self.check_server_status(self.config.get("llamacpphost", "127.0.0.1:8080"))
        return ollama_online, llamacpp_online
    
    def resetmodel(self, parts):
        if self.mode == 'ollama':
            self.mode = 'llama.cpp'
        elif self.mode == 'llama.cpp':
            self.mode = 'openai'
        else:
            self.mode = 'ollama'
            
        ConfigManager.save_config_value('current_mode', self.mode)
        self.chat_history.clear()
        self.load_chat_to_display()
        self.chat_history.append(f"<b style='color: yellow;'>Mode switched to {self.mode}. Chat history loaded.</b>")
        self.display_welcome_message()

    def check_server_status(self, host):
        try:
            response = requests.get(f"http://{host}")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def load_models_from_ollama(self):
        try:
            baseurl = self.config.get("baseurl", "http://")
            host = self.config.get("ollamahost", "127.0.0.1:11434")
            full_url = baseurl + host
            response = requests.get(f"{full_url}/api/tags")
            response.raise_for_status()
            models_info = response.json()
            self.available_models = models_info.get("models", [])
        except requests.RequestException as e:
            self.chat_history.append(f"<b style='color: red;'>Error fetching models from Ollama: {e}</b>")

    def display_welcome_message(self):
        ollama_status, llamacpp_status = self.server_is_reachable()
        openai_status = bool(self.config.get('openaiapikey'))

        ollama_status_message = f"<b style='color: {'green' if ollama_status else 'red'};'>Ollama host: {'Online' if ollama_status else 'Offline'}</b>"
        llamacpp_status_message = f"<b style='color: {'green' if llamacpp_status else 'red'};'>Llama.cpp host: {'Online' if llamacpp_status else 'Offline'}</b>"
        openai_status_message = f"<b style='color: {'green' if openai_status else 'red'};'>OpenAI: {'Configured' if openai_status else 'Not Configured'}</b>"

        welcome_message = f"""
        <h3>Welcome to Retrochat!</h3>
        <p>{ollama_status_message}</p>
        <p>{llamacpp_status_message}</p>
        <p>{openai_status_message}</p>
        """

        self.chat_history.setHtml(welcome_message)

        if openai_status:
            self.mode = 'openai'
            self.chat_history.append("<b style='color: yellow;'>OpenAI mode is selected.</b>")
        else:
            self.chat_history.append("<b style='color: yellow;'>To use OpenAI, please configure your API key:</b>")
            self.chat_history.append("<b style='color: green;'>/config openaiapikey your-key-here</b>")

        if ollama_status:
            self.mode = 'ollama'
            self.chat_history.append("<b style='color: yellow;'>Ollama mode is selected.</b>")
        elif llamacpp_status:
            self.mode = 'llama.cpp'
            self.chat_history.append("<b style='color: yellow;'>Llama.cpp is ready to chat.</b>")

        if ollama_status:
            self.display_models_list()

        self.help_message_displayed = True
        self.chat_history.moveCursor(QTextCursor.End)

    def process_input(self):
        user_message = self.user_input.text().strip()
        if user_message:
            if self.help_message_displayed:
                self.chat_history.clear()
                self.help_message_displayed = False

            if user_message.startswith("/"):
                self.execute_command(user_message)
                self.command_history.append(user_message)
                self.command_index = -1
            else:
                self.send_message(user_message)
            self.user_input.clear()

    def execute_command(self, command):
        parts = command.split(maxsplit=2)
        command_key = parts[0]

        commands = {
            "/config": self.update_config,
            "/chat": self.manage_chat,
            "/models": self.list_models,
            "/select_model": self.selectmodel,
            "/resetmodel": self.resetmodel,
            "/help": self.display_help_message,
            "/system_prompt": self.set_system_prompt,
        }

        if command_key in commands:
            if command_key in ["/config", "/select_model", "/system_prompt"]:
                if len(parts) >= 2:
                    commands[command_key](parts)
                else:
                    self.display_error(f"Usage: {command_key} requires an argument.")
            else:
                commands[command_key](parts)
        else:
            self.display_error(f"Invalid command: {command}")

    def set_system_prompt(self, parts):
        if len(parts) < 2:
            self.display_error("Usage: /system_prompt Your prompt message")
            return
        
        prompt_message = parts[1]
        
        self.system_prompt = prompt_message
        
        self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)
        
        self.chat_history.append(f"<b style='color: yellow;'>System prompt updated to: {prompt_message}</b>")
        self.chat_history.moveCursor(QTextCursor.End)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            if self.command_history:
                if self.command_index == -1:
                    self.command_index = len(self.command_history) - 1
                else:
                    self.command_index = max(0, self.command_index - 1)
                self.user_input.setText(self.command_history[self.command_index])
        elif event.key() == Qt.Key_Down:
            if self.command_index != -1:
                self.command_index = min(len(self.command_history), self.command_index + 1)
                if self.command_index < len(self.command_history):
                    self.user_input.setText(self.command_history[self.command_index])
                else:
                    self.user_input.clear()
                    self.command_index = -1
        elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.process_input()
        else:
            super().keyPressEvent(event)

    def selectmodel(self, parts):
        if len(parts) == 2:
            model_name = parts[1]

            if model_name in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]:
                self.mode = 'openai'
            elif any(model["name"] == model_name for model in self.available_models):
                self.mode = 'ollama'
            else:
                self.mode = 'llama.cpp'

            is_valid_model = False

            if self.mode == 'ollama':
                is_valid_model = any(model["name"] == model_name for model in self.available_models)
            elif self.mode == 'openai':
                valid_openai_models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
                is_valid_model = model_name in valid_openai_models

            if is_valid_model:
                self.selected_model = model_name
                ConfigManager.save_config_value('selected_model', model_name)
                self.chat_history.append(f"<b style='color: yellow;'>Model selected: {model_name}</b>")
                self.chat_history.clear()
                self.load_chat_to_display()
            else:
                self.display_error(f"Invalid model name: {model_name}. Please choose a valid model.")
        else:
            self.display_error("Usage: /select_model model_name")

    def display_error(self, message):
        self.chat_history.append(f"<b style='color: red;'>Error:</b> {message}")
        self.chat_history.moveCursor(QTextCursor.End)

    def initUI(self):
        self.setGeometry(300, 300, 1100, 550)
        
        self.setWindowFlags(Qt.Window)
        
        self.setWindowTitle(" ")

        main_layout = QVBoxLayout()
        chat_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Courier New", self.fontsize))
        self.chat_history.setStyleSheet(self.get_chat_style())

        self.chat_scroll_area = QScrollArea()
        self.chat_scroll_area.setWidgetResizable(True)
        self.chat_scroll_area.setWidget(self.chat_history)
        self.chat_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll_area.setFrameShape(QFrame.NoFrame)
        chat_layout.addWidget(self.chat_scroll_area)

        self.prompt_label = QLabel(">")
        self.prompt_label.setStyleSheet(self.get_prompt_style())
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message here...")
        self.user_input.returnPressed.connect(self.process_input)
        self.user_input.setFont(QFont("Courier New", self.fontsize))
        self.user_input.setStyleSheet(self.get_input_style())

        input_layout.addWidget(self.prompt_label, 0, Qt.AlignLeft)
        input_layout.addWidget(self.user_input, 1)

        main_layout.addLayout(chat_layout)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)
        self.setStyleSheet(self.get_global_style())

        if not self.conversation_history and not self.selected_model:
            self.display_help_message()

    def get_global_style(self):
        return f"""
            QWidget {{
                background-color: black;
                color: #00FF00;
                font-family: 'Courier New', Courier, monospace;
                font-size: {self.fontsize}px;
                border: none;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: #222222;
                margin: 0;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #00FF00;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none.
            }}
        """

    def get_chat_style(self):
        return f"padding: 5px; background-color: #000000; color: {self.config['umc']};"

    def get_prompt_style(self):
        return f"color: {self.config['umc']}; font-size: {self.fontsize}px; font-family: Courier New; margin: 0; padding: 0;"

    def get_input_style(self):
        return f"margin: 0; padding: 0; background-color: #000000; color: {self.config['umc']}; border: none;"

    def load_chat_to_display(self):
        self.chat_history.clear()
        for message in self.conversation_history:
            if message['role'] == 'user':
                user_message_html = markdown.markdown(message['content'], extensions=['tables', 'fenced_code'])
                user_message_html = self.apply_custom_css(user_message_html, role="user")
                self.chat_history.append(user_message_html)
            elif message['role'] == 'assistant':
                assistant_message_html = markdown.markdown(message['content'], extensions=['tables', 'fenced_code'])
                assistant_message_html = self.apply_custom_css(assistant_message_html, role="assistant")
                self.chat_history.append(assistant_message_html)
        self.chat_history.moveCursor(QTextCursor.End)

    def display_help_message(self, parts=None):
        help_message = """
        <p><strong>Available Commands:</strong></p>

        <p><strong>/config</strong></p>
        <p>Customize your chat experience by adjusting various settings.</p>
        <p><strong>Usage:</strong> <code>/config &lt;key&gt; &lt;value&gt;</code></p>
        <p><strong>Available Keys:</strong></p>
        <ul>
            <li><code>fontsize</code>: Adjust the size of the font. Example: <code>/config fontsize 18</code></li>
            <li><code>baseurl</code>: Set the base URL for API requests. Example: <code>/config baseurl http://new-url.com</code></li>
            <li><code>openaiapikey</code>: Set your OpenAI API key. Example: <code>/config openaiapikey YOUR_API_KEY</code></li>
            <li><code>umc</code>: Change the color of user messages. Example: <code>/config umc #00FF00</code></li>
            <li><code>amc</code>: Change the color of assistant messages. Example: <code>/config amc #FFBF00</code></li>
            <li><code>system_prompt</code>: Set a custom system prompt for the chat session. Example: <code>/config system_prompt "Your prompt here"</code></li>
        </ul>

        <p><strong>/chat</strong></p>
        <p>Manage your chat sessions.</p>
        <p><strong>Usage:</strong> <code>/chat &lt;action&gt; &lt;filename&gt; [new_name]</code></p>
        <p><strong>Available Actions:</strong></p>
        <ul>
            <li><code>new &lt;filename&gt;</code>: Create and switch to a new chat file. Example: <code>/chat new my_chat.json</code></li>
            <li><code>save &lt;filename&gt;</code>: Save the current chat history to a specified file. Example: <code>/chat save my_chat_backup.json</code></li>
            <li><code>delete &lt;filename&gt;</code>: Permanently delete a specified chat file. Example: <code>/chat delete old_chat.json</code></li>
            <li><code>reset</code>: Clear the current chat history. Example: <code>/chat reset</code></li>
            <li><code>rename &lt;old_filename&gt; &lt;new_filename&gt;</code>: Rename a chat file. Example: <code>/chat rename chat_1.json new_chat_name.json</code></li>
            <li><code>open &lt;filename&gt;</code>: Open and load an existing chat file. Example: <code>/chat open my_chat.json</code></li>
            <li><code>list</code>: List all JSON chat files in the current directory.</li>
        </ul>

        <p><strong>/models</strong></p>
        <p>List available models from Ollama or OpenAI (depending on the current mode).</p>

        <p><strong>/selectmodel</strong></p>
        <p>Select a model for the current mode. Example: <code>/selectmodel gpt-4o</code> for OpenAI or <code>/selectmodel model_name</code> for Ollama.</p>
        
        <p><strong>/resetmodel</strong></p>
        <p>Switch between available modes (llama.cpp, ollama, openai). Example: <code>/resetmodel</code></p>
        """
        self.chat_history.setHtml(help_message)
        self.help_message_displayed = True
        self.chat_history.moveCursor(QTextCursor.End)

    def update_config(self, parts):
        if len(parts) >= 3:
            key = parts[1]
            value = parts[2]

            if key == "openaiapikey":
                ConfigManager.save_config_value(key, value)
                self.config[key] = value
                self.chat_history.append(f"<b style='color: yellow;'>Config updated: {key} = {value}</b>")
                self.display_welcome_message()
            elif key == "system_prompt":
                self.system_prompt = value
                self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)
                self.chat_history.append(f"<b style='color: yellow;'>System prompt updated: {value}</b>")
            elif key in self.config:
                if key == "fontsize":
                    try:
                        value = int(value)
                    except ValueError:
                        self.display_error("Font size must be an integer.")
                        return
                    self.fontsize = value
                    self.update_fontsizes()

                ConfigManager.save_config_value(key, value)
                self.config[key] = value
                self.chat_history.append(f"<b style='color: yellow;'>Config updated: {key} = {value}</b>")
            else:
                self.display_error(f"Invalid configuration key: {key}")
        else:
            self.display_error("Usage: /config <key> <value>")

    def manage_chat(self, parts):
        if len(parts) >= 3:
            action, filename = parts[1], parts[2]
            filename = self.ensure_json_extension(filename)

            if action == "new":
                self.chat_manager.chat_filename = filename
                self.system_prompt = ""
                self.chat_manager.save_chat_history([], self.system_prompt)
                self.open_chat(filename)
                self.chat_history.append(f"<b style='color: yellow;'>New chat {filename} created and opened.</b>")
            elif action == "save":
                self.chat_manager.chat_filename = filename
                self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)
                self.chat_history.append(f"<b style='color: yellow;'>Chat saved as {filename}.</b>")
            elif action == "delete":
                self.chat_manager.set_chat_filename(filename)
                chat_history_path = os.path.join(os.getcwd(), self.chat_manager.chat_filename)
                if os.path.exists(chat_history_path):
                    os.remove(chat_history_path)
                    self.chat_history.append(f"<b style='color: yellow;'>Chat file {filename} deleted.</b>")
                else:
                    self.display_error(f"Chat file {filename} does not exist.")
            elif action == "reset":
                self.reset_chat()
            elif action == "rename" and len(parts) == 4:
                old_filename = self.ensure_json_extension(parts[2])
                new_filename = self.ensure_json_extension(parts[3])
                self.rename_chat_file(old_filename, new_filename)
            elif action == "open":
                self.open_chat(filename)
            else:
                self.display_error(f"Invalid chat command: {parts[0]} {parts[1]}")
        elif len(parts) == 2 and parts[1] == "reset":
            self.reset_chat()
        elif len(parts) == 2 and parts[1] == "list":
            self.list_chat_files()
        else:
            self.display_error(f"Invalid chat command: {parts[0]}")

    def rename_chat_file(self, old_filename, new_filename):
        old_path = os.path.join(os.getcwd(), old_filename)
        new_path = os.path.join(os.getcwd(), new_filename)
        
        if not os.path.exists(old_path):
            self.display_error(f"Chat file {old_filename} does not exist.")
            return
        
        if os.path.exists(new_path):
            self.display_error(f"Chat file {new_filename} already exists.")
            return
        
        try:
            shutil.move(old_path, new_path)
            self.chat_manager.set_chat_filename(new_filename)
            self.chat_history.append(f"<b style='color: yellow;'>Chat file renamed to {new_filename}.</b>")
        except Exception as e:
            self.display_error(f"Failed to rename chat file: {str(e)}")

    def list_chat_files(self):
        json_files = [f for f in os.listdir(os.getcwd()) if f.endswith('.json') and f != 'config.json']
        self.chat_history.append("<b style='color: yellow;'>Available chat files:</b>")
        for file in json_files:
            self.chat_history.append(f"<b style='color: green;'>{file}</b>")
        self.chat_history.moveCursor(QTextCursor.End)

    def reset_chat(self):
        self.conversation_history = []
        self.system_prompt = ""
        self.chat_history.clear()
        self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)
        self.chat_history.append(f"<b style='color: yellow;'>Chat history has been reset.</b>")
        self.chat_history.moveCursor(QTextCursor.End)

    def open_chat(self, chat_filename):
        self.chat_manager.chat_filename = chat_filename
        self.conversation_history, self.system_prompt = self.chat_manager.load_chat_history()
        self.chat_history.clear()
        self.load_chat_to_display()
        self.chat_history.append(f"<b style='color: yellow;'>Chat {chat_filename} opened.</b>")
        ConfigManager.save_config_value('current_chat_filename', chat_filename)

    def ensure_json_extension(self, filename):
        if not filename.endswith('.json'):
            filename += '.json'
        return filename

    def update_fontsizes(self):
        fontsize = int(self.fontsize)
        
        self.chat_history.setFont(QFont("Courier New", fontsize))
        
        self.user_input.setFont(QFont("Courier New", fontsize))
        
        self.prompt_label.setStyleSheet(f"color: {self.config['umc']}; font-size: {fontsize}px; font-family: Courier New; margin: 0; padding: 0;")
        
        self.chat_history.setStyleSheet(self.get_chat_style())
        
        self.setStyleSheet(self.get_global_style())
        
    def send_message(self, user_message):
        user_message_html = markdown.markdown(user_message, extensions=['tables', 'fenced_code'])
        user_message_html = self.apply_custom_css(user_message_html, role="user")
        
        self.chat_history.append(user_message_html)
        self.chat_history.moveCursor(QTextCursor.End)
        
        self.conversation_history.append({"role": "user", "content": user_message})
        self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)

        baseurl = self.config['baseurl']
        path = self.config['path']

        system_prompt = {"role": "system", "content": self.system_prompt if self.system_prompt else "You are a helpful assistant."}

        if self.mode == 'ollama':
            full_endpoint = f"{baseurl}{self.config['ollamahost']}{path}"
            data = {
                "model": self.selected_model,
                "messages": [system_prompt] + self.conversation_history
            }
        elif self.mode == 'llama.cpp':
            full_endpoint = f"{baseurl}{self.config['llamacpphost']}{path}"
            data = {
                "messages": [system_prompt] + self.conversation_history
            }
        elif self.mode == 'openai':
            openai_url = "https://api.openai.com/v1/chat/completions"
            api_key = self.config.get('openaiapikey')
            if not api_key:
                self.handle_error("OpenAI API key is not set. Please update your configuration.")
                return
            
            if not self.selected_model:
                self.selected_model = "gpt-4o"

            full_endpoint = openai_url
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": self.selected_model,
                "messages": [system_prompt] + self.conversation_history
            }
        else:
            self.handle_error("Invalid mode selected. Please check your configuration.")
            return

        headers = headers if self.mode == 'openai' else {"Content-Type": "application/json"}
        
        self.worker = NetworkWorker(self.conversation_history, full_endpoint, data, headers)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def handle_response(self, response):
        self.conversation_history.append({"role": "assistant", "content": response})
        self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)

        response_html = markdown.markdown(response, extensions=['tables', 'fenced_code'])
        response_html = self.apply_custom_css(response_html, role="assistant")
        self.chat_history.append(response_html)

        self.chat_history.moveCursor(QTextCursor.End)

    def handle_error(self, error_message):
        self.chat_history.append(f"<b style='color: red;'>Error:</b> {error_message}")

    def apply_custom_css(self, html_content, role):
        if role == "user":
            custom_css = f"""
            <style>
                div.user-message {{
                    color: {self.config['umc']};
                    font-family: 'Courier New';
                    background-color: #000000;
                    margin: 0;
                    padding: 2px 0;
                }}
                pre, code {{
                    background-color: #333333;
                    color: {self.config['umc']};
                    border-radius: 4px;
                    padding: 5px;
                    margin: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid {self.config['umc']};
                    padding: 3px;
                }}
                blockquote {{
                    border-left: 4px solid {self.config['umc']};
                    margin: 5px 0;
                    padding-left: 10px;
                    color: {self.config['umc']};
                    background-color: #222222;
                }}
            </style>
            """
            return f"{custom_css}<div class='user-message'>{html_content}</div>"
        else:
            custom_css = f"""
            <style>
                div.bot-message {{
                    color: {self.config['amc']};
                    font-family: 'Courier New';
                    background-color: #000000;
                    margin: 0;
                    padding: 2px 0;
                }}
                pre, code {{
                    background-color: #333333;
                    color: {self.config['amc']};
                    border-radius: 4px;
                    padding: 5px;
                    margin: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse.
                }}
                th, td {{
                    border: 1px solid {self.config['amc']};
                    padding: 3px;
                }}
                blockquote {{
                    border-left: 4px solid {self.config['amc']};
                    margin: 5px 0;
                    padding-left: 10px;
                    color: {self.config['amc']};
                    background-color: #222222;
                }}
            </style>
            """
            return f"{custom_css}<div class='bot-message'>{html_content}</div>"
        
    def display_models_list(self):
        ollama_status, _ = self.server_is_reachable()
        openai_status = bool(self.config.get('openaiapikey'))

        if openai_status:
            openai_models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
            self.chat_history.append("<b style='color: yellow;'>Available models from OpenAI:</b>")
            for model in openai_models:
                self.chat_history.append(f"<b style='color: green;'>/select_model {model}</b>")
            self.chat_history.append("<b style='color: yellow;'>Copy and paste a command to select a model and press enter.</b>")

        if ollama_status:
            if self.available_models:
                self.chat_history.append("<b style='color: yellow;'>Available models from Ollama:</b>")
                for model in self.available_models:
                    self.chat_history.append(f"<b style='color: green;'>/select_model {model['name']}</b>")
                self.chat_history.append("<b style='color: yellow;'>Copy and paste a command to select a model and press enter.</b>")
            else:
                self.chat_history.append("<b style='color: yellow;'>No available models found from Ollama.</b>")

        self.chat_history.moveCursor(QTextCursor.End)
    
    def list_models(self, parts):
        self.display_models_list()

if __name__ == "__main__":
    config = ConfigManager.load_config()

    expected_chat_structure = {
        "system_prompt": "",
        "conversation_history": []
    }

    chat_manager = ChatHistoryManager()
    chat_manager.ensure_chat_files_are_up_to_date(expected_chat_structure)

    app = QApplication([])

    chatbox = Chatbox()
    set_amoled_black_title_bar(chatbox)
    chatbox.show()

    sys.exit(app.exec_())