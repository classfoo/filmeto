import os

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit
from qasync import asyncSlot

from app.plugins.models.bailian.bailian_model import BaiLianModel
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
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
        self.workspace.task_manager.task_execute.connect(self.execute)

    def generate_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        return {
            "type":"text2img",
            "prompt":self.prompt.toPlainText()
        }

    @asyncSlot()
    async def execute(self, task):
        print(task.options)
        model = ComfyUiModel()
        await model.text2img(task.options['prompt'],os.path.join(task.path,"result.png"))
        return
