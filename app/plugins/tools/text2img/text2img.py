import os

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit
from qasync import asyncSlot

from app.data.task import TaskResult
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool


class Text2Image(BaseTool):

    def __init__(self, workspace):
        super(Text2Image,self).__init__(workspace)
        self.setObjectName("tool_text_to_image")
        self.workspace = workspace
        self.layout = QVBoxLayout(self)
        self.button = QPushButton("生成")
        self.layout.addWidget(self.button)
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("输入prompt")
        self.prompt.setText("一个比基尼模特，车展")
        self.layout.addWidget(self.prompt)
        self.button.clicked.connect(self.generate_image)
        self.workspace.connect_task_execute(self.execute)

    def generate_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        return {
            "tool":"text2img",
            "model":"comfy_ui",
            "prompt":self.prompt.toPlainText()
        }

    def onProgress(self, percent:int):
        self.percent = percent
        #刷新进度
        return

    @asyncSlot()
    async def execute(self, task):
        print(task.options)
        model = ComfyUiModel()
        result = await model.text2image(task.options['prompt'],task.path, self)
        #刷新当前页面显示
        task_result = TaskResult(task, result)
        self.workspace.on_task_finished(task_result)