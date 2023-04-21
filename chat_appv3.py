import sys
import os
import json
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from threading import Thread

# Function to read the config file
def read_config():
    if getattr(sys, 'frozen', False):
        # The application is running as a bundled executable
        script_directory = sys._MEIPASS
    else:
        # The application is running as a script
        script_directory = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(script_directory, 'config.json')
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
    return config_data

config = read_config()
OPENAI_API_KEY = config['OPENAI_API_KEY']

class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Chat with OpenAI')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #2c2c2c;")

        layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("QTextEdit {background-color: #2c2c2c; color: white; font: 30px Arial; border: none;}")
        layout.addWidget(self.chat_display)

        self.user_input = QLineEdit()
        self.user_input.setStyleSheet("QLineEdit {background-color: #3c3c3c; color: white; font: 30px Arial; border: none; padding: 5px;}")
        layout.addWidget(self.user_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("QPushButton {background-color: #4c4c4c; color: white; font: bold 25px 'Segoe UI'; padding: 5px; border: none;} QPushButton:hover {background-color: #5c5c5c;}")
        layout.addWidget(self.send_button)

        # Connect the returnPressed signal to the send_message method
        self.user_input.returnPressed.connect(self.send_message)

        self.setLayout(layout)

    def send_message(self):
        user_input = self.user_input.text()
        if user_input.lower() not in ["quit", "exit"]:
            self.chat_display.append(f"<font color='white'>User:</font> {user_input}")
            self.user_input.clear()

            thread = Thread(target=self.get_ai_response, args=(user_input,))
            thread.start()

    def get_ai_response(self, user_input):
        ai_response = self.chat_with_openai(user_input)
        self.chat_display.append(f"<font color='cyan'>AI:</font> {ai_response}")

    def chat_with_openai(self, user_input):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": user_input}],
            "max_tokens": 1500,
            "temperature": 1,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
        )

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            response.raise_for_status()

        message = response.json()["choices"][0]["message"]["content"].strip()
        return message

def run_app():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
