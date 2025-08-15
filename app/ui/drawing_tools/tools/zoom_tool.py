"""
Zoom tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap, QCursor, QPainter, QPen
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting


class ZoomTool(DrawingTool):
    """Implementation of the zoom tool."""

    def __init__(self):
        self.config = {}

    def get_id(self) -> str:
        return "zoom"

    def get_name(self) -> str:
        return "缩放工具"

    def get_icon(self) -> str:
        return "\uE65E"

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

    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Zoom tool doesn't paint on the pixmap.
        This is a no-op implementation.
        """
        pass

    def get_cursor(self) -> QCursor:
        # Create a custom zoom cursor using a pixmap
        zoom_pixmap = QPixmap(16, 16)
        zoom_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(zoom_pixmap)
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(6, 6, 10, 10)  # Diagonal line for handle
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(2, 2, 10, 10)  # Magnifying glass circle
        painter.end()
        return QCursor(zoom_pixmap)