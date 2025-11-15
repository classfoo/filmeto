"""
Eraser tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting, SizeSetting


class EraserTool(DrawingTool):
    """Implementation of the eraser tool."""

    def __init__(self):
        self.config = {
            "size": 20
        }
        # Define settings for this tool
        self._settings = [
            SizeSetting("Size", min_size=5, max_size=100, default_size=20)
        ]

    def get_id(self) -> str:
        return "eraser"

    def get_name(self) -> str:
        return "橡皮擦工具"

    def get_icon(self) -> str:
        return "\uE7F1"  # 橡皮擦

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "size" in config:
            self.config["size"] = config["size"]

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the eraser tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings