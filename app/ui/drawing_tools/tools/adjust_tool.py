"""
Adjust tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap, QCursor
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting


class AdjustTool(DrawingTool):
    """Implementation of the adjust tool."""

    def __init__(self):
        self.config = {}

    def get_id(self) -> str:
        return "adjust"

    def get_name(self) -> str:
        return "调整工具"

    def get_icon(self) -> str:
        return "\uE658"  # 调整

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

    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Adjust tool doesn't paint on the pixmap.
        This is a no-op implementation.
        """
        pass

    def get_cursor(self) -> QCursor:
        return Qt.CursorShape.CrossCursor