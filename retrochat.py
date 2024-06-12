import os
import sys
import json
import requests
import markdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel, QPushButton, QComboBox, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QTextCursor, QFont

# ConfigManager class (unchanged)
class ConfigManager:
    CONFIG_FILENAME = "config.json"
    DEFAULT_CONFIG = {
        "base_url": "http://",
        "ollama_host": "127.0.0.1:11434",
        "path": "/v1/chat/completions",
        "user_message_color": "#00FF00",
        "assistant_message_color": "#FFBF00",
        "font_size": 18,
        "current_chat_filename": "chat_1.json",
        "selected_model": None
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

# ChatHistoryManager class (unchanged)
class ChatHistoryManager:
    def __init__(self, chat_filename="chat_1.json"):
        self.chat_filename = chat_filename

    def save_chat_history(self, chat_history):
        chat_history_path = os.path.join(os.getcwd(), self.chat_filename)
        with open(chat_history_path, 'w') as file:
            json.dump(chat_history, file, indent=4)
        ConfigManager.save_config_value('current_chat_filename', self.chat_filename)

    def load_chat_history(self):
        chat_history_path = os.path.join(os.getcwd(), self.chat_filename)
        if os.path.exists(chat_history_path):
            try:
                with open(chat_history_path, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return []
        return []

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

# CustomTitleBar class (unchanged)
class CustomTitleBar(QWidget):
    def __init__(self, parent=None, font_size=14):
        super().__init__(parent)
        self.parent = parent
        self.font_size = font_size
        self.initUI()

    def initUI(self):
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #333333; color: #00FF00;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.minimize_button = QPushButton("-")
        self.minimize_button.clicked.connect(self.parent.showMinimized)
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(self.font_size))

        self.fullscreen_button = QPushButton("[ ]")
        self.fullscreen_button.clicked.connect(self.toggleFullscreen)
        self.fullscreen_button.setFixedSize(30, 30)
        self.fullscreen_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(self.font_size))

        self.close_button = QPushButton("x")
        self.close_button.clicked.connect(self.parent.close)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(self.font_size))

        layout.addStretch()
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.fullscreen_button)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def toggleFullscreen(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.is_moving = True
            self.parent.startPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.parent.is_moving:
            delta = QPoint(event.globalPos() - self.parent.startPos)
            self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
            self.parent.startPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.parent.is_moving = False

# Chatbox class
class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager.load_config()
        self.chat_manager = ChatHistoryManager(chat_filename=self.config.get('current_chat_filename', 'chat_1.json'))
        self.font_size = self.config.get("font_size", 14)
        self.conversation_history = self.chat_manager.load_chat_history()
        self.command_history = []
        self.command_index = -1
        self.is_moving = False
        self.startPos = QPoint(0, 0)
        self.help_message_displayed = False
        self.resizing = False
        self.resize_direction = None
        self.oldPos = QPoint(0, 0)
        self.selected_model = self.config.get('selected_model')  # Load the selected model from config
        self.available_models = []  
        self.initUI()

        if self.server_is_reachable():
            if not self.selected_model:
                self.prompt_model_selection()
            else:
                self.load_chat_to_display()
        else:
            self.display_error("Server is not reachable. Please check the configuration.")

    def server_is_reachable(self):
        try:
            base_url = self.config.get("base_url", "http://")
            host = self.config.get("ollama_host", "127.0.0.1:11434")
            full_url = base_url + host
            response = requests.get(f"{full_url}/api/tags")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def prompt_model_selection(self):
        self.load_models_from_ollama()
        if self.available_models:
            dialog = ModelSelectionDialog(self.available_models)
            if dialog.exec_():
                selected_model = dialog.get_selected_model()
                self.selected_model = selected_model
                ConfigManager.save_config_value('selected_model', selected_model)
                self.chat_history.clear()
                self.load_chat_to_display()
        else:
            self.display_error("No models available to select.")

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
                background: none;
            }}
        """

    def get_chat_style(self):
        return f"padding: 10px; background-color: #000000; color: {self.config['user_message_color']};"

    def get_prompt_style(self):
        return f"color: {self.config['user_message_color']}; font-size: {self.font_size}px; font-family: Courier New; margin: 0; padding: 0;"

    def get_input_style(self):
        return f"margin: 0; padding: 0; background-color: #000000; color: {self.config['user_message_color']}; border: none;"

    def load_chat_to_display(self):
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

    def process_input(self):
        user_message = self.user_input.text().strip()
        if user_message:
            if self.help_message_displayed:
                self.chat_history.clear()
                self.help_message_displayed = False
                self.chat_manager.save_chat_history([])

            if user_message.startswith("/"):
                self.execute_command(user_message)
                self.command_history.append(user_message)
                self.command_index = -1
            else:
                self.send_message(user_message)
            self.user_input.clear()

    def execute_command(self, command):
        parts = command.split(maxsplit=3)
        commands = {
            "/config": self.update_config,
            "/chat": self.manage_chat,
            "/models": self.list_models,
            "/select_model": self.select_model,
            "/help": self.display_help_message,
        }
        if parts[0] in commands:
            if parts[0] == "/help":
                commands[parts[0]]()  # Call display_help_message without arguments
            else:
                commands[parts[0]](parts)
        else:
            self.display_error(f"Invalid command: {command}")


    def update_config(self, parts):
        if len(parts) == 3:
            key, value = parts[1], parts[2]
            if key in self.config:
                ConfigManager.save_config_value(key, value)
                self.config[key] = value  # Update the local config
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
                self.chat_manager.save_chat_history([])  # Save an empty chat history for new chat
                self.open_chat(filename)
                self.chat_history.append(f"<b style='color: yellow;'>New chat {filename} created and opened.</b>")
            elif action == "save":
                self.chat_manager.chat_filename = filename
                self.chat_manager.save_chat_history(self.conversation_history)
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
        json_files = [f for f in os.listdir(os.getcwd()) if f.endswith('.json')]
        self.chat_history.append("<b style='color: yellow;'>Available chat files:</b>")
        for file in json_files:
            self.chat_history.append(f"<b style='color: green;'>{file}</b>")
        self.chat_history.moveCursor(QTextCursor.End)

    def reset_chat(self):
        self.conversation_history = []
        self.chat_history.clear()
        # Check if the file exists before saving
        chat_history_path = os.path.join(os.getcwd(), self.chat_manager.chat_filename)
        if os.path.exists(chat_history_path):
            self.chat_manager.save_chat_history(self.conversation_history)
            self.chat_history.append(f"<b style='color: yellow;'>Chat history has been reset.</b>")
        else:
            self.chat_history.append(f"<b style='color: yellow;'>Chat history reset but not saved as the file does not exist.</b>")
        
        self.chat_history.moveCursor(QTextCursor.End)

    def open_chat(self, chat_filename):
        self.chat_manager.chat_filename = chat_filename
        self.conversation_history = self.chat_manager.load_chat_history()
        self.chat_history.clear()
        self.load_chat_to_display()
        self.chat_history.append(f"<b style='color: yellow;'>Chat {chat_filename} opened.</b>")
        ConfigManager.save_config_value('current_chat_filename', chat_filename)

    def ensure_json_extension(self, filename):
        if not filename.endswith('.json'):
            filename += '.json'
        return filename

    def update_font_sizes(self):
        self.chat_history.setFont(QFont("Courier New", self.font_size))
        self.user_input.setFont(QFont("Courier New", self.font_size))
        self.prompt_label.setStyleSheet(f"color: {self.config['user_message_color']}; font-size: {self.font_size}px; font-family: Courier New; margin: 0; padding: 0;")

    def send_message(self, user_message):
        user_message_html = markdown.markdown(user_message, extensions=['tables', 'fenced_code'])
        user_message_html = self.apply_custom_css(user_message_html, role="user")
        
        self.chat_history.append(user_message_html)
        self.chat_history.moveCursor(QTextCursor.End)
        
        self.conversation_history.append({"role": "user", "content": user_message})
        self.chat_manager.save_chat_history(self.conversation_history)
        
        full_endpoint = f"{self.config['base_url']}{self.config['ollama_host']}{self.config['path']}"
        if self.selected_model:
            data = {
                "model": self.selected_model,
                "messages": self.conversation_history
            }
        else:
            self.display_error("No model selected. Please select a model using /select_model <model_name>")
            return
        
        self.worker = NetworkWorker(self.conversation_history, full_endpoint, data)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()


    def handle_response(self, response):
        self.conversation_history.append({"role": "assistant", "content": response})
        self.chat_manager.save_chat_history(self.conversation_history)

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
        else:
            super().keyPressEvent(event)

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

    def display_models_list(self):
        if self.available_models:
            self.chat_history.append("<b style='color: yellow;'>Available models:</b>")
            for model in self.available_models:
                self.chat_history.append(f"<b style='color: green;'>/select_model {model['name']}</b>")
            self.chat_history.append("<b style='color: yellow;'>You can copy and paste the above commands to select a model.</b>")
        else:
            self.chat_history.append("<b style='color: yellow;'>No available models found.</b>")
        self.chat_history.moveCursor(QTextCursor.End)

    def list_models(self, parts):
        self.display_models_list()

    def select_model(self, parts):
        if len(parts) == 2:
            model_name = parts[1]
            matching_model = next((model for model in self.available_models if model["name"] == model_name), None)
            if matching_model:
                self.selected_model = model_name
                ConfigManager.save_config_value('selected_model', model_name)
                self.chat_history.append(f"<b style='color: yellow;'>Selected model: {model_name}</b>")
            else:
                self.display_error(f"Model {model_name} not found in the available models.")
        else:
            self.display_error("Usage: /select_model model_name")

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

class ModelSelectionDialog(QMessageBox):
    def __init__(self, models, parent=None):
        super().__init__(parent)
        self.models = models
        self.selected_model = None
        self.setWindowTitle("Select Model")
        self.setText("Please select a model to use:")
        self.setIcon(QMessageBox.Information)

        combo = QComboBox(self)
        for model in models:
            combo.addItem(model["name"])

        self.layout().addWidget(combo, 1, 1)
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.combo = combo

        self.buttonClicked.connect(self.on_button_clicked)

    def on_button_clicked(self, button):
        if button.text() == "OK":
            self.selected_model = self.combo.currentText()

    def get_selected_model(self):
        return self.selected_model

if __name__ == "__main__":
    app = QApplication([])
    chatbox = Chatbox()
    chatbox.show()
    sys.exit(app.exec_())
