"""
Pen tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QCursor
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
            ColorSetting("color"),
            SizeSetting("size", min_size=1, max_size=20, default_size=2)
        ]

    def get_id(self) -> str:
        return "pen"

    def get_name(self) -> str:
        return "铅笔工具"

    def get_icon(self) -> str:
        return "\uE65A"

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

    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Paint with pen on the pixmap.
        
        Args:
            pixmap: The pixmap to paint on (at original scale)
            start_point: Starting point (in scaled coordinates)
            end_point: Ending point (in scaled coordinates)
            scale_factor: The scale factor for coordinate conversion
        """
        # Convert scaled coordinates to original coordinates
        original_start = QPoint(
            int(start_point.x() / scale_factor),
            int(start_point.y() / scale_factor)
        )
        original_end = QPoint(
            int(end_point.x() / scale_factor),
            int(end_point.y() / scale_factor)
        )
        
        # Get pen color and size from config
        color = QColor(self.config.get('color', '#000000'))
        size = int(self.config.get('size', 2))
        
        # Paint on the original pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Fix the QPen constructor - pass parameters correctly
        pen = QPen(color)
        pen.setWidth(size)
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(original_start, original_end)
        painter.end()

    def get_cursor(self) -> QCursor:
        return Qt.CursorShape.ArrowCursor