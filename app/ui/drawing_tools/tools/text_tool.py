"""
Text tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting, ColorSetting, SizeSetting


class TextTool(DrawingTool):
    """Implementation of the text tool."""

    def __init__(self):
        self.config = {
            "font_size": 14,
            "text_color": "#000000",
            "font_family": "Arial"
        }
        # Define settings for this tool
        self._settings = [
            ColorSetting("Text Color"),
            SizeSetting("Font Size", min_size=8, max_size=72, default_size=14)
        ]

    def get_id(self) -> str:
        return "text"

    def get_name(self) -> str:
        return "文字工具"

    def get_icon(self) -> str:
        return "\uE647"  # 字体

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "font_size" in config:
            self.config["font_size"] = config["font_size"]
        if "text_color" in config:
            self.config["text_color"] = config["text_color"]
        if "font_family" in config:
            self.config["font_family"] = config["font_family"]

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the text tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings