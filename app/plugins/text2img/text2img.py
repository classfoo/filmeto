from PySide6.QtGui import QTextFrame
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit, QMessageBox

from app.ui.base_widget import BaseWidget


class Text2Image(BaseWidget):

    def __init__(self, window,workspace):
        super(Text2Image,self).__init__()
        self.setObjectName("tool_text_to_image")
        self.window = window
        self.workspace = workspace
        self.layout = QVBoxLayout(self)
        self.button = QPushButton("生成")
        self.layout.addWidget(self.button)
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("输入prompt")
        self.prompt.setText("一个比基尼模特，车展")
        self.layout.addWidget(self.prompt)
        self.button.clicked.connect(self.generate_image)

    def generate_image(self):
        self.workspace.submit_task(self.params())
        self.execute(self.params())

    def params(self):
        return {
            "prompt":self.prompt.toPlainText()
        }

    def execute(self):

        return
