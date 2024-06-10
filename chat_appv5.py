import os
import requests
import asyncio
import functools
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel, QHBoxLayout
from PyQt5.QtGui import QFont, QColor

api_key = os.getenv('OPENAI_API_KEY')

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.conversation_history = []  # To store the conversation history
    
    def initUI(self):
        self.setWindowTitle("Chatbox")
        self.setGeometry(100, 100, 600, 700)  # Set a larger initial size

        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Chat history
        self.chat_history = QListWidget()
        layout.addWidget(self.chat_history)
        
        # User input
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message and press Enter...")
        self.user_input.returnPressed.connect(self.send_message)
        layout.addWidget(self.user_input)

        # Set some styles
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                font-family: 'Roboto', sans-serif;
            }
            QLineEdit {
                padding: 15px;
                font-size: 18px;
                border-radius: 25px;
                border: 2px solid #009688;
                background-color: #FFFFFF;
                margin: 10px;
            }
            QListWidget {
                background-color: #FFFFFF;
                border: none;
                padding: 10px;
                border-radius: 15px;
                margin: 10px;
                font-size: 16px;
            }
            QListWidget::item {
                color: #FFFFFF;
            }
            QScrollBar:vertical {
                border: none;
                background: #2E2E2E;
                width: 14px;
                margin: 15px 0 15px 0;
            }
            QScrollBar::handle:vertical {
                background: #606060;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def add_message_to_chat(self, text, sender):
        # Create a widget for the message
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)

        message_label = QLabel(text)
        message_label.setWordWrap(True)

        # Style based on sender
        message_label.setStyleSheet("""
            QLabel {{
                background-color: {};
                padding: 10px;
                border-radius: 10px;
                margin: 5px 20px 5px 5px;
            }}
        """.format('#E0F7FA' if sender == "user" else '#E3F2FD'))

        message_layout.addWidget(message_label)
        item = QListWidgetItem()
        item.setSizeHint(message_widget.sizeHint())
        self.chat_history.addItem(item)
        self.chat_history.setItemWidget(item, message_widget)
        self.chat_history.scrollToBottom()

    def send_message(self):
        user_message = self.user_input.text().strip()
        if not user_message:
            return
        self.user_input.clear()
        self.add_message_to_chat(f"You: {user_message}", "user")
        self.conversation_history.append({"role": "user", "content": user_message})
        QTimer.singleShot(500, functools.partial(self.get_bot_response, user_message))

    async def async_get_bot_response(self, user_message):
        data = {
            "model": "gpt-3.5-turbo",
            "messages": self.conversation_history
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = await asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.post, "http://127.0.0.1:8080/v1/chat/completions", headers=headers, json=data))
        if response.status_code == 200:
            bot_message = response.json()["choices"][0]["message"]["content"].strip()
            self.conversation_history.append({"role": "assistant", "content": bot_message})
            self.add_message_to_chat(f"Bot: {bot_message}", "bot")
        else:
            self.add_message_to_chat(f"Error: {response.status_code} - {response.text}", "bot")

    def get_bot_response(self, user_message):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(self.async_get_bot_response(user_message))
        else:
            loop.run_until_complete(self.async_get_bot_response(user_message))

if __name__ == "__main__":
    app = QApplication([])
    chatbox = Chatbox()
    chatbox.show()
    app.exec_()
