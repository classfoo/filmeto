from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget
from utils.i18n_utils import tr


class Text2Image(BaseTool,BaseTaskWidget):

    def __init__(self, workspace, editor=None):
        super(Text2Image,self).__init__(workspace)
        self.setObjectName("tool_text_to_image")
        self.workspace = workspace
        self.workspace.connect_task_execute(self.execute)
        self.editor = editor
        self.reference_image_path = None

    def generate_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        return {
            "tool":"text2img",
            "model":"comfy_ui",
            "prompt":self.editor.get_prompt(),
            "reference_image_path": self.reference_image_path
        }

    def init_ui(self, canvas_editor):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(6)
        title = QLabel(tr("Reference Image"))
        layout.addWidget(title)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.setSpacing(4)
        path_edit = QLineEdit()
        path_edit.setReadOnly(True)
        browse_btn = QPushButton(tr("Browse"))
        def on_browse():
            file_path, _ = QFileDialog.getOpenFileName(panel, tr("Select Reference Image"), "", "Images (*.png *.jpg *.jpeg)")
            if file_path:
                self.reference_image_path = file_path
                path_edit.setText(file_path)
        browse_btn.clicked.connect(on_browse)
        row_layout.addWidget(path_edit, 1)
        row_layout.addWidget(browse_btn)
        layout.addWidget(row)
        canvas_editor.set_tool_panel(panel)

    @classmethod
    def get_tool_name(cls):
        return "text2img"
    
    @classmethod
    def get_tool_icon(cls):
        return "\ue60b"  # Text to image icon from iconfont.json
    
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