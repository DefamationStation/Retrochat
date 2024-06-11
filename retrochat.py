import sys
import os
import json
import requests
import markdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QTextCursor, QFont

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

        self.close_button = QPushButton("x")
        self.close_button.clicked.connect(self.parent.close)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("background-color: black; color: #00FF00; font-size: {}px;".format(self.font_size))

        layout.addStretch()
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)

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
        self.initUI()
        self.conversation_history = []
        self.is_moving = False
        self.startPos = QPoint(0, 0)
        self.right_button_pressed = False
        self.oldPos = QPoint(0, 0)
        self.resizing = False  # To track if the window is being resized
        self.resize_direction = None  # To track the direction of resizing

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

    def process_input(self):
        user_message = self.user_input.text()
        if user_message.strip():
            if user_message.startswith("/"):
                self.apply_command(user_message)
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

                # Update the configuration
                self.config[key] = value
                save_config(self.config)
                self.chat_history.append(f"<b style='color: yellow;'>Configuration updated: {key} = {value}</b>")
                
                # Apply the new font size if it's changed
                if key == "font_size":
                    self.font_size = value
                    self.update_font_sizes()

            else:
                self.chat_history.append(f"<b style='color: red;'>Invalid configuration key: {key}</b>")
        else:
            self.chat_history.append(f"<b style='color: red;'>Invalid command: {command}</b>")
        self.chat_history.moveCursor(QTextCursor.End)

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

        full_endpoint = f"{self.config['base_url']}{self.config['host']}{self.config['path']}"
        self.worker = NetworkWorker(self.conversation_history, full_endpoint)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def handle_response(self, response):
        self.conversation_history.append({"role": "assistant", "content": response})

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
