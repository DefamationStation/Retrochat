import requests
import markdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor, QFont

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.conversation_history = []

    def initUI(self):
        self.setWindowTitle("Chatbox")
        self.setGeometry(100, 100, 600, 500)
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

        main_layout = QVBoxLayout()
        chat_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont('Courier New', 14))
        self.chat_history.setStyleSheet("padding: 10px;")

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
        self.user_input.setStyleSheet("margin: 0; padding: 0;")

        input_layout.addWidget(self.prompt_label, 0, Qt.AlignLeft)
        input_layout.addWidget(self.user_input, 1)

        main_layout.addLayout(chat_layout)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

    def send_message(self):
        user_message = self.user_input.text()
        if user_message.strip():
            self.user_input.clear()
            
            # Convert user message to HTML using Markdown and apply custom CSS
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

        # Convert response to HTML using Markdown and apply custom CSS
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
                    margin: 0;
                    padding: 5px 0;
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
                    margin: 0;
                    padding: 5px 0;
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
                    border-collapse: collapse;
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
    app.exec_()
