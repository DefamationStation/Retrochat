import os
import sys
import requests
import asyncio
from functools import partial
from dotenv import load_dotenv
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QScrollArea, QLabel, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QPalette, QColor

# Load the API key from .env file
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.conversation_history = []  # To store the conversation history
    
    def initUI(self):
        self.setWindowTitle("Chatbox")
        self.setGeometry(100, 100, 600, 700)  # Set a larger initial size

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Scrollable chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # User input layout
        input_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message and press Enter...")
        self.user_input.setFont(QFont('Arial', 14))
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        main_layout.addLayout(input_layout)

        # Add a spacer to keep messages at the top
        self.scroll_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Set some styles
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: 'Arial', sans-serif;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #009688;
                border-radius: 5px;
                background-color: #ffffff;
                font-size: 14px;
                margin-right: 10px;
            }
            QPushButton {
                padding: 10px 20px;
                background-color: #009688;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #00796B;
            }
            QLabel {
                background-color: #E0F7FA;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
                font-size: 14px;
            }
            QLabel.bot {
                background-color: #E3F2FD;
            }
        """)

    def add_message_to_chat(self, text, sender):
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setFont(QFont('Arial', 12))
        message_label.setStyleSheet("QLabel { background-color: #E0F7FA; padding: 10px; border-radius: 5px; margin: 5px 0; }")
        
        if sender == "bot":
            message_label.setStyleSheet("QLabel { background-color: #E3F2FD; padding: 10px; border-radius: 5px; margin: 5px 0; }")

        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, message_label)
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def send_message(self):
        user_message = self.user_input.text().strip()
        if not user_message:
            return
        self.user_input.clear()
        self.add_message_to_chat(f"You: {user_message}", "user")
        self.conversation_history.append({"role": "user", "content": user_message})
        QTimer.singleShot(500, partial(self.get_bot_response, user_message))

    async def async_get_bot_response(self, user_message):
        data = {
            "model": "gpt-3.5-turbo",
            "messages": self.conversation_history
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = await asyncio.get_event_loop().run_in_executor(None, partial(requests.post, "http://127.0.0.1:8080/v1/chat/completions", headers=headers, json=data))
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
    sys.exit(app.exec_())
