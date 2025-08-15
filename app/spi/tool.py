from typing import Any

from qasync import asyncSlot

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from utils.progress_utils import Progress


class BaseTool(BaseWidget,Progress):

    def __init__(self,workspace:Workspace):
        # Only initialize QWidget if workspace is not None
        if workspace is not None:
            super(BaseTool,self).__init__(workspace)
        return

    def submit_task(self,task:Any):
        self.workspace.submit_task(task)

    @asyncSlot()
    async def execute(self, task):
        return

    @classmethod
    def get_tool_name(cls):
        """Get the tool name for tool-specific prompt storage.
        Should be overridden by subclasses."""
        # Default implementation - return the class name in lowercase with 'tool' removed
        class_name = cls.__name__.lower()
        if class_name.endswith('tool'):
            class_name = class_name[:-4]  # Remove 'tool' suffix
        return class_name
    
    @classmethod
    def get_tool_icon(cls):
        """Get the tool icon for UI display.
        Should be overridden by subclasses."""
        # Default implementation - return a generic icon
        return "\ue600"  # Barrage as generic tool icon
    
    @classmethod
    def get_tool_display_name(cls):
        """Get the tool display name for UI.
        Should be overridden by subclasses."""
        # Default implementation - return the tool name
        return cls.get_tool_name().title()
    
    def get_media_path(self, timeline_item):
        """Get the appropriate media path for this tool.
        Should be overridden by subclasses to customize behavior.
        Returns the path to the media file that should be displayed.
        """
        # Default implementation - return None
        return None