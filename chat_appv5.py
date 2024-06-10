import os
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QScrollArea, QHBoxLayout, QFrame, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QTextCursor, QFont
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.conversation_history = []  # To store the conversation history
    
    def initUI(self):
        self.setWindowTitle("Chatbox")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                color: #00FF00;
                font-family: 'Courier New', Courier, monospace;
                font-size: 14px;
            }
            QLineEdit {
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
                margin-top: 10px;
            }
            QTextEdit {
                background-color: black;
                color: #00FF00;
                border: none;
                font-family: 'Courier New', Courier, monospace;
            }
            QScrollBar:vertical {
                width: 8px;
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

        # Layouts
        main_layout = QVBoxLayout()
        chat_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        # Chat history with scrollbar
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont('Courier New', 14))

        self.chat_scroll_area = QScrollArea()
        self.chat_scroll_area.setWidgetResizable(True)
        self.chat_scroll_area.setWidget(self.chat_history)
        self.chat_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll_area.setFrameShape(QFrame.NoFrame)
        chat_layout.addWidget(self.chat_scroll_area)

        # User input
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

        # Timer for smooth updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_chat)
        self.timer.start(1000)  # Check for updates every second

    def send_message(self):
        user_message = self.user_input.text()
        if user_message.strip():  # Check if message is not just whitespace
            self.user_input.clear()
            self.chat_history.append(f"<b>You:</b> {user_message}")

            # Append the user message to the conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Prepare the request payload
            data = {
                "model": "gpt-3.5-turbo",
                "messages": self.conversation_history
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            try:
                # Send the request to the specified endpoint
                response = requests.post(
                    "http://127.0.0.1:8080/v1/chat/completions",
                    headers=headers,
                    json=data
                )

                # Check for errors in the response
                if response.status_code != 200:
                    self.chat_history.append(f"<b style='color: red;'>Error:</b> {response.status_code} - {response.text}")
                    response.raise_for_status()

                # Extract the message from the response
                bot_message = response.json()["choices"][0]["message"]["content"].strip()

                # Append the bot's response to the conversation history
                self.conversation_history.append({"role": "assistant", "content": bot_message})
                self.chat_history.append(f"<b>Bot:</b> {bot_message}")

                # Auto-scroll to the latest message
                self.chat_history.moveCursor(QTextCursor.End)

            except requests.RequestException as e:
                self.chat_history.append(f"<b style='color: red;'>Error:</b> {e}")
    
    def update_chat(self):
        # This function can be extended to periodically check for new messages
        # from a server or other updates if needed.
        pass

if __name__ == "__main__":
    app = QApplication([])
    chatbox = Chatbox()
    chatbox.show()
    app.exec_()
