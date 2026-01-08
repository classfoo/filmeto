# -*- coding: utf-8 -*-
"""
Window Manager

Manages the startup and edit windows, handling transitions between them.
"""
import logging
from PySide6.QtCore import QObject

from app.data.workspace import Workspace
from .startup_window import StartupWindow
from .edit_window import EditWindow

logger = logging.getLogger(__name__)


class WindowManager(QObject):
    """
    Manages startup and edit windows.
    
    Handles creation, destruction, and transitions between windows.
    """
    
    def __init__(self, workspace: Workspace):
        super().__init__()
        self.workspace = workspace
        
        # Window instances
        self.startup_window = None
        self.edit_window = None
    
    def show_startup_window(self):
        """Show the startup window and hide the edit window."""
        # Create startup window if it doesn't exist
        if self.startup_window is None:
            self.startup_window = StartupWindow(self.workspace)
            self.startup_window.enter_edit_mode.connect(self._on_enter_edit_mode)
            self.startup_window.destroyed.connect(self._on_startup_window_destroyed)
        
        # Ensure window is in normal state (not maximized)
        from PySide6.QtCore import Qt
        self.startup_window.setWindowState(Qt.WindowNoState)
        
        # Show startup window
        self.startup_window.show()
        
        # Hide edit window if it exists
        if self.edit_window:
            self.edit_window.hide()
    
    def show_edit_window(self, project_name: str = None):
        """Show the edit window and hide the startup window."""
        # Switch project if specified
        if project_name:
            self.workspace.switch_project(project_name)
        
        # Create edit window if it doesn't exist
        if self.edit_window is None:
            self.edit_window = EditWindow(self.workspace)
            self.edit_window.go_home.connect(self._on_go_home)
            self.edit_window.destroyed.connect(self._on_edit_window_destroyed)
            # Override closeEvent to show startup window instead of closing
            def close_with_fallback(event):
                # Save window size before hiding
                self.edit_window._save_window_sizes()
                # Hide edit window and show startup window instead of closing
                self.edit_window.hide()
                if self.startup_window:
                    self.startup_window.show()
                # Don't call original_close to prevent actual window destruction
                event.ignore()
            self.edit_window.closeEvent = close_with_fallback
        
        # Update project reference
        self.edit_window.project = self.workspace.get_project()
        
        # Show edit window
        self.edit_window.show()
        
        # Hide startup window if it exists
        if self.startup_window:
            self.startup_window.hide()
    
    def _on_enter_edit_mode(self, project_name: str):
        """Handle entering edit mode from startup window."""
        self.show_edit_window(project_name)
    
    def _on_go_home(self):
        """Handle returning to home/startup mode."""
        self.show_startup_window()
    
    def _on_startup_window_destroyed(self):
        """Handle startup window destruction."""
        self.startup_window = None
    
    def _on_edit_window_destroyed(self):
        """Handle edit window destruction."""
        self.edit_window = None
    
    def get_startup_window(self):
        """Get the startup window instance."""
        return self.startup_window
    
    def get_edit_window(self):
        """Get the edit window instance."""
        return self.edit_window
    
    def refresh_projects(self):
        """Refresh the project list in startup window."""
        if self.startup_window:
            self.startup_window.refresh_projects()

