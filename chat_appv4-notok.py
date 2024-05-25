import sys
import os
import json
import requests
import markdown
from threading import Thread
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui import QTextCursor

# Function to read the config file
def read_config():
    if getattr(sys, 'frozen', False):
        script_directory = os.path.dirname(sys.executable)
    else:
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
        self.current_ai_message = ""  # Initialize buffer for AI message
        self.is_ai_response = False  # Track if AI is responding

    def init_ui(self):
        self.setWindowTitle('Chat with OpenAI')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #2c2c2c;")
        layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("QTextEdit {background-color: #2c2c2c; color: white; font: 20px Arial; border: none;}")
        layout.addWidget(self.chat_display)
        self.user_input = QLineEdit()
        self.user_input.setStyleSheet("QLineEdit {background-color: #3c3c3c; color: white; font: 20px Arial; border: none; padding: 5px;}")
        layout.addWidget(self.user_input)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("QPushButton {background-color: #4c4c4c; color: white; font: bold 25px 'Segoe UI'; padding: 5px; border: none;} QPushButton:hover {background-color: #5c5c5c;}")
        layout.addWidget(self.send_button)
        self.user_input.returnPressed.connect(self.send_message)
        self.setLayout(layout)

    def send_message(self):
        user_input = self.user_input.text()
        if user_input.lower() not in ["quit", "exit"]:
            self.is_ai_response = False
            self.append_chat_display(f"<font color='white'>User:</font> {user_input}")
            self.user_input.clear()
            thread = Thread(target=self.get_ai_response, args=(user_input,))
            thread.start()

    def get_ai_response(self, user_input):
        self.current_ai_message = ""  # Reset buffer for new AI message
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": user_input}],
            "temperature": 0,
            "stream": True
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, stream=True)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            QMetaObject.invokeMethod(self, "append_chat_display", Qt.QueuedConnection, Q_ARG(str, f"<font color='red'>Error: {response.status_code} - {response.text}</font>"))
            return

        try:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith("data: "):
                        line_str = line_str[len("data: "):]
                    if line_str == "[DONE]":
                        break
                    try:
                        decoded_line = json.loads(line_str)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e} - Line: {line_str}")
                        continue
                    if 'choices' in decoded_line:
                        choice = decoded_line['choices'][0]
                        if 'delta' in choice and 'content' in choice['delta']:
                            content = choice['delta']['content']
                            self.current_ai_message += content  # Append new content to the current message
                            self.is_ai_response = True
                            QMetaObject.invokeMethod(self, "update_last_ai_message", Qt.QueuedConnection, Q_ARG(str, self.current_ai_message))
        except Exception as e:
            print(f"Unhandled exception: {e}")
            QMetaObject.invokeMethod(self, "append_chat_display", Qt.QueuedConnection, Q_ARG(str, "<font color='red'>Error: Unhandled exception.</font>"))

    @pyqtSlot(str)
    def update_last_ai_message(self, ai_response):
        if self.is_ai_response:
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            if not self.chat_display.toPlainText().endswith('\n'):
                cursor.insertBlock()
            if not cursor.block().text().startswith("AI:"):
                cursor.insertHtml("<font color='cyan'>AI:</font> ")
                cursor.insertText(ai_response)
            else:
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.insertHtml(f"<font color='cyan'>AI:</font> {ai_response}")
            self.chat_display.moveCursor(QTextCursor.End)

    @pyqtSlot(str)
    def append_chat_display(self, message):
        self.chat_display.append(message)
        self.chat_display.moveCursor(QTextCursor.End)

def run_app():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
