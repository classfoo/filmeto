from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget
from app.ui.media_selector.media_selector import MediaSelector
from utils.i18n_utils import tr
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ImageEdit(BaseTool, BaseTaskWidget):

    def __init__(self, workspace, editor=None):
        super(ImageEdit, self).__init__(workspace)
        self.setObjectName("tool_image_edit")
        self.workspace = workspace
        self.workspace.connect_task_execute(self.execute)
        self.editor = editor
        self.input_image_path = None
        self.media_selector = None

    def init_ui(self, main_editor):
        """Initialize the UI for the image edit tool"""
        # Create widget for tool configuration
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create media selector for input image
        self.media_selector = MediaSelector()
        # Set supported types to image formats only
        self.media_selector.set_supported_types(['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'])
        
        # Set initial value if exists
        timeline_index = self.workspace.get_project().get_timeline_index()
        timeline_item = self.workspace.get_project().get_timeline().get_item(timeline_index)
        current_image_path = timeline_item.get_image_path()
        if current_image_path:
            self.media_selector.set_value(current_image_path)
            self.input_image_path = current_image_path
            
        # Connect signal
        self.media_selector.file_selected.connect(self._on_image_selected)
        self.media_selector.file_cleared.connect(self._on_image_cleared)
        
        layout.addWidget(QLabel(tr("Select Input Image:")))
        layout.addWidget(self.media_selector)
        layout.addStretch()
        
        # Set the widget in the main editor's tool panel
        main_editor.set_tool_panel(widget)

    def _on_image_selected(self, file_path):
        """Handle image selection"""
        self.input_image_path = file_path

    def _on_image_cleared(self):
        """Handle image clearing"""
        self.input_image_path = None

    def edit_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        timeline_index = self.workspace.get_project().get_timeline_index()
        timeline_item = self.workspace.get_project().get_timeline().get_item(timeline_index)
        input_image_path = self.input_image_path or timeline_item.get_image_path()
        return {
            "tool": "imgedit",
            "model": "comfy_ui",
            "input_image_path": input_image_path,
            "prompt": self.editor.get_prompt()
        }

    @classmethod
    def get_tool_name(cls):
        return "imgedit"
    
    @classmethod
    def get_tool_icon(cls):
        return "\ue710"  # Image edit icon from iconfont.json
    
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