"""
DrawingTool interface definition
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget

from app.ui.drawing_tools.drawing_setting import DrawingSetting


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
    def create_config_panel(self) -> QWidget:
        """
        Create and return the configuration panel widget for this tool.
        Returns:
            QWidget: The configuration panel for the tool
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

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for this tool.
        By default, return an empty list (no settings).
        Override in subclasses to provide tool-specific settings.
        
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return []