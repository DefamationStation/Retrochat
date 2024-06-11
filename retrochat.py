import sys
import os
import json
import requests
import markdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QTextCursor, QFont

DEFAULT_CHAT_FILENAME = "chat_1.json"  # Default chat file
CONFIG_FILENAME = "config.json"
DEFAULT_CONFIG = {
    "base_url": "http://",
    "host": "127.0.0.1:8080",
    "path": "/v1/chat/completions",
    "user_message_color": "#00FF00",
    "assistant_message_color": "#FFBF00",
    "font_size": 20
}

def load_or_create_config():
    config_path = os.path.join(os.getcwd(), CONFIG_FILENAME)
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w') as config_file:
                json.dump(DEFAULT_CONFIG, config_file, indent=4)
            print(f"Config file created with default settings at {config_path}")
        except Exception as e:
            print(f"Error creating config file: {e}")
            return DEFAULT_CONFIG
    else:
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
            print(f"Config file loaded from {config_path}")
            return config
        except json.JSONDecodeError as e:
            print(f"Error reading config file: {e}")
            return DEFAULT_CONFIG
        except Exception as e:
            print(f"Unexpected error: {e}")
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    config_path = os.path.join(os.getcwd(), CONFIG_FILENAME)
    try:
        with open(config_path, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        print(f"Config file updated at {config_path}")
    except Exception as e:
        print(f"Error saving config file: {e}")

def save_chat_history(chat_filename, chat_history):
    chat_history_path = os.path.join(os.getcwd(), chat_filename)
    try:
        with open(chat_history_path, 'w') as chat_history_file:
            json.dump(chat_history, chat_history_file, indent=4)
        print(f"Chat history saved at {chat_history_path}")
    except Exception as e:
        print(f"Error saving chat history: {e}")

def load_chat_history(chat_filename):
    chat_history_path = os.path.join(os.getcwd(), chat_filename)
    if os.path.exists(chat_history_path):
        try:
            with open(chat_history_path, 'r') as chat_history_file:
                chat_history = json.load(chat_history_file)
            print(f"Chat history loaded from {chat_history_path}")
            return chat_history
        except json.JSONDecodeError as e:
            print(f"Error reading chat history file: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    return []

def delete_chat_file(chat_filename):
    chat_history_path = os.path.join(os.getcwd(), chat_filename)
    if os.path.exists(chat_history_path):
        try:
            os.remove(chat_history_path)
            print(f"Chat file {chat_history_path} deleted.")
        except Exception as e:
            print(f"Error deleting chat file: {e}")
    else:
        print(f"Chat file {chat_history_path} does not exist.")

def rename_chat_file(old_name, new_name):
    old_path = os.path.join(os.getcwd(), old_name)
    new_path = os.path.join(os.getcwd(), new_name)
    if os.path.exists(old_path):
        try:
            os.rename(old_path, new_path)
            print(f"Renamed chat file from {old_path} to {new_path}.")
        except Exception as e:
            print(f"Error renaming chat file: {e}")
    else:
        print(f"Chat file {old_path} does not exist.")

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

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_or_create_config()
        self.font_size = self.config.get("font_size", 14)  # Get the font size from config
        self.chat_filename = DEFAULT_CHAT_FILENAME
        self.initUI()
        self.conversation_history = load_chat_history(self.chat_filename)  # Load the conversation history from file
        self.command_history = []  # List to store commands
        self.command_index = -1  # Index to track command history navigation
        self.is_moving = False
        self.startPos = QPoint(0, 0)
        self.right_button_pressed = False
        self.oldPos = QPoint(0, 0)
        self.resizing = False  # To track if the window is being resized
        self.resize_direction = None  # To track the direction of resizing

        # Load chat history into the display
        self.load_chat_to_display()

    def initUI(self):
        self.setWindowTitle("Retrochat")
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
        self.chat_history.setStyleSheet(f"padding: 10px; background-color: #000000; color: {self.config['user_message_color']};")

        self.chat_scroll_area = QScrollArea()
        self.chat_scroll_area.setWidgetResizable(True)
        self.chat_scroll_area.setWidget(self.chat_history)
        self.chat_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll_area.setFrameShape(QFrame.NoFrame)
        chat_layout.addWidget(self.chat_scroll_area)

        self.prompt_label = QLabel(">")
        self.prompt_label.setStyleSheet(f"color: {self.config['user_message_color']}; font-size: {self.font_size}px; font-family: Courier New; margin: 0; padding: 0;")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message here...")
        self.user_input.returnPressed.connect(self.process_input)
        self.user_input.setFont(QFont("Courier New", self.font_size))
        self.user_input.setStyleSheet(f"margin: 0; padding: 0; background-color: #000000; color: {self.config['user_message_color']}; border: none;")

        input_layout.addWidget(self.prompt_label, 0, Qt.AlignLeft)
        input_layout.addWidget(self.user_input, 1)

        main_layout.addLayout(chat_layout)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: black;
                color: #00FF00;
                font-family: 'Courier New', Courier, monospace;
                font-size: {self.font_size}px;
            }}
            QLineEdit {{
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
                margin-top: 13px;
            }}
            QTextEdit {{
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
            }}
            QScrollBar:vertical {{
                width: 4px;
                background: black;
                margin: 0;
                border: 1px solid #00FF00;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #00FF00;
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

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

    def process_input(self):
        user_message = self.user_input.text()
        if user_message.strip():
            if user_message.startswith("/"):
                self.apply_command(user_message)
                self.command_history.append(user_message)  # Add command to history
                self.command_index = -1  # Reset the command index after a new command is entered
            else:
                self.send_message(user_message)
            self.user_input.clear()

    def apply_command(self, command):
        parts = command.split(maxsplit=3)  # Use maxsplit to ensure we capture the entire value part as a single string

        if len(parts) == 3 and parts[0] == "/config":
            key, value = parts[1], parts[2]
            if key in self.config:
                current_value = self.config[key]
                if isinstance(current_value, int):
                    try:
                        value = int(value)
                    except ValueError:
                        self.chat_history.append(f"<b style='color: red;'>Invalid value for {key}: must be an integer</b>")
                        self.chat_history.moveCursor(QTextCursor.End)
                        return
                elif isinstance(current_value, float):
                    try:
                        value = float(value)
                    except ValueError:
                        self.chat_history.append(f"<b style='color: red;'>Invalid value for {key}: must be a float</b>")
                        self.chat_history.moveCursor(QTextCursor.End)
                        return
                self.config[key] = value
                save_config(self.config)
                self.chat_history.append(f"<b style='color: yellow;'>Configuration updated: {key} = {value}</b>")
                if key == "font_size":
                    self.font_size = value
                    self.update_font_sizes()
            else:
                self.chat_history.append(f"<b style='color: red;'>Invalid configuration key: {key}</b>")

        elif parts[0] == "/chat":
            if parts[1] == "save" and len(parts) == 3:
                self.chat_filename = parts[2]
                save_chat_history(self.chat_filename, self.conversation_history)
                self.chat_history.append(f"<b style='color: yellow;'>Chat saved as {self.chat_filename}.</b>")
            elif parts[1] == "delete" and len(parts) == 3:
                delete_chat_file(parts[2])
                if parts[2] == self.chat_filename:
                    self.reset_chat()
                self.chat_history.append(f"<b style='color: yellow;'>Chat file {parts[2]} deleted.</b>")
            elif parts[1] == "reset" and len(parts) == 2:
                self.reset_chat()
            elif parts[1] == "rename" and len(parts) == 4:
                old_name, new_name = parts[2], parts[3]
                rename_chat_file(old_name, new_name)
                if old_name == self.chat_filename:
                    self.chat_filename = new_name
                    self.open_chat(new_name)
                self.chat_history.append(f"<b style='color: yellow;'>Chat file {old_name} renamed to {new_name}.</b>")
            elif parts[1] == "open" and len(parts) == 3:
                new_chat_filename = parts[2]
                self.open_chat(new_chat_filename)
            else:
                self.chat_history.append(f"<b style='color: red;'>Invalid chat command: {command}</b>")
        else:
            self.chat_history.append(f"<b style='color: red;'>Invalid command: {command}</b>")
        self.chat_history.moveCursor(QTextCursor.End)

    def open_chat(self, chat_filename):
        """Open a specified chat file and load its history."""
        self.chat_filename = chat_filename
        self.conversation_history = load_chat_history(chat_filename)
        self.chat_history.clear()
        self.load_chat_to_display()
        self.chat_history.append(f"<b style='color: yellow;'>Chat {chat_filename} opened.</b>")

    def reset_chat(self):
        """Clear the current chat history."""
        self.conversation_history = []
        self.chat_history.clear()
        save_chat_history(self.chat_filename, self.conversation_history)
        self.chat_history.append(f"<b style='color: yellow;'>Chat history has been reset.</b>")


    def update_font_sizes(self):
        self.chat_history.setFont(QFont("Courier New", self.font_size))
        self.user_input.setFont(QFont("Courier New", self.font_size))
        self.prompt_label.setStyleSheet(f"color: {self.config['user_message_color']}; font-size: {self.font_size}px; font-family: Courier New; margin: 0; padding: 0;")

        self.setStyleSheet(f"""
            QWidget {{
                background-color: black;
                color: #00FF00;
                font-family: 'Courier New', Courier, monospace;
                font-size: {self.font_size}px;
            }}
            QLineEdit {{
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
                margin-top: 13px;
            }}
            QTextEdit {{
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
            }}
            QScrollBar:vertical {{
                width: 4px;
                background: black;
                margin: 0;
                border: 1px solid #00FF00;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #00FF00;
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

    def send_message(self, user_message):
        user_message_html = markdown.markdown(user_message, extensions=['tables', 'fenced_code'])
        user_message_html = self.apply_custom_css(user_message_html, role="user")
        self.chat_history.append(user_message_html)

        self.conversation_history.append({"role": "user", "content": user_message})
        save_chat_history(self.chat_filename, self.conversation_history)

        full_endpoint = f"{self.config['base_url']}{self.config['host']}{self.config['path']}"
        self.worker = NetworkWorker(self.conversation_history, full_endpoint)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def handle_response(self, response):
        self.conversation_history.append({"role": "assistant", "content": response})
        save_chat_history(self.chat_filename, self.conversation_history)

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
                if self.command_index == -1:  # First time pressing up, start from the last command
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
                    self.command_index = -1  # Reset to the initial state
        else:
            super().keyPressEvent(event)  # Handle other keys normally

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
        margin = 10  # Sensitivity for border resizing
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

class NetworkWorker(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversation_history, endpoint):
        super().__init__()
        self.conversation_history = conversation_history
        self.endpoint = endpoint

    def run(self):
        data = {
            "model": "gpt-3.5-turbo",
            "messages": self.conversation_history
        }
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                error_message = f"{response.status_code} - {response.text}"
                self.error_occurred.emit(error_message)
                return

            bot_message = response.json()["choices"][0]["message"]["content"].strip()
            self.response_received.emit(bot_message)

        except requests.RequestException as e:
            self.error_occurred.emit(str(e))

if __name__ == "__main__":
    app = QApplication([])
    chatbox = Chatbox()
    chatbox.show()
    sys.exit(app.exec_())
