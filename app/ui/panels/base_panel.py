"""Base panel class for workspace tool panels."""

from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace


class BasePanel(BaseWidget):
    """
    Abstract base class for workspace tool panels.
    
    All panels must inherit from this class and implement the required lifecycle methods.
    Provides consistent interface for panel switching and state management.
    """
    
    def __init__(self, workspace: Workspace, parent=None):
        """
        Initialize the panel with workspace context.
        
        Args:
            workspace: Workspace instance providing access to project and services
            parent: Optional parent widget
        """
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        self._is_active = False
        self.setup_ui()
    
    def setup_ui(self):
        """
        Set up the panel UI components.
        
        This method should create and configure all widgets for the panel.
        Called during initialization.
        Subclasses must override this method.
        """
        raise NotImplementedError("Subclasses must implement setup_ui()")
    
    def on_activated(self):
        """
        Called when the panel becomes visible/active.
        
        Override this method to refresh data, reconnect signals,
        or perform any necessary updates when panel is shown.
        """
        self._is_active = True
    
    def on_deactivated(self):
        """
        Called when the panel is hidden/deactivated.
        
        Override this method to disconnect signals, pause operations,
        or clean up resources when panel is hidden.
        """
        self._is_active = False
    
    def is_active(self) -> bool:
        """
        Check if panel is currently active.
        
        Returns:
            True if panel is active, False otherwise
        """
        return self._is_active
