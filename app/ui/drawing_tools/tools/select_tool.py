"""
Select tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting


class SelectTool(DrawingTool):
    """Implementation of the select tool."""

    def __init__(self):
        self.config = {}

    def get_id(self) -> str:
        return "select"

    def get_name(self) -> str:
        return "选择工具"

    def get_icon(self) -> str:
        return "\uE6C5"  # 选择

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the select tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool (empty for select tool)
        """
        return []