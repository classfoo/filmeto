"""
CanvasPixMap component that handles drawing operations with dual pixmaps:
one at original size and one scaled for display.
"""

from PySide6.QtCore import QPoint, Qt, QRect
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor


class CanvasPixMap:
    """
    A component that manages two pixmaps for drawing:
    1. Original pixmap - maintains the actual size and quality
    2. Scaled pixmap - for display at different zoom levels
    
    Both pixmaps are kept in sync to ensure consistent drawing regardless of display scale.
    """

    def __init__(self, original_pixmap: QPixmap):
        """
        Initialize the CanvasPixMap with an original pixmap.
        
        Args:
            original_pixmap: The original pixmap at actual size
        """
        self.original_pixmap = original_pixmap
        self.scaled_pixmap = None
        self.scale_factor = 1.0

    def set_scale_factor(self, scale_factor: float):
        """
        Set the scale factor for display scaling and recreate the scaled pixmap.
        
        Args:
            scale_factor: The scaling factor to apply (e.g., 0.5 for 50% size)
        """
        self.scale_factor = scale_factor
        
        # Destroy and recreate the scaled pixmap
        if self.scaled_pixmap:
            self.scaled_pixmap = None
            
        # Create a new scaled pixmap
        scaled_width = int(self.original_pixmap.width() * self.scale_factor)
        scaled_height = int(self.original_pixmap.height() * self.scale_factor)
        self.scaled_pixmap = QPixmap(scaled_width, scaled_height)
        self.scaled_pixmap.fill(Qt.GlobalColor.transparent)
        
        # Scale the original pixmap to the new scaled pixmap
        painter = QPainter(self.scaled_pixmap)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, scaled_width, scaled_height, self.original_pixmap)
        painter.end()

    def set_brush_properties(self, color: QColor, size: int):
        """
        Set the brush properties for drawing.
        
        Args:
            color: Color of the brush
            size: Size of the brush
        """
        self.brush_color = color
        self.brush_size = size

    def map_to_original_coordinates(self, point: QPoint) -> QPoint:
        """
        Map a point from scaled coordinates to original coordinates.
        
        Args:
            point: Point in scaled coordinates
            
        Returns:
            Point mapped to original coordinates
        """
        if self.scale_factor <= 0:
            return point
            
        return QPoint(
            int(point.x() / self.scale_factor),
            int(point.y() / self.scale_factor)
        )

    def map_to_scaled_coordinates(self, point: QPoint) -> QPoint:
        """
        Map a point from original coordinates to scaled coordinates.
        
        Args:
            point: Point in original coordinates
            
        Returns:
            Point mapped to scaled coordinates
        """
        return QPoint(
            int(point.x() * self.scale_factor),
            int(point.y() * self.scale_factor)
        )

    def draw_line(self, start_point: QPoint, end_point: QPoint, brush_color: QColor = None, brush_size: int = None):
        """
        Draw a line on both the original and scaled pixmaps.
        
        Args:
            start_point: Starting point of the line in scaled coordinates
            end_point: Ending point of the line in scaled coordinates
            brush_color: Color of the brush (optional, uses instance color if not provided)
            brush_size: Size of the brush (optional, uses instance size if not provided)
        """
        color = brush_color if brush_color is not None else getattr(self, 'brush_color', QColor(Qt.GlobalColor.black))
        size = brush_size if brush_size is not None else getattr(self, 'brush_size', 5)
        
        # Draw on original pixmap with scale factor 1.0 (no scaling)
        self._draw_line(start_point, end_point, self.original_pixmap, 1.0, color, size)
        
        # Draw on scaled pixmap with current scale factor
        self._draw_line(start_point, end_point, self.scaled_pixmap, self.scale_factor, color, size)

    def _draw_line(self, start_point: QPoint, end_point: QPoint, pixmap: QPixmap, scale: float, 
                   brush_color: QColor, brush_size: int):
        """
        Internal method to draw a line on a specific pixmap with a given scale.
        
        Args:
            start_point: Starting point of the line in scaled coordinates
            end_point: Ending point of the line in scaled coordinates
            pixmap: The pixmap to draw on
            scale: The scale factor to apply to the brush size
            brush_color: Color of the brush
            brush_size: Size of the brush
        """
        # Map points to the target coordinate system
        target_start = self.map_to_original_coordinates(start_point)
        target_end = self.map_to_original_coordinates(end_point)
        
        # If we're drawing on the scaled pixmap, we need to adjust coordinates
        if scale != 1.0:
            target_start = self.map_to_scaled_coordinates(target_start)
            target_end = self.map_to_scaled_coordinates(target_end)
        
        # Draw on the specified pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen_size = max(1, int(brush_size * scale))
        painter.setPen(QPen(brush_color, pen_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(target_start, target_end)
        painter.end()

    def draw_eraser(self, start_point: QPoint, end_point: QPoint, eraser_size: int = None):
        """
        Erase a line on both the original and scaled pixmaps.
        
        Args:
            start_point: Starting point of the eraser in scaled coordinates
            end_point: Ending point of the eraser in scaled coordinates
            eraser_size: Size of the eraser (optional, uses instance size if not provided)
        """
        size = eraser_size if eraser_size is not None else getattr(self, 'brush_size', 5)
        
        # Erase on original pixmap with scale factor 1.0 (no scaling)
        self._draw_eraser(start_point, end_point, self.original_pixmap, 1.0, size)
        
        # Erase on scaled pixmap with current scale factor
        self._draw_eraser(start_point, end_point, self.scaled_pixmap, self.scale_factor, size)

    def _draw_eraser(self, start_point: QPoint, end_point: QPoint, pixmap: QPixmap, scale: float, eraser_size: int):
        """
        Internal method to erase a line on a specific pixmap with a given scale.
        
        Args:
            start_point: Starting point of the eraser in scaled coordinates
            end_point: Ending point of the eraser in scaled coordinates
            pixmap: The pixmap to erase on
            scale: The scale factor to apply to the eraser size
            eraser_size: Size of the eraser
        """
        # Map points to the target coordinate system
        target_start = self.map_to_original_coordinates(start_point)
        target_end = self.map_to_original_coordinates(end_point)
        
        # If we're drawing on the scaled pixmap, we need to adjust coordinates
        if scale != 1.0:
            target_start = self.map_to_scaled_coordinates(target_start)
            target_end = self.map_to_scaled_coordinates(target_end)
        
        # Erase on the specified pixmap using transparent color
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen_size = max(1, int(eraser_size * scale)) * 2  # Eraser is typically larger than brush
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.setPen(QPen(QColor(0, 0, 0, 0), pen_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(target_start, target_end)
        painter.end()

    def draw_shape(self, shape_type: str, start_point: QPoint, end_point: QPoint, 
                   brush_color: QColor = None, brush_size: int = None):
        """
        Draw a shape on both the original and scaled pixmaps.
        
        Args:
            shape_type: Type of shape to draw ('rectangle', 'ellipse', etc.)
            start_point: Starting point of the shape in scaled coordinates
            end_point: Ending point of the shape in scaled coordinates
            brush_color: Color of the brush (optional, uses instance color if not provided)
            brush_size: Size of the brush (optional, uses instance size if not provided)
        """
        color = brush_color if brush_color is not None else getattr(self, 'brush_color', QColor(Qt.GlobalColor.black))
        size = brush_size if brush_size is not None else getattr(self, 'brush_size', 5)
        
        # Draw on original pixmap with scale factor 1.0 (no scaling)
        self._draw_shape(shape_type, start_point, end_point, self.original_pixmap, 1.0, color, size)
        
        # Draw on scaled pixmap with current scale factor
        self._draw_shape(shape_type, start_point, end_point, self.scaled_pixmap, self.scale_factor, color, size)

    def _draw_shape(self, shape_type: str, start_point: QPoint, end_point: QPoint, pixmap: QPixmap, scale: float,
                    brush_color: QColor, brush_size: int):
        """
        Internal method to draw a shape on a specific pixmap with a given scale.
        
        Args:
            shape_type: Type of shape to draw ('rectangle', 'ellipse', etc.)
            start_point: Starting point of the shape in scaled coordinates
            end_point: Ending point of the shape in scaled coordinates
            pixmap: The pixmap to draw on
            scale: The scale factor to apply to the brush size
            brush_color: Color of the brush
            brush_size: Size of the brush
        """
        # Map points to the target coordinate system
        target_start = self.map_to_original_coordinates(start_point)
        target_end = self.map_to_original_coordinates(end_point)
        
        # If we're drawing on the scaled pixmap, we need to adjust coordinates
        if scale != 1.0:
            target_start = self.map_to_scaled_coordinates(target_start)
            target_end = self.map_to_scaled_coordinates(target_end)
        
        # Create normalized rectangle from the points
        rect = QRect(target_start, target_end).normalized()
        
        # Draw on the specified pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen_size = max(1, int(brush_size * scale))
        painter.setPen(QPen(brush_color, pen_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill for shape
        
        if shape_type.lower() == 'rectangle':
            painter.drawRect(rect)
        elif shape_type.lower() == 'ellipse':
            painter.drawEllipse(rect)
        # Add more shape types as needed
        
        painter.end()

    def clear(self):
        """Clear both pixmaps."""
        self.original_pixmap.fill(Qt.GlobalColor.transparent)
        if self.scaled_pixmap:
            self.scaled_pixmap.fill(Qt.GlobalColor.transparent)

    def get_original_pixmap(self) -> QPixmap:
        """
        Get the original pixmap.
        
        Returns:
            The original pixmap at actual size
        """
        return self.original_pixmap

    def get_scaled_pixmap(self) -> QPixmap:
        """
        Get the scaled pixmap.
        
        Returns:
            The scaled pixmap for display
        """
        return self.scaled_pixmap

    def save_original_pixmap(self, filepath: str):
        """
        Save the original pixmap to a file.
        
        Args:
            filepath: Path to save the pixmap
        """
        self.original_pixmap.save(filepath)

    def save_scaled_pixmap(self, filepath: str):
        """
        Save the scaled pixmap to a file.
        
        Args:
            filepath: Path to save the pixmap
        """
        if self.scaled_pixmap:
            self.scaled_pixmap.save(filepath)