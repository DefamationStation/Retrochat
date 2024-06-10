import os
import requests  # Import requests library
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
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
        self.setGeometry(100, 100, 400, 500)

        # Layout
        layout = QVBoxLayout()

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        # User input
        self.user_input = QLineEdit()
        self.user_input.returnPressed.connect(self.send_message)
        layout.addWidget(self.user_input)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

    def send_message(self):
        user_message = self.user_input.text()
        self.user_input.clear()
        self.chat_history.append(f"You: {user_message}")

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
                self.chat_history.append(f"Error: {response.status_code} - {response.text}")
                response.raise_for_status()

            # Extract the message from the response
            bot_message = response.json()["choices"][0]["message"]["content"].strip()

            # Append the bot's response to the conversation history
            self.conversation_history.append({"role": "assistant", "content": bot_message})
            self.chat_history.append(f"Bot: {bot_message}")

        except requests.RequestException as e:
            self.chat_history.append(f"Error: {e}")

if __name__ == "__main__":
    app = QApplication([])
    chatbox = Chatbox()
    chatbox.show()
    app.exec_()
