"""
Shape tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting, ColorSetting, SizeSetting, BrushTypeSetting, ShapeTypeSetting


class ShapeTool(DrawingTool):
    """Implementation of the shape tool."""

    def __init__(self):
        self.config = {
            "shape": "rectangle",
            "stroke_color": "#000000",
            "stroke_size": 2,
            "line_style": "solid"
        }
        # Define settings for this tool
        self._settings = [
            ShapeTypeSetting("Shape"),
            ColorSetting("Stroke Color"),
            SizeSetting("Stroke Size", min_size=1, max_size=20, default_size=2),
            BrushTypeSetting("Line Style")
        ]

    def get_id(self) -> str:
        return "shape"

    def get_name(self) -> str:
        return "形状工具"

    def get_icon(self) -> str:
        return "\uE716"  # 形状

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "shape" in config:
            self.config["shape"] = config["shape"]
        if "stroke_color" in config:
            self.config["stroke_color"] = config["stroke_color"]
        if "stroke_size" in config:
            self.config["stroke_size"] = config["stroke_size"]
        if "line_style" in config:
            self.config["line_style"] = config["line_style"]

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the shape tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings