"""
DrawingTool interface definition
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPixmap, QCursor

from .settings import DrawingSetting


class DrawingTool(ABC):
    """
    Abstract base class for all drawing tools.
    Each tool must implement these methods to integrate with the DrawingToolsWidget.
    """

    @abstractmethod
    def get_id(self) -> str:
        """
        Get the unique identifier for this tool.
        Returns:
            str: The unique identifier for the tool
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the display name for this tool.
        Returns:
            str: The display name for the tool
        """
        pass

    @abstractmethod
    def get_icon(self) -> str:
        """
        Get the icon character for this tool.
        Returns:
            str: The icon character (unicode) for the tool
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration data for this tool.
        Returns:
            Dict[str, Any]: The configuration data as a dictionary
        """
        pass

    @abstractmethod
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set the configuration data for this tool.
        Args:
            config (Dict[str, Any]): The configuration data to set
        """
        pass

    @abstractmethod
    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for this tool.
        By default, return an empty list (no settings).
        Override in subclasses to provide tool-specific settings.
        
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return []

    @abstractmethod
    def paint(self, pixmap: QPixmap, start_point: QPoint, end_point: QPoint, 
              scale_factor: float = 1.0) -> None:
        """
        Paint on the pixmap using this tool.
        This is the core method that performs the actual drawing operation.
        
        Args:
            pixmap: The pixmap to paint on (at original scale)
            start_point: Starting point of the paint operation (in scaled coordinates)
            end_point: Ending point of the paint operation (in scaled coordinates)
            scale_factor: The scale factor for coordinate conversion (default: 1.0)
        """
        pass

    @abstractmethod
    def get_cursor(self)->QCursor:
        return Qt.CursorShape.PointingHandCursor