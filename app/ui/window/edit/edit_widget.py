# -*- coding: utf-8 -*-
"""
Edit Widget

This widget contains the edit mode UI (the current main window layout).
It wraps the existing top bar, h_layout, and bottom bar into a single widget
that can be swapped with the startup widget.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from .top_side_bar import MainWindowTopSideBar
from .bottom_side_bar import MainWindowBottomSideBar
from .h_layout import MainWindowHLayout


class EditWidget(BaseWidget):
    """
    Edit mode container widget.
    
    This wraps the existing edit mode layout:
    - Top bar (with drawing tools, settings, etc.)
    - H layout (left sidebar, workspace, right sidebar)
    - Bottom bar (timeline, playback controls)
    """
    
    go_home = Signal()  # Emitted when home button is clicked
    
    def __init__(self, window, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.window = window
        self.project = workspace.get_project()
        self.setObjectName("edit_widget")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar
        self.top_bar = MainWindowTopSideBar(self.window, self.workspace)
        self.top_bar.setObjectName("main_window_top_bar")
        
        # Connect home button signal (will be set up by top bar)
        if hasattr(self.top_bar, 'home_clicked'):
            self.top_bar.home_clicked.connect(self.go_home.emit)
        
        layout.addWidget(self.top_bar)
        
        # Main horizontal layout
        self.h_layout = MainWindowHLayout(self.window, self.workspace)
        layout.addWidget(self.h_layout, 1)
        
        # Bottom bar
        self.bottom_bar = MainWindowBottomSideBar(self.workspace, self.window)
        self.bottom_bar.setObjectName("main_window_bottom_bar")
        layout.addWidget(self.bottom_bar)
    
    def get_top_bar(self):
        """Get the top bar widget."""
        return self.top_bar
    
    def get_bottom_bar(self):
        """Get the bottom bar widget."""
        return self.bottom_bar
    
    def get_h_layout(self):
        """Get the horizontal layout widget."""
        return self.h_layout
