import os
import traceback

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit
from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.data.timeline import TimelineItem
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget


class Image2Video(BaseTool,BaseTaskWidget):

    def __init__(self, workspace):
        super(Image2Video,self).__init__(workspace)
        self.setObjectName("tool_text_to_image")
        self.workspace = workspace
        self.layout = QVBoxLayout(self)
        self.button = QPushButton("Img2Video")
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
        timeline_index = self.workspace.get_project().get_timeline_index()
        timeline_item = self.workspace.get_project().get_timeline().get_item(timeline_index)
        input_image_path = timeline_item.get_image_path()
        return {
            "tool":"img2video",
            "model":"comfy_ui",
            "input_image_path":input_image_path,
            "prompt":self.prompt.toPlainText()
        }

    def on_timeline_switch(self,item:TimelineItem):
        prompt = item.get_prompt()
        self.prompt.setText(prompt)
        return

    @asyncSlot()
    async def execute(self, task):
        # Only process img2video tasks to avoid conflicts with other tools
        if task.tool != "img2video" and task.tool != "image2video":
            return  # Exit early if this is not an img2video task
            
        try:
            print(f"Processing img2video task: {task.options}")
            model = ComfyUiModel()
            progress = TaskProgress(task)
            result = await model.image2video(task.options['input_image_path'], task.options['prompt'],task.path, progress)
            #刷新当前页面显示
            task_result = TaskResult(task, result)
            self.workspace.on_task_finished(task_result)
        except Exception as e:
            print(str(e))
            traceback.print_exc()

