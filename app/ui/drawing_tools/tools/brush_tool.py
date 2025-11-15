"""
Brush tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting, ColorSetting, SizeSetting, OpacitySetting, BrushTypeSetting


class BrushTool(DrawingTool):
    """Implementation of the brush tool."""

    def __init__(self):
        self.config = {
            "style": "圆形",
            "size": 5,
            "opacity": 100
        }
        # Define settings for this tool
        self._settings = [
            ColorSetting("Color"),
            SizeSetting("Size", min_size=1, max_size=50, default_size=5),
            OpacitySetting("Opacity", default_opacity=100),
            BrushTypeSetting("Line Style")
        ]

    def get_id(self) -> str:
        return "brush"

    def get_name(self) -> str:
        return "画笔工具"

    def get_icon(self) -> str:
        return "\uE648"  # 37画笔

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "style" in config:
            self.config["style"] = config["style"]
        if "size" in config:
            self.config["size"] = config["size"]
        if "opacity" in config:
            self.config["opacity"] = config["opacity"]

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the brush tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings