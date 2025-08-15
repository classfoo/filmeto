import os

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit
from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.data.timeline import TimelineItem
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget
from utils.i18n_utils import tr


class ImageEdit(BaseTool, BaseTaskWidget):

    def __init__(self, workspace, editor=None):
        super(ImageEdit, self).__init__(workspace)
        self.setObjectName("tool_image_edit")
        self.workspace = workspace
        # self.layout = QVBoxLayout(self)
        # self.button = QPushButton("编辑图片")
        # self.layout.addWidget(self.button)
        # self.prompt = QTextEdit()
        # self.prompt.setPlaceholderText("输入编辑指令")
        # self.prompt.setText("Enhance the image quality, improve lighting and clarity")
        # self.layout.addWidget(self.prompt)
        #self.button.clicked.connect(self.edit_image)
        self.workspace.connect_task_execute(self.execute)
        self.editor = editor

    def edit_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        timeline_index = self.workspace.get_project().get_timeline_index()
        timeline_item = self.workspace.get_project().get_timeline().get_item(timeline_index)
        input_image_path = timeline_item.get_image_path()
        return {
            "tool": "imgedit",
            "model": "comfy_ui",
            "input_image_path": input_image_path,
            "prompt": self.prompt.toPlainText()
        }

    def on_timeline_switch(self, item: TimelineItem):
        current_tool = item.get_config_value("current_tool")
        if current_tool != self.get_tool_name():
            return
        image_path = item.get_image_path()
        if os.path.exists(image_path) and self.editor:
            self.editor.get_review_widget().switch_file(image_path)

    @classmethod
    def get_tool_name(cls):
        return "imgedit"
    
    @classmethod
    def get_tool_icon(cls):
        return "\ue837"  # Image edit icon
    
    @classmethod
    def get_tool_display_name(cls):
        return tr("Image Edit")
    
    def get_media_path(self, timeline_item):
        """Get media path for image edit tool"""
        return timeline_item.get_image_path()

    @asyncSlot()
    async def execute(self, task):
        # Only process imgedit tasks
        if task.tool != "imgedit":
            return  # Exit early if this is not an imgedit task
        try:
            print(f"Processing imgedit task: {task.options}")
            model = ComfyUiModel()
            progress = TaskProgress(task)
            result = await model.image_edit(task.options['input_image_path'], task.options['prompt'], task.path, progress)
            # 刷新当前页面显示
            task_result = TaskResult(task, result)
            self.workspace.on_task_finished(task_result)
        except Exception as e:
            print(str(e))