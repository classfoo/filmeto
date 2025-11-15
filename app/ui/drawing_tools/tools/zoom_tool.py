"""
Zoom tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting


class ZoomTool(DrawingTool):
    """Implementation of the zoom tool."""

    def __init__(self):
        self.config = {}
        self.config_panel = None

    def get_id(self) -> str:
        return "zoom"

    def get_name(self) -> str:
        return "缩放工具"

    def get_icon(self) -> str:
        return "\uE603"  # 放大镜

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = QWidget()
        return self.config_panel

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the zoom tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool (empty for zoom tool)
        """
        return []
