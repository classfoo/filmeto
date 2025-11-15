"""
Pen tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting, ColorSetting, SizeSetting


class PenTool(DrawingTool):
    """Implementation of the pen tool."""

    def __init__(self):
        self.config = {
            "size": 2,
            "color": "#000000"
        }
        # Define settings for this tool
        self._settings = [
            ColorSetting("Color"),
            SizeSetting("Size", min_size=1, max_size=20, default_size=2)
        ]

    def get_id(self) -> str:
        return "pen"

    def get_name(self) -> str:
        return "铅笔工具"

    def get_icon(self) -> str:
        return "\uE754"  # 手工2

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "size" in config:
            self.config["size"] = config["size"]
        if "color" in config:
            self.config["color"] = config["color"]

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the pen tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings