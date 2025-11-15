"""
Adjust tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting


class AdjustTool(DrawingTool):
    """Implementation of the adjust tool."""

    def __init__(self):
        self.config = {}
        self.config_panel = None

    def get_id(self) -> str:
        return "adjust"

    def get_name(self) -> str:
        return "调整工具"

    def get_icon(self) -> str:
        return "\uE6B2"  # 调整

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
        Get the list of settings for the adjust tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool (empty for adjust tool)
        """
        return []
