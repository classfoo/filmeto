"""
Brush tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, Qt, QRect
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QCursor
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
            ColorSetting("color"),
            SizeSetting("size", min_size=1, max_size=50, default_size=5),
            OpacitySetting("opacity", default_opacity=100),
            BrushTypeSetting("line_style")
        ]
        # Create initial brush cursor
        self._update_cursor()

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
        if "color" in config:
            self.config["color"] = config["color"]
        if "line_style" in config:
            self.config["line_style"] = config["line_style"]
        # Update cursor when config changes
        self._update_cursor()

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the brush tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings

    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Paint with brush on the pixmap.
        
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
        
        # Get brush properties from config
        color = QColor(self.config.get('color', '#000000'))
        size = int(self.config.get('size', 5))
        opacity = int(self.config.get('opacity', 100))
        line_style_str = self.config.get('line_style', 'solid')
        
        # Apply opacity to color
        color.setAlpha(int(opacity * 255 / 100))
        
        # Map line style string to Qt.PenStyle
        line_style_map = {
            'solid': Qt.PenStyle.SolidLine,
            'dash': Qt.PenStyle.DashLine,
            'dot': Qt.PenStyle.DotLine,
            'dashdot': Qt.PenStyle.DashDotLine
        }
        line_style = line_style_map.get(line_style_str, Qt.PenStyle.SolidLine)
        
        # Paint on the original pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Fix the QPen constructor - pass parameters correctly
        pen = QPen(color)
        pen.setWidth(size)
        pen.setStyle(line_style)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(original_start, original_end)
        painter.end()

    def get_cursor(self) -> QCursor:
        return self.brush_cursor

    def _update_cursor(self) -> None:
        """Create a custom cursor that represents the brush with current settings."""
        # Get brush properties from config
        color = QColor(self.config.get('color', '#000000'))
        size = int(self.config.get('size', 5))
        
        # Create a pixmap for the cursor (minimum size 20x20, larger if brush is bigger)
        cursor_size = max(20, size * 2)
        brush_pixmap = QPixmap(cursor_size, cursor_size)
        brush_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(brush_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the brush outline
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(color)
        # Draw a circle representing the brush tip
        circle_rect = QRect((cursor_size - size) // 2, (cursor_size - size) // 2, size, size)
        painter.drawEllipse(circle_rect)
        
        # Draw a crosshair in the center for precision
        center_x = cursor_size // 2
        center_y = cursor_size // 2
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawLine(center_x - 2, center_y, center_x + 2, center_y)  # Horizontal line
        painter.drawLine(center_x, center_y - 2, center_x, center_y + 2)  # Vertical line
        
        painter.end()
        
        # Create cursor with the pixmap, with hotspot at the center
        self.brush_cursor = QCursor(brush_pixmap, cursor_size // 2, cursor_size // 2)