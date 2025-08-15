"""
Text tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QPen, QCursor
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
            ColorSetting("text_color"),
            SizeSetting("font_size", min_size=8, max_size=72, default_size=14)
        ]

    def get_id(self) -> str:
        return "text"

    def get_name(self) -> str:
        return "文字工具"

    def get_icon(self) -> str:
        return "\uE647"

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

    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Paint text on the pixmap.
        Note: This is a simplified implementation. 
        A full text tool would need a text input dialog.
        
        Args:
            pixmap: The pixmap to paint on (at original scale)
            start_point: Starting point (in scaled coordinates)
            end_point: Ending point (in scaled coordinates) - not used for text
            scale_factor: The scale factor for coordinate conversion
        """
        # Convert scaled coordinates to original coordinates
        original_start = QPoint(
            int(start_point.x() / scale_factor),
            int(start_point.y() / scale_factor)
        )
        
        # Get text properties from config
        text_color = QColor(self.config.get('text_color', '#000000'))
        font_size = int(self.config.get('font_size', 14))
        font_family = self.config.get('font_family', 'Arial')
        
        # For now, just draw a placeholder text cursor
        # In a real implementation, this would open a text input dialog
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a text cursor indicator
        pen = QPen(text_color)
        painter.setPen(pen)
        cursor_height = font_size
        painter.drawLine(original_start.x(), original_start.y(), 
                        original_start.x(), original_start.y() + cursor_height)
        
        painter.end()

    def get_cursor(self) -> QCursor:
        # Create a custom text cursor using a pixmap
        text_pixmap = QPixmap(16, 16)
        text_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(text_pixmap)
        painter.setPen(QPen(QColor("#000000"), 1))
        # Draw a T-shape to represent text tool
        painter.drawLine(4, 2, 12, 2)  # Top horizontal line
        painter.drawLine(8, 2, 8, 14)  # Vertical line
        painter.drawLine(6, 14, 10, 14)  # Bottom small line
        painter.end()
        return QCursor(text_pixmap)