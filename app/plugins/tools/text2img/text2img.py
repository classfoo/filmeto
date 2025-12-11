from qasync import asyncSlot

from app.data.task import TaskResult, TaskProgress
from app.plugins.models.comfy_ui.comfy_ui_model import ComfyUiModel
from app.spi.tool import BaseTool
from app.ui.base_widget import BaseTaskWidget
from app.ui.media_selector.media_selector import MediaSelector
from utils.i18n_utils import tr
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSpacerItem, QSizePolicy


class Text2Image(BaseTool,BaseTaskWidget):

    def __init__(self, workspace, editor=None):
        super(Text2Image,self).__init__(workspace)
        self.setObjectName("tool_text_to_image")
        self.workspace = workspace
        self.workspace.connect_task_execute(self.execute)
        self.editor = editor
        self.reference_image_path = None
        self.media_selector = None

    def generate_image(self):
        self.workspace.submit_task(self.params())

    def params(self):
        return {
            "tool":"text2img",
            "model":"comfy_ui",
            "prompt":self.editor.get_prompt(),
            "reference_image_path": self.reference_image_path
        }

    def init_ui(self, main_editor):
        """Initialize the UI for the text2img tool"""
        # Create widget for tool configuration
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Create media selector for reference image with 9:16 aspect ratio
        self.media_selector = MediaSelector()
        # Set size with 9:16 aspect ratio (portrait) - height 54px, width 30px
        # This fits within the 60px max height constraint of prompt input config panel
        self.media_selector.preview_widget.setFixedSize(30, 54)
        self.media_selector.placeholder_widget.setFixedSize(30, 54)
        
        # Set supported types to image formats only
        self.media_selector.set_supported_types(['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'])
        
        # Connect signals
        self.media_selector.file_selected.connect(self._on_image_selected)
        self.media_selector.file_cleared.connect(self._on_image_cleared)
        
        # Add to layout
        layout.addWidget(self.media_selector)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Set the widget in the prompt input's config panel
        main_editor.prompt_input.set_config_panel_widget(widget)

    def _on_image_selected(self, file_path):
        """Handle image selection"""
        self.reference_image_path = file_path

    def _on_image_cleared(self):
        """Handle image clearing"""
        self.reference_image_path = None

    @classmethod
    def get_tool_name(cls):
        return "text2img"
    
    @classmethod
    def get_tool_icon(cls):
        return "\ue60b"  # Text to image icon from iconfont.json
    
    @classmethod
    def get_tool_display_name(cls):
        return tr("Text to Image")
    
    @classmethod
    def uses_prompt_config_panel(cls):
        """This tool uses the prompt input config panel"""
        return True
    
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