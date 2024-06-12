import os
import sys
import json
import requests
import markdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QTextCursor, QFont

class ConfigManager:
    CONFIG_FILENAME = "config.json"
    DEFAULT_CONFIG = {
        "base_url": "http://",
        "ollama_host": "127.0.0.1:11434",
        "llama.cpp_host": "127.0.0.1:8080",
        "path": "/v1/chat/completions",
        "user_message_color": "#00FF00",
        "assistant_message_color": "#FFBF00",
        "font_size": 18,
        "current_chat_filename": "chat_1.json",
        "selected_model": "",
        "current_mode": "llama.cpp"
    }

    @classmethod
    def load_config(cls):
        config_path = os.path.join(os.getcwd(), cls.CONFIG_FILENAME)
        if not os.path.exists(config_path):
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG
        try:
            with open(config_path, 'r') as config_file:
                return json.load(config_file)
        except (json.JSONDecodeError, Exception):
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
                    return chat_data.get("conversation_history", []), chat_data.get("system_prompt", "")
            except json.JSONDecodeError:
                return [], ""
        return [], ""

    def delete_chat_file(self):
        chat_history_path = os.path.join(os.getcwd(), self.chat_filename)
        if os.path.exists(chat_history_path):
            try:
                os.remove(chat_history_path)
                print(f"Deleted file: {chat_history_path}")
            except Exception as e:
                print(f"Error deleting file {chat_history_path}: {e}")
        else:
            print(f"File does not exist: {chat_history_path}")

    def rename_chat_file(self, new_name):
        old_path = os.path.join(os.getcwd(), self.chat_filename)
        new_path = os.path.join(os.getcwd(), new_name)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            self.chat_filename = new_name
            ConfigManager.save_config_value('current_chat_filename', new_name)

    def set_chat_filename(self, filename):
        self.chat_filename = filename

    def get_next_available_filename(self):
        index = 1
        while True:
            filename = f"chat_{index}.json"
            if not os.path.exists(filename):
                return filename
            index += 1

class CustomTitleBar(QWidget):
    def __init__(self, parent=None, font_size=14):
        super().__init__(parent)
        self.parent_widget = parent
        self.font_size = font_size
        self.initUI()

    def initUI(self):
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #333333; color: #00FF00;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.minimize_button = QPushButton("-")
        self.minimize_button.clicked.connect(self.parent_widget.showMinimized)
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(self.font_size))

        self.fullscreen_button = QPushButton("[ ]")
        self.fullscreen_button.clicked.connect(self.toggleFullscreen)
        self.fullscreen_button.setFixedSize(30, 30)
        self.fullscreen_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(self.font_size))

        self.close_button = QPushButton("x")
        self.close_button.clicked.connect(self.parent_widget.close)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(self.font_size))

        layout.addStretch()
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.fullscreen_button)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def toggleFullscreen(self):
        if self.parent_widget.isMaximized():
            self.parent_widget.showNormal()
        else:
            self.parent_widget.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_widget.is_moving = True
            self.parent_widget.startPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.parent_widget.is_moving:
            delta = QPoint(event.globalPos() - self.parent_widget.startPos)
            self.parent_widget.move(self.parent_widget.x() + delta.x(), self.parent_widget.y() + delta.y())
            self.parent_widget.startPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.parent_widget.is_moving = False

    def update_buttons_font_size(self, font_size):
        self.minimize_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(font_size))
        self.fullscreen_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(font_size))
        self.close_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(font_size))

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager.load_config()
        self.chat_manager = ChatHistoryManager(chat_filename=self.config.get('current_chat_filename', 'chat_1.json'))
        self.font_size = int(self.config.get("font_size", 18))
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

    def server_is_reachable(self):
        ollama_online = self.check_server_status(self.config.get("ollama_host", "127.0.0.1:11434"))
        llamacpp_online = self.check_server_status(self.config.get("llama.cpp_host", "127.0.0.1:8080"))
        return ollama_online, llamacpp_online
    
    def reset_mode(self, parts):
        if self.mode == 'ollama':
            self.mode = 'llama.cpp'
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
            base_url = self.config.get("base_url", "http://")
            host = self.config.get("ollama_host", "127.0.0.1:11434")
            full_url = base_url + host
            response = requests.get(f"{full_url}/api/tags")
            response.raise_for_status()
            models_info = response.json()
            self.available_models = models_info.get("models", [])
        except requests.RequestException as e:
            self.chat_history.append(f"<b style='color: red;'>Error fetching models from Ollama: {e}</b>")

    def display_welcome_message(self):
        ollama_status, llamacpp_status = self.server_is_reachable()

        ollama_status_message = f"<b style='color: {'green' if ollama_status else 'red'};'>Ollama host: {'Online' if ollama_status else 'Offline'}</b>"
        llamacpp_status_message = f"<b style='color: {'green' if llamacpp_status else 'red'};'>Llama.cpp host: {'Online' if llamacpp_status else 'Offline'}</b>"

        welcome_message = f"""
        <h3>Welcome to Retrochat!</h3>
        <p>{ollama_status_message}</p>
        <p>{llamacpp_status_message}</p>
        """

        self.chat_history.setHtml(welcome_message)

        if ollama_status:
            self.mode = 'ollama'
            self.display_models_list()
        elif llamacpp_status:
            self.mode = 'llama.cpp'
            self.chat_history.append("<b style='color: yellow;'>Llama.cpp is ready to chat.</b>")

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
        parts = command.split(maxsplit=1)
        command_key = parts[0]

        commands = {
            "/config": self.update_config,
            "/chat": self.manage_chat,
            "/models": self.list_models,
            "/select_model": self.select_model,
            "/reset_mode": self.reset_mode,
            "/help": self.display_help_message,
        }

        if command_key in commands:
            if command_key == "/config":
                config_parts = command.split(maxsplit=2)
                if len(config_parts) == 3:
                    commands[command_key](config_parts)
                else:
                    self.display_error("Usage: /config <key> <value>")
            else:
                parts = command.split(maxsplit(2))
                commands[command_key](parts)
        else:
            self.display_error(f"Invalid command: {command}")

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

    def select_model(self, parts):
        if len(parts) == 2:
            model_name = parts[1]
            matching_model = next((model for model in self.available_models if model["name"] == model_name), None)
            if matching_model:
                self.selected_model = model_name
                ConfigManager.save_config_value('selected_model', model_name)
                self.chat_history.append(f"<b style='color: yellow;'>Selected model: {model_name}</b>")
                self.chat_history.clear()
                self.load_chat_to_display()
            else:
                self.display_error(f"Model {model_name} not found in the available models.")
        else:
            self.display_error("Usage: /select_model model_name")

    def display_error(self, message):
        self.chat_history.append(f"<b style='color: red;'>Error:</b> {message}")
        self.chat_history.moveCursor(QTextCursor.End)

    def initUI(self):
        self.setGeometry(300, 300, 1100, 550)
        self.setWindowFlags(Qt.FramelessWindowHint)

        main_layout = QVBoxLayout()
        chat_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        self.custom_title_bar = CustomTitleBar(self, self.font_size)
        main_layout.addWidget(self.custom_title_bar)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Courier New", self.font_size))
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
        self.user_input.setFont(QFont("Courier New", self.font_size))
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
                font-size: {self.font_size}px;
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
        return f"padding: 10px; background-color: #000000; color: {self.config['user_message_color']};"

    def get_prompt_style(self):
        return f"color: {self.config['user_message_color']}; font-size: {self.font_size}px; font-family: Courier New; margin: 0; padding: 0;"

    def get_input_style(self):
        return f"margin: 0; padding: 0; background-color: #000000; color: {self.config['user_message_color']}; border: none;"

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

    def display_help_message(self):
        help_message = """
        <h3>Welcome to Retrochat!</h3>
        <p>Here’s a quick guide to help you get started and make the most out of this application.</p>
        
        <p><strong>Available Commands:</strong></p>

        <p><strong>/config</strong></p>
        <p>Customize your chat experience by adjusting various settings.</p>
        <p><strong>Usage:</strong> <code>/config &lt;key&gt; &lt;value&gt;</code></p>
        <p><strong>Available Keys:</strong></p>
        <ul>
            <li><code>font_size</code>: Adjust the size of the font. Example: <code>/config font_size 18</code></li>
            <li><code>base_url</code>: Set the base URL for API requests. Example: <code>/config base_url http://new-url.com</code></li>
            <li><code>host</code>: Define the server host and port. Example: <code>/config host 127.0.0.1:5000</code></li>
            <li><code>path</code>: Specify the API endpoint path. Example: <code>/config path /v2/chat/completions</code></li>
            <li><code>user_message_color</code>: Change the color of user messages. Example: <code>/config user_message_color #00FF00</code></li>
            <li><code>assistant_message_color</code>: Change the color of assistant messages. Example: <code>/config assistant_message_color #FFBF00</code></li>
            <li><code>system_prompt</code>: Set a custom system prompt for the chat session. Example: <code>/config system_prompt "Your prompt here"</code></li>
        </ul>

        <strong>/chat</strong>
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
        
        <strong>/models</strong>
        <p>List available models from Ollama.</p>

        <strong>/models</strong>
        """
        self.chat_history.setHtml(help_message)
        self.help_message_displayed = True

    def update_config(self, parts):
        if len(parts) >= 3:
            key = parts[1]
            value = parts[2] if len(parts) == 3 else ' '.join(parts[2:])

            if key == "system_prompt":
                self.system_prompt = value
                self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)
                self.chat_history.append(f"<b style='color: yellow;'>System prompt updated: {value}</b>")
            elif key in self.config:
                ConfigManager.save_config_value(key, value)
                self.config[key] = value
                if key == "font_size":
                    self.font_size = int(value)
                    self.update_font_sizes()
                self.chat_history.append(f"<b style='color: yellow;'>Config updated: {key} = {value}</b>")
            else:
                self.display_error(f"Invalid configuration key: {key}")

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
                self.chat_manager.delete_chat_file()

                chat_history_path = os.path.join(os.getcwd(), self.chat_manager.chat_filename)
                if not os.path.exists(chat_history_path):
                    self.chat_history.append(f"<b style='color: yellow;'>Chat file {filename} deleted.</b>")
                else:
                    self.display_error(f"Failed to delete chat file: {filename}")

                self.chat_manager.set_chat_filename(self.chat_manager.get_next_available_filename())
            elif action == "reset":
                self.reset_chat()
            elif action == "rename" and len(parts) == 4:
                new_name = self.ensure_json_extension(parts[3])
                self.chat_manager.rename_chat_file(new_name)
                self.chat_history.append(f"<b style='color: yellow;'>Chat file renamed to {new_name}.</b>")
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

    def update_font_sizes(self):
        font_size = int(self.font_size)
        
        self.chat_history.setFont(QFont("Courier New", font_size))
        
        self.user_input.setFont(QFont("Courier New", font_size))
        
        self.prompt_label.setStyleSheet(f"color: {self.config['user_message_color']}; font-size: {font_size}px; font-family: Courier New; margin: 0; padding: 0;")
        
        self.custom_title_bar.font_size = font_size
        self.custom_title_bar.update_buttons_font_size(font_size)
        
        self.chat_history.setStyleSheet(self.get_chat_style())
        
        self.setStyleSheet(self.get_global_style())
        
    def send_message(self, user_message):
        user_message_html = markdown.markdown(user_message, extensions=['tables', 'fenced_code'])
        user_message_html = self.apply_custom_css(user_message_html, role="user")
        
        self.chat_history.append(user_message_html)
        self.chat_history.moveCursor(QTextCursor.End)
        
        self.conversation_history.append({"role": "user", "content": user_message})
        self.chat_manager.save_chat_history(self.conversation_history, self.system_prompt)

        base_url = self.config['base_url']
        path = self.config['path']

        system_prompt = {"role": "system", "content": self.system_prompt if self.system_prompt else "You are a helpful assistant."}

        if self.mode == 'ollama':
            full_endpoint = f"{base_url}{self.config['ollama_host']}{path}"
            data = {
                "model": self.selected_model,
                "messages": [system_prompt] + self.conversation_history
            }
        else:
            full_endpoint = f"{base_url}{self.config['llama.cpp_host']}{path}"
            data = {
                "messages": [system_prompt] + self.conversation_history
            }

        self.worker = NetworkWorker(self.conversation_history, full_endpoint, data)
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
                    color: {self.config['user_message_color']};
                    font-family: 'Courier New';
                    background-color: #000000;
                    margin: 0;
                    padding: 2px 0;
                }}
                pre, code {{
                    background-color: #333333;
                    color: {self.config['user_message_color']};
                    border-radius: 4px;
                    padding: 5px;
                    margin: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid {self.config['user_message_color']};
                    padding: 3px;
                }}
                blockquote {{
                    border-left: 4px solid {self.config['user_message_color']};
                    margin: 5px 0;
                    padding-left: 10px;
                    color: {self.config['user_message_color']};
                    background-color: #222222;
                }}
            </style>
            """
            return f"{custom_css}<div class='user-message'>{html_content}</div>"
        else:
            custom_css = f"""
            <style>
                div.bot-message {{
                    color: {self.config['assistant_message_color']};
                    font-family: 'Courier New';
                    background-color: #000000;
                    margin: 0;
                    padding: 2px 0;
                }}
                pre, code {{
                    background-color: #333333;
                    color: {self.config['assistant_message_color']};
                    border-radius: 4px;
                    padding: 5px;
                    margin: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse.
                }}
                th, td {{
                    border: 1px solid {self.config['assistant_message_color']};
                    padding: 3px;
                }}
                blockquote {{
                    border-left: 4px solid {self.config['assistant_message_color']};
                    margin: 5px 0;
                    padding-left: 10px;
                    color: {self.config['assistant_message_color']};
                    background-color: #222222;
                }}
            </style>
            """
            return f"{custom_css}<div class='bot-message'>{html_content}</div>"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_on_border(event.pos()):
                self.resizing = True
                self.resize_direction = self.get_resize_direction(event.pos())
                self.oldPos = event.globalPos()
            else:
                self.is_moving = True
                self.startPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.resizing:
            self.handle_resize(event)
        elif self.is_moving:
            delta = QPoint(event.globalPos() - self.startPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.startPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.is_moving = False
        self.resizing = False

    def handle_resize(self, event):
        if self.resizing:
            diff = event.globalPos() - self.oldPos
            if self.resize_direction == 'bottom_right':
                self.resize(self.width() + diff.x(), self.height() + diff.y())
            elif self.resize_direction == 'bottom':
                self.resize(self.width(), self.height() + diff.y())
            elif self.resize_direction == 'right':
                self.resize(self.width() + diff.x(), self.height())
            self.oldPos = event.globalPos()

    def is_on_border(self, pos):
        margin = 10
        rect = self.rect()
        bottom_right = QRect(rect.right() - margin, rect.bottom() - margin, margin, margin)
        bottom = QRect(rect.left(), rect.bottom() - margin, rect.width(), margin)
        right = QRect(rect.right() - margin, rect.top(), margin, rect.height())

        return bottom_right.contains(pos) or bottom.contains(pos) or right.contains(pos)

    def get_resize_direction(self, pos):
        margin = 10
        rect = self.rect()
        if QRect(rect.right() - margin, rect.bottom() - margin, margin, margin).contains(pos):
            return 'bottom_right'
        if QRect(rect.left(), rect.bottom() - margin, rect.width(), margin).contains(pos):
            return 'bottom'
        if QRect(rect.right() - margin, rect.top(), margin, rect.height()).contains(pos):
            return 'right'
        return None

    def display_models_list(self):
        if self.available_models:
            self.chat_history.append("<b style='color: yellow;'>Available models from Ollama:</b>")
            for model in self.available_models:
                self.chat_history.append(f"<b style='color: green;'>/select_model {model['name']}</b>")
            self.chat_history.append("<b style='color: yellow;'>Copy and paste a command to select a model and press enter.</b>")
        else:
            self.chat_history.append("<b style='color: yellow;'>No available models found.</b>")
        self.chat_history.moveCursor(QTextCursor.End)

    def list_models(self, parts):
        self.display_models_list()

class NetworkWorker(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversation_history, endpoint, data):
        super().__init__()
        self.conversation_history = conversation_history
        self.endpoint = endpoint
        self.data = data

    def run(self):
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.endpoint, headers=headers, json=self.data)
            if response.status_code == 200:
                bot_message = response.json()["choices"][0]["message"]["content"].strip()
                self.response_received.emit(bot_message)
            else:
                self.error_occurred.emit(f"{response.status_code} - {response.text}")
        except requests.RequestException as e:
            self.error_occurred.emit(str(e))

if __name__ == "__main__":
    app = QApplication([])
    chatbox = Chatbox()
    chatbox.show()
    sys.exit(app.exec_())
