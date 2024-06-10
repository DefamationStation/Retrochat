import sys
import requests
import markdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QTextCursor, QFont

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #333333; color: #00FF00;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # commented out the title_label related lines
        # self.title_label = QLabel(self.parent.windowTitle())
        # self.title_label.setStyleSheet("margin-left: 10px; font-size: 14px; font-family: 'Courier New', Courier, monospace;")
        # self.title_label.setAlignment(Qt.AlignCenter)
        
        self.minimize_button = QPushButton("-")
        self.minimize_button.clicked.connect(self.parent.showMinimized)
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("background-color: black; color: #00FF00;")

        self.close_button = QPushButton("x")
        self.close_button.clicked.connect(self.parent.close)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("background-color: black; color: #00FF00;")

        # commented out the title_label related line
        # layout.addWidget(self.title_label)
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
        self.initUI()
        self.conversation_history = []
        self.is_moving = False
        self.startPos = QPoint(0, 0)
        self.right_button_pressed = False  # Initialize the attribute
        self.oldPos = QPoint(0, 0)         # Initialize the attribute

    def initUI(self):
        self.setWindowTitle("Retrochat")
        self.setGeometry(300, 300, 1100, 550)
        self.setWindowFlags(Qt.FramelessWindowHint)

        main_layout = QVBoxLayout()
        chat_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        self.custom_title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.custom_title_bar)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont('Courier New', 14))
        self.chat_history.setStyleSheet("padding: 10px; background-color: black; color: #00FF00;")

        self.chat_scroll_area = QScrollArea()
        self.chat_scroll_area.setWidgetResizable(True)
        self.chat_scroll_area.setWidget(self.chat_history)
        self.chat_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll_area.setFrameShape(QFrame.NoFrame)
        chat_layout.addWidget(self.chat_scroll_area)

        self.prompt_label = QLabel(">")
        self.prompt_label.setStyleSheet("color: #00FF00; font-size: 14px; font-family: 'Courier New', Courier, monospace; margin: 0; padding: 0;")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message here...")
        self.user_input.returnPressed.connect(self.send_message)
        self.user_input.setFont(QFont('Courier New', 14))
        self.user_input.setStyleSheet("margin: 0; padding: 0; background-color: black; color: #00FF00; border: none;")

        input_layout.addWidget(self.prompt_label, 0, Qt.AlignLeft)
        input_layout.addWidget(self.user_input, 1)

        main_layout.addLayout(chat_layout)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                color: #00FF00;
                font-family: 'Courier New', Courier, monospace;
                font-size: 16px;
            }
            QLineEdit {
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
                margin-top: 13px;
            }
            QTextEdit {
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
            }
            QScrollBar:vertical {
                width: 4px;
                background: black;
                margin: 0;
                border: 1px solid #00FF00;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #00FF00;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def send_message(self):
        user_message = self.user_input.text()
        if user_message.strip():
            self.user_input.clear()
            
            user_message_html = markdown.markdown(user_message, extensions=['tables', 'fenced_code'])
            user_message_html = self.apply_custom_css(user_message_html, role="user")
            self.chat_history.append(user_message_html)

            self.conversation_history.append({"role": "user", "content": user_message})

            self.worker = NetworkWorker(self.conversation_history)
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
            custom_css = """
            <style>
                div.user-message {
                    color: #00FF00; /* Green for user */
                    font-family: 'Courier New', Courier, monospace;
                    background-color: black;
                    margin: 0; /* No margin to remove extra space */
                    padding: 2px 0; /* Less padding to tighten spacing */
                }
                pre, code {
                    background-color: #333333;
                    color: #00FF00;
                    border-radius: 4px;
                    padding: 5px;
                    margin: 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid #00FF00;
                    padding: 3px;
                }
                blockquote {
                    border-left: 4px solid #00FF00;
                    margin: 5px 0;
                    padding-left: 10px;
                    color: #00FF00;
                    background-color: #222222;
                }
            </style>
            """
            return f"{custom_css}<div class='user-message'>{html_content}</div>"
        else:
            custom_css = """
            <style>
                div.bot-message {
                    color: #FFBF00; /* Amber for bot */
                    font-family: 'Courier New', Courier, monospace;
                    background-color: black;
                    margin: 0; /* No margin to remove extra space */
                    padding: 2px 0; /* Less padding to tighten spacing */
                }
                pre, code {
                    background-color: #333333;
                    color: #FFBF00;
                    border-radius: 4px;
                    padding: 5px;
                    margin: 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse.
                }
                th, td {
                    border: 1px solid #FFBF00;
                    padding: 3px;
                }
                blockquote {
                    border-left: 4px solid #FFBF00;
                    margin: 5px 0;
                    padding-left: 10px;
                    color: #FFBF00;
                    background-color: #222222;
                }
            </style>
            """
            return f"{custom_css}<div class='bot-message'>{html_content}</div>"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_moving = True
            self.startPos = event.globalPos()
        elif event.button() == Qt.RightButton:
            self.right_button_pressed = True
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.is_moving:
            delta = QPoint(event.globalPos() - self.startPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.startPos = event.globalPos()
        elif self.right_button_pressed:
            self.handle_resize(event)

    def mouseReleaseEvent(self, event):
        self.is_moving = False
        self.right_button_pressed = False

    def handle_resize(self, event):
        if self.right_button_pressed:
            diff = event.globalPos() - self.oldPos
            self.resize(self.width() + diff.x(), self.height() + diff.y())
            self.oldPos = event.globalPos()

class NetworkWorker(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversation_history):
        super().__init__()
        self.conversation_history = conversation_history

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
                "http://127.0.0.1:8080/v1/chat/completions",
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
