import sys
import os
import json
import threading
import requests
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Ensure the API key is set
if not api_key:
    print("Error: OPENAI_API_KEY is not set in the .env file.")
    sys.exit(1)

class Chatbox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('OpenAI Chatbox')
        
        self.layout = QVBoxLayout()
        
        self.chat_area = QTextEdit(self)
        self.chat_area.setReadOnly(True)
        self.layout.addWidget(self.chat_area)
        
        self.input_area = QHBoxLayout()
        
        self.input_field = QLineEdit(self)
        self.input_field.returnPressed.connect(self.sendMessage)
        self.input_area.addWidget(self.input_field)
        
        self.send_button = QPushButton('Send', self)
        self.send_button.clicked.connect(self.sendMessage)
        self.input_area.addWidget(self.send_button)
        
        self.layout.addLayout(self.input_area)
        
        self.setLayout(self.layout)
        
    def sendMessage(self):
        user_message = self.input_field.text().strip()
        if not user_message:
            return
        
        self.chat_area.append(f'User: {user_message}')
        self.input_field.clear()

        # Send user message to OpenAI and get response in a new thread
        threading.Thread(target=self.getOpenAIResponse, args=(user_message,)).start()

    def getOpenAIResponse(self, user_message):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 1500,
            "temperature": 1,
        }

        try:
            response = requests.post(
                "http://127.0.0.1:8080/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                self.updateChatArea(f"Error: {response.status_code} - {response.text}")
                response.raise_for_status()

            # Extract and display the message content
            message = response.json()["choices"][0]["message"]["content"].strip()
            message = self.trimResponse(message)
            self.updateChatArea(f"Assistant: {message}")

        except Exception as e:
            self.updateChatArea(f"Error: {str(e)}")

    def trimResponse(self, message):
        # Define possible tokens or extraneous text to trim from the message
        end_tokens = ["<|endoftext|>", "stop", "END", "[END]"]
        for token in end_tokens:
            if message.endswith(token):
                message = message[:-len(token)].strip()
        return message

    def updateChatArea(self, text):
        # Safely update the chat area from a different thread using invokeMethod
        QMetaObject.invokeMethod(self.chat_area, "append", Qt.QueuedConnection, Q_ARG(str, text))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chatbox = Chatbox()
    chatbox.resize(400, 300)
    chatbox.show()
    sys.exit(app.exec_())
