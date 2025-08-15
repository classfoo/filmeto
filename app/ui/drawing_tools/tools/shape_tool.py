"""
Shape tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QCursor
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
            ShapeTypeSetting("shape"),
            ColorSetting("stroke_color"),
            SizeSetting("stroke_size", min_size=1, max_size=20, default_size=2),
            BrushTypeSetting("line_style")
        ]

    def get_id(self) -> str:
        return "shape"

    def get_name(self) -> str:
        return "形状工具"

    def get_icon(self) -> str:
        return "\uE716"

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

    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Paint a shape on the pixmap.
        
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
        
        # Get shape properties from config
        shape_type = self.config.get('shape', 'rectangle')
        stroke_color = QColor(self.config.get('stroke_color', '#000000'))
        stroke_size = int(self.config.get('stroke_size', 2))
        line_style_str = self.config.get('line_style', 'solid')
        
        # Map line style string to Qt.PenStyle
        line_style_map = {
            'solid': Qt.PenStyle.SolidLine,
            'dash': Qt.PenStyle.DashLine,
            'dot': Qt.PenStyle.DotLine,
            'dashdot': Qt.PenStyle.DashDotLine
        }
        line_style = line_style_map.get(line_style_str, Qt.PenStyle.SolidLine)
        
        # Create normalized rectangle from the points
        rect = QRect(original_start, original_end).normalized()
        
        # Paint on the original pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Fix the QPen constructor - pass parameters correctly
        pen = QPen(stroke_color)
        pen.setWidth(stroke_size)
        pen.setStyle(line_style)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill for shape
        
        if shape_type.lower() == 'rectangle':
            painter.drawRect(rect)
        elif shape_type.lower() == 'ellipse':
            painter.drawEllipse(rect)
        # Add more shape types as needed
        
        painter.end()

    def get_cursor(self) -> QCursor:
        return Qt.CursorShape.PointingHandCursor