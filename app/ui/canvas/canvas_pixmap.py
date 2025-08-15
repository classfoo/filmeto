"""
CanvasPixMap component that manages dual pixmaps:
One at original size and one scaled for display.
Drawing logic is delegated to DrawingTool implementations.
"""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap, QPainter


class CanvasPixMap:
    """
    A component that manages two pixmaps:
    1. Original pixmap - maintains the actual size and quality
    2. Scaled pixmap - for display at different zoom levels
    
    Drawing operations are handled by DrawingTool implementations.
    """

    def __init__(self, original_pixmap: QPixmap):
        """
        Initialize the CanvasPixMap with an original pixmap.
        
        Args:
            original_pixmap: The original pixmap at actual size
        """
        self.original_pixmap = original_pixmap
        # Initialize scaled_pixmap with the same size as original_pixmap
        self.scaled_pixmap = QPixmap(original_pixmap.size())
        self.scaled_pixmap.fill(Qt.GlobalColor.transparent)
        self.scale_factor = 1.0

    def set_scale_factor(self, scale_factor: float):
        """
        Set the scale factor for display scaling and recreate the scaled pixmap.
        
        Args:
            scale_factor: The scaling factor to apply (e.g., 0.5 for 50% size)
        """
        self.scale_factor = scale_factor
        
        # Create a new scaled pixmap
        scaled_width = int(self.original_pixmap.width() * self.scale_factor)
        scaled_height = int(self.original_pixmap.height() * self.scale_factor)
        
        # Only create scaled pixmap if dimensions are valid
        if scaled_width > 0 and scaled_height > 0:
            self.scaled_pixmap = QPixmap(scaled_width, scaled_height)
            self.scaled_pixmap.fill(Qt.GlobalColor.transparent)
            
            # Scale the original pixmap to the new scaled pixmap
            painter = QPainter(self.scaled_pixmap)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(0, 0, scaled_width, scaled_height, self.original_pixmap)
            painter.end()

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

    def update_scaled_pixmap(self):
        """
        Update the scaled pixmap from the original pixmap.
        This should be called after drawing operations on the original pixmap.
        """
        scaled_width = int(self.original_pixmap.width() * self.scale_factor)
        scaled_height = int(self.original_pixmap.height() * self.scale_factor)
        
        if scaled_width > 0 and scaled_height > 0:
            self.scaled_pixmap = QPixmap(scaled_width, scaled_height)
            self.scaled_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(self.scaled_pixmap)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(0, 0, scaled_width, scaled_height, self.original_pixmap)
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
        return self.scaled_pixmap if self.scaled_pixmap else self.original_pixmap

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