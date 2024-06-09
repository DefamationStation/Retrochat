import sys
import openai
import threading
from dotenv import load_dotenv
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

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
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
            
            # Initialize the chat completion with streaming
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                stream=True
            )

            response_content = "Assistant: "
            for chunk in completion:
                if 'delta' in chunk.choices[0]:
                    response_part = chunk.choices[0].delta.get('content', '')
                    response_content += response_part
                    # Update the chat area incrementally
                    self.chat_area.setPlainText(response_content)
        except Exception as e:
            self.chat_area.append(f"Error: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chatbox = Chatbox()
    chatbox.resize(400, 300)
    chatbox.show()
    sys.exit(app.exec_())
