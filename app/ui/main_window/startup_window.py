# -*- coding: utf-8 -*-
"""
Startup Window

Independent window for startup/home mode with its own size management.
"""
import json
import os
import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from app.data.workspace import Workspace
from .startup import StartupWidget

logger = logging.getLogger(__name__)


class StartupWindow(QMainWindow):
    """
    Independent window for startup/home mode.
    
    This window displays the project list and project info,
    allowing users to browse and manage projects.
    """
    
    enter_edit_mode = Signal(str)  # Emits project name when entering edit mode
    
    def __init__(self, workspace: Workspace):
        super(StartupWindow, self).__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.workspace = workspace
        
        # Window size storage
        self._window_sizes = {}
        self._load_window_sizes()
        
        # Set up the UI
        self._setup_ui()
        
        # Set initial window size (ensure not maximized)
        width, height = self._get_window_size()
        self.resize(width, height)
        
        # Ensure window is in normal state (not maximized)
        self.setWindowState(Qt.WindowNoState)
        
        # Center the window on screen
        screen = self.screen().availableGeometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)
    
    def _load_window_sizes(self):
        """Load stored window sizes from file."""
        try:
            config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "window_sizes.json")
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._window_sizes = json.load(f)
            else:
                # Default size for startup window
                self._window_sizes = {
                    "startup": {"width": 800, "height": 600}
                }
        except Exception as e:
            logger.error(f"Error loading window sizes: {e}")
            # Default sizes if loading fails
            self._window_sizes = {
                "startup": {"width": 800, "height": 600}
            }
    
    def _save_window_sizes(self):
        """Save current window size to file."""
        try:
            config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "window_sizes.json")
            
            # Load existing sizes to preserve edit window size
            existing_sizes = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_sizes = json.load(f)
            
            # Update startup window size
            existing_sizes["startup"] = {
                "width": self.width(),
                "height": self.height()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(existing_sizes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving window sizes: {e}")
    
    def _get_window_size(self):
        """Get the stored size for startup window."""
        # Startup window always uses default 800x600 size
        # This ensures consistent startup experience
        return 800, 600
    
    def closeEvent(self, event):
        """Handle close event to save current window size."""
        self._save_window_sizes()
        # Closing startup window should close the application
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
        event.accept()
    
    def _setup_ui(self):
        """Set up the UI with startup widget."""
        central_widget = QWidget()
        central_widget.setObjectName("startup_window")
        
        layout = QVBoxLayout()
        layout.setObjectName("startup_window_layout")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create startup widget
        self.startup_widget = StartupWidget(self, self.workspace)
        self.startup_widget.enter_edit_mode.connect(self.enter_edit_mode.emit)
        layout.addWidget(self.startup_widget)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def refresh_projects(self):
        """Refresh the project list."""
        if self.startup_widget:
            self.startup_widget.refresh_projects()
    
    def get_selected_project(self) -> str:
        """Get the currently selected project name."""
        if self.startup_widget:
            return self.startup_widget.get_selected_project()
        return None
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        # Let the startup widget handle its own keyboard events
        super().keyPressEvent(event)

