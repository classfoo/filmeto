"""
DrawingSetting - Base interface for all drawing tool settings
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from PySide6.QtWidgets import QPushButton, QFrame, QHBoxLayout, QWidget
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QFont


class DrawingSetting(QObject):
    """
    Abstract base class for drawing tool settings.
    
    Each setting provides:
    - A compact status button (28x28px) displaying current value
    - A floating configuration panel for detailed adjustments
    - Value persistence and change notifications
    """
    
    value_changed = Signal(object)  # Emitted when setting value changes
    
    def __init__(self, name: str, icon: str = ""):
        """
        Initialize drawing setting.
        
        Args:
            name: Setting display name
            icon: Icon character (unicode from iconfont)
        """
        super().__init__()
        self.name = name
        self.icon = icon
        self._value: Any = None
        self._button: Optional[QWidget] = None  # Changed from QPushButton to QWidget to accommodate layout
        self._panel: Optional[QFrame] = None
    
    @abstractmethod
    def create_button(self) -> QWidget:
        """
        Create a status button showing current setting value.
        Button must fit in 30px toolbar.
        
        Returns:
            QWidget with visual indication of current value
        """
        pass
    
    @abstractmethod
    def create_panel(self) -> QFrame:
        """
        Create configuration panel for detailed settings.
        
        Returns:
            QFrame containing setting controls
        """
        pass
    
    @abstractmethod
    def get_value(self) -> str:
        """Get current setting value as string"""
        pass
    
    @abstractmethod
    def set_value(self, value: str):
        """Set setting value from string and update button display"""
        pass
    
    def get_button(self) -> QWidget:
        """Get or create the status button"""
        if self._button is None:
            self._button = self.create_button()
        return self._button
    
    def get_panel(self) -> QFrame:
        """Get or create the config panel"""
        if self._panel is None:
            self._panel = self.create_panel()
        return self._panel
    
    def update_button_display(self):
        """Update button visual to reflect current value"""
        # Override in subclass to customize button appearance
        pass