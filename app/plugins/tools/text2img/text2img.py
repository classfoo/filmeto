import os

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit
from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.data.timeline import TimelineItem
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget


class Text2Image(BaseTool,BaseTaskWidget):

    def __init__(self, workspace):
        super(Text2Image,self).__init__(workspace)
        self.setObjectName("tool_text_to_image")
        self.workspace = workspace
        self.layout = QVBoxLayout(self)
        self.button = QPushButton("生成")
        self.layout.addWidget(self.button)
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("输入prompt")
        self.prompt.setText("Impressionism style art, painting of attractive angelic young woman with white angel wings, wearing skimpy white ancient greek  short dress with golden accents and belt, holding glowing sword, closeup of upper body, sultry sexy posing ")
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

    def on_timeline_switch(self,item:TimelineItem):
        prompt = item.get_prompt()
        self.prompt.setText(prompt)
        return

    @asyncSlot()
    async def execute(self, task):
        # Only process text2img tasks to avoid conflicts with other tools
        if task.tool != "text2img" and task.tool != "text2image":
            return  # Exit early if this is not a text2img task
        try:
            print(f"Processing text2img task: {task.options}")
            model = ComfyUiModel()
            progress = TaskProgress(task)
            result = await model.text2image(task.options['prompt'],task.path, progress)
            #刷新当前页面显示
            task_result = TaskResult(task, result)
            self.workspace.on_task_finished(task_result)
        except Exception as e:
            print(str(e))

