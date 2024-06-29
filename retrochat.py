import os
import sys
import json
import requests
import markdown
import shutil
import ctypes
from ctypes import windll, byref, c_int, sizeof
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel, QPushButton, QDialog, QFormLayout, QComboBox, QSpinBox
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
        "ollamahost": "192.168.1.82:11434",
        "llamacpphost": "192.168.1.82:8080",
        "path": "/v1/chat/completions",
        "user_color": "#00FF00",
        "assistant_color": "#FFBF00",
        "fontsize": 18,
        "current_chat_filename": "",
        "selected_model": "",
        "current_mode": "",
        "openaiapikey": "",
        "window_geometry": None,
        "window_state": "normal"
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
    def save_window_state(cls, geometry, state):
        config = cls.load_config()
        config['window_geometry'] = geometry
        config['window_state'] = state
        cls.save_config(config)

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


class OptionsDialog(QDialog):
    def __init__(self, commands, parent=None):
        super().__init__(parent)
        self.commands = commands
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Options")
        layout = QFormLayout()

        self.command_box = QComboBox(self)
        for command in self.commands.keys():
            self.command_box.addItem(command)
        self.command_box.currentIndexChanged.connect(self.update_arguments)

        self.arguments_layout = QVBoxLayout()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.execute_command)

        layout.addRow("Command", self.command_box)
        layout.addRow(self.arguments_layout)
        layout.addRow(self.ok_button)

        self.setLayout(layout)
        self.resize(400, 300)

        self.update_arguments()

    def update_arguments(self):
        command = self.command_box.currentText()
        self.clear_arguments_layout()
        if command == "/config":
            key_box = QComboBox()
            key_box.addItems(["baseurl", "ollamahost", "llamacpphost", "path", "user_color", "assistant_color", "fontsize", "openaiapikey"])
            value_input = QLineEdit()
            value_input.setStyleSheet("background-color: #D3D3D3;")
            self.arguments_layout.addWidget(QLabel("Key:"))
            self.arguments_layout.addWidget(key_box)
            self.arguments_layout.addWidget(QLabel("Value:"))
            self.arguments_layout.addWidget(value_input)
            self.arguments_layout.key_box = key_box
            self.arguments_layout.value_input = value_input
        elif command == "/select_model":
            provider_box = QComboBox()
            provider_box.addItems(["OpenAI", "Anthropic", "Ollama"])
            provider_box.currentIndexChanged.connect(self.update_models)
            model_box = QComboBox()
            self.update_models(provider_box.currentIndex())

            self.arguments_layout.addWidget(QLabel("Provider:"))
            self.arguments_layout.addWidget(provider_box)
            self.arguments_layout.addWidget(QLabel("Model:"))
            self.arguments_layout.addWidget(model_box)
            self.arguments_layout.provider_box = provider_box
            self.arguments_layout.model_box = model_box
        elif command == "/system_prompt":
            prompt_input = QLineEdit()
            prompt_input.setStyleSheet("background-color: #D3D3D3;")
            self.arguments_layout.addWidget(QLabel("Prompt:"))
            self.arguments_layout.addWidget(prompt_input)
            self.arguments_layout.prompt_input = prompt_input

    def update_models(self, index):
        provider = self.arguments_layout.provider_box.currentText()
        model_box = self.arguments_layout.model_box
        model_box.clear()

        if provider == "OpenAI":
            model_box.addItems(["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        elif provider == "Anthropic":
            model_box.addItems(["claude-v1", "claude-v2"])
        elif provider == "Ollama":
            if self.parent and self.parent.available_models:
                model_box.addItems([model['name'] for model in self.parent.available_models])

    def clear_arguments_layout(self):
        for i in reversed(range(self.arguments_layout.count())):
            widget = self.arguments_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def execute_command(self):
        command = self.command_box.currentText()
        arguments = ""
        if command == "/config":
            key = self.arguments_layout.key_box.currentText()
            value = self.arguments_layout.value_input.text()
            arguments = f"{key} {value}"
        elif command == "/select_model":
            provider = self.arguments_layout.provider_box.currentText().lower()
            model = self.arguments_layout.model_box.currentText()
            arguments = f"{provider} {model}"
        elif command == "/system_prompt":
            prompt = self.arguments_layout.prompt_input.text()
            arguments = f"{prompt}"

        self.parent().user_input.setText(f"{command} {arguments}")
        self.parent().process_input()
        self.close()


class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager.load_config()

        # Ensure default values if not present
        current_chat_filename = self.config.get('current_chat_filename', 'chat_1.json')
        if not current_chat_filename:
            current_chat_filename = 'chat_1.json'
            ConfigManager.save_config_value('current_chat_filename', current_chat_filename)

        self.selected_model = self.config.get('selected_model', "")
        self.mode = self.config.get('current_mode', "llama.cpp")

        self.chat_manager = ChatHistoryManager(chat_filename=current_chat_filename)

        # Ensure the chat file exists or create it
        self.ensure_chat_file_exists(current_chat_filename)

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
        self.available_models = []
        self.ollama_online, self.llamacpp_online = self.server_is_reachable()

        self.is_full_screen = False

        self.commands = {
            "/config": self.update_config,
            "/chat": self.manage_chat,
            "/models": self.list_models,
            "/select_model": self.select_model,
            "/resetmodel": self.reset_model,
            "/system_prompt": self.set_system_prompt,
        }

        self.initUI()

        if self.ollama_online:
            self.load_models_from_ollama()

        self.load_chat_to_display()

        if not self.conversation_history:
            self.display_welcome_message()

        self.setWindowIcon(self.create_transparent_icon())

        self.restore_window_state()

    def ensure_chat_file_exists(self, filename):
        """Ensure the specified chat file exists or create it if it doesn't."""
        if not os.path.exists(filename):
            default_structure = {
                "system_prompt": "",
                "conversation_history": []
            }
            self.chat_manager.create_new_file_with_structure(filename, default_structure)

    def restore_window_state(self):
        """Restore the window's last state from the config."""
        geometry = self.config.get('window_geometry')
        is_maximized = self.config.get('window_state', "normal") == "maximized"
        full_screen = self.config.get('is_full_screen', False)

        if geometry:
            x, y, width, height = geometry

            adjusted_y = y + 40
            self.setGeometry(x, adjusted_y, width, height)

        if is_maximized:
            self.showMaximized()
        elif full_screen:
            self.enter_full_screen()
        else:
            self.showNormal()

    def save_window_state(self):
        """Save the window's current state to the config."""
        if self.isFullScreen():
            self.config['window_geometry'] = (self.x(), self.y(), self.width(), self.height())
            self.config['window_state'] = "full_screen"
            self.is_full_screen = True
        elif self.isMaximized():
            normal_geom = self.normalGeometry()
            self.config['window_geometry'] = (normal_geom.x(), normal_geom.y(), normal_geom.width(), normal_geom.height())
            self.config['window_state'] = "maximized"
            self.is_full_screen = False
        else:
            self.config['window_geometry'] = (self.x(), self.y(), self.width(), self.height())
            self.config['window_state'] = "normal"
            self.is_full_screen = False

        ConfigManager.save_config(self.config)

    def enter_full_screen(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.showFullScreen()
        self.is_full_screen = True

    def exit_full_screen(self):
        self.setWindowFlags(Qt.Window)
        self.showNormal()
        self.is_full_screen = False

    def toggle_full_screen(self):
        if self.is_full_screen:
            self.exit_full_screen()
        else:
            self.enter_full_screen()

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
        elif event.key() == Qt.Key_Escape:
            if self.is_full_screen:
                self.exit_full_screen()
        elif event.key() == Qt.Key_F11:
            self.toggle_full_screen()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle window close event to save state before closing."""
        self.save_window_state()

        ConfigManager.save_config_value('selected_model', self.selected_model)
        ConfigManager.save_config_value('current_mode', self.mode)
        ConfigManager.save_config_value('current_chat_filename', self.chat_manager.chat_filename)

        event.accept()

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

        if command_key in self.commands:
            if command_key in ["/config", "/select_model", "/system_prompt"]:
                if len(parts) >= 2:
                    self.commands[command_key](parts)
                else:
                    self.display_error(f"Usage: {command_key} requires an argument.")
            else:
                self.commands[command_key](parts)
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

    def select_model(self, parts):
        if len(parts) == 3:
            provider, model_name = parts[1], parts[2]

            if provider == "openai":
                self.mode = 'openai'
                is_valid_model = model_name in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
            elif provider == "anthropic":
                self.mode = 'anthropic'
                is_valid_model = model_name in ["claude-v1", "claude-v2"]
            elif provider == "ollama":
                self.mode = 'ollama'
                is_valid_model = any(model["name"] == model_name for model in self.available_models)
            else:
                is_valid_model = False

            if is_valid_model:
                self.selected_model = model_name
                ConfigManager.save_config_value('selected_model', model_name)
                ConfigManager.save_config_value('current_mode', self.mode)
                self.chat_history.append(f"<b style='color: yellow;'>Provider: {provider.capitalize()}, Model: {model_name}</b>")
                self.chat_history.clear()
                self.load_chat_to_display()
            else:
                self.display_error(f"Invalid model name: {model_name}. Please choose a valid model.")
        else:
            self.display_error("Usage: /select_model provider model_name")

    def reset_model(self, parts):
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

        self.options_button = QPushButton("Options")
        self.options_button.clicked.connect(self.show_options_dialog)

        input_layout.addWidget(self.prompt_label, 0, Qt.AlignLeft)
        input_layout.addWidget(self.user_input, 1)
        input_layout.addWidget(self.options_button, 0, Qt.AlignRight)

        main_layout.addLayout(chat_layout)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)
        self.setStyleSheet(self.get_global_style())

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
                background: none.
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none.
            }}
            QTextEdit {{
                padding: 1px;  /* Further reduced padding */
                margin: 0;    /* No margin */
                line-height: 1.1;  /* Further adjusted line height */
            }}
        """

    def get_chat_style(self):
        return f"padding: 5px; background-color: #000000; color: {self.config['user_color']};"

    def get_prompt_style(self):
        return f"color: {self.config['user_color']}; font-size: {self.fontsize}px; font-family: Courier New; margin: 0; padding: 0;"

    def get_input_style(self):
        return f"margin: 0; padding: 0; background-color: #000000; color: {self.config['user_color']}; border: none;"

    def show_options_dialog(self):
        options_dialog = OptionsDialog(self.commands, self)
        options_dialog.exec_()

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

        self.prompt_label.setStyleSheet(f"color: {self.config['user_color']}; font-size: {fontsize}px; font-family: Courier New; margin: 0; padding: 0;")

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
        custom_css = """
        <style>
            .user-message, .bot-message {
                margin: 1px 0;
                padding: 0;
                line-height: 1.1;
                margin-bottom: 1px;
            }
            pre, code {
                background-color: #333333;
                border-radius: 4px;
                padding: 2px;
                margin: 0;
            }
            table {
                width: 100%;
                border-collapse: collapse.
            }
            th, td {
                border: 1px solid.
                padding: 2px;
            }
            blockquote {
                border-left: 4px solid;
                margin: 3px 0;
                padding-left: 10px;
                background-color: #222222;
            }
        </style>
        """
        if role == "user":
            custom_css += f"""
            <style>
                .user-message {{
                    color: {self.config['user_color']};
                    font-family: 'Courier New';
                    background-color: #000000;
                }}
                blockquote {{
                    color: {self.config['user_color']};
                    border-color: {self.config['user_color']};
                }}
            </style>
            """
            return f"{custom_css}<div class='user-message'>{html_content}</div>"
        else:
            custom_css += f"""
            <style>
                .bot-message {{
                    color: {self.config['assistant_color']};
                    font-family: 'Courier New';
                    background-color: #000000;
                }}
                blockquote {{
                    color: {self.config['assistant_color']};
                    border-color: {self.config['assistant_color']};
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
                self.chat_history.append(f"<b style='color: green;'>/select_model openai {model}</b>")
            self.chat_history.append("<b style='color: yellow;'>Copy and paste a command to select a model and press enter.</b>")

        if ollama_status:
            if self.available_models:
                self.chat_history.append("<b style='color: yellow;'>Available models from Ollama:</b>")
                for model in self.available_models:
                    self.chat_history.append(f"<b style='color: green;'>/select_model ollama {model['name']}</b>")
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
