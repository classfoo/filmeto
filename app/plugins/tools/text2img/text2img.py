import os

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit
from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.data.timeline import TimelineItem
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget
from utils.i18n_utils import tr


class Text2Image(BaseTool,BaseTaskWidget):

    def __init__(self, workspace, editor=None):
        super(Text2Image,self).__init__(workspace)
        self.setObjectName("tool_text_to_image")
        self.workspace = workspace
        # self.layout = QVBoxLayout(self)
        # self.button = QPushButton("生成")
        # self.layout.addWidget(self.button)
        # self.prompt = QTextEdit()
        # self.prompt.setPlaceholderText("输入prompt")
        # self.prompt.setText("Impressionism style art, painting of attractive angelic young woman with white angel wings, wearing skimpy white ancient greek  short dress with golden accents and belt, holding glowing sword, closeup of upper body, sultry sexy posing ")
        # self.layout.addWidget(self.prompt)
        # self.button.clicked.connect(self.generate_image)
        self.workspace.connect_task_execute(self.execute)
        self.editor = editor

    def generate_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        return {
            "tool":"text2img",
            "model":"comfy_ui",
            "prompt":self.prompt.toPlainText()
        }

    def on_timeline_switch(self,item:TimelineItem):
        current_tool = item.get_config_value("current_tool")
        if current_tool != self.get_tool_name():
            return
        image_path = item.get_image_path()
        if os.path.exists(image_path) and self.editor:
            self.editor.get_review_widget().load_file(image_path)

    @classmethod
    def get_tool_name(cls):
        return "text2img"
    
    @classmethod
    def get_tool_icon(cls):
        return "\ue82c"  # Text to image icon
    
    @classmethod
    def get_tool_display_name(cls):
        return tr("Text to Image")
    
    def get_media_path(self, timeline_item):
        """Get media path for text2img tool"""
        return timeline_item.get_image_path()
    
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