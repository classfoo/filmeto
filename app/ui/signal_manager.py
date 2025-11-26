"""
Global Signal Manager for UI Component Communication

This singleton class manages signals for communication between UI components,
keeping UI logic separate from the data layer.
"""

from blinker import signal


class UISignalManager:
    """
    Singleton class for managing global UI signals.
    
    Provides a centralized way for UI components to communicate without
    coupling them directly or polluting the data layer with UI-specific signals.
    """
    
    _instance = None
    
    # UI Component Signals
    timeline_position_clicked = signal('timeline_position_clicked')  # Emitted when user clicks on timeline (position in seconds)
    
    def __new__(cls):
        """Singleton pattern - ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(UISignalManager, cls).__new__(cls)
        return cls._instance
    
    def connect_timeline_position_clicked(self, func):
        """Connect to timeline position clicked UI signal"""
        self.timeline_position_clicked.connect(func)

    def send_timeline_position_clicked(self, position: float):
        """Send timeline position clicked UI signal"""
        self.timeline_position_clicked.send(self, position=position)
