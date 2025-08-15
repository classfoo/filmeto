"""
Eraser tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, Qt, QRect
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QCursor
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
            SizeSetting("size", min_size=5, max_size=100, default_size=20)
        ]
        # Create initial eraser cursor
        self._update_cursor()

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
        # Update cursor when config changes
        self._update_cursor()

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the eraser tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings

    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Erase on the pixmap.
        
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
        
        # Get eraser size from config
        size = int(self.config.get('size', 20))
        
        # Erase on the original pixmap using transparent color
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        # Fix the QPen constructor - pass parameters in correct order
        pen = QPen(QColor(0, 0, 0, 0))  # Transparent color
        pen.setWidth(size * 2)  # Eraser is typically larger
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(original_start, original_end)
        painter.end()

    def get_cursor(self) -> QCursor:
        return self.eraser_cursor

    def _update_cursor(self) -> None:
        """Create a custom cursor that represents the eraser with current size setting."""
        # Get eraser size from config
        size = int(self.config.get('size', 20))
        
        # Create a pixmap for the cursor (minimum size 20x20, larger if eraser is bigger)
        cursor_size = max(20, size * 2)
        eraser_pixmap = QPixmap(cursor_size, cursor_size)
        eraser_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(eraser_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the eraser outline
        painter.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
        # Draw a square representing the eraser
        square_rect = QRect((cursor_size - size) // 2, (cursor_size - size) // 2, size, size)
        painter.drawRect(square_rect)
        
        # Draw a crosshair in the center for precision
        center_x = cursor_size // 2
        center_y = cursor_size // 2
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawLine(center_x - 2, center_y, center_x + 2, center_y)  # Horizontal line
        painter.drawLine(center_x, center_y - 2, center_x, center_y + 2)  # Vertical line
        
        painter.end()
        
        # Create cursor with the pixmap, with hotspot at the center
        self.eraser_cursor = QCursor(eraser_pixmap, cursor_size // 2, cursor_size // 2)