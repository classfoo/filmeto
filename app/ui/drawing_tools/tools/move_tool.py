"""
Move tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget
from app.ui.drawing_tools.drawing_tool import DrawingTool


class MoveTool(DrawingTool):
    """Implementation of the move tool."""

    def get_id(self) -> str:
        return "move"

    def get_name(self) -> str:
        return "移动工具"

    def get_icon(self) -> str:
        return "\uE61B"  # 平移

    def create_config_panel(self) -> QWidget:
        # Move tool has no configuration
        return QWidget()

    def get_config(self) -> Dict[str, Any]:
        return {}

    def set_config(self, config: Dict[str, Any]) -> None:
        pass