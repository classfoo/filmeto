# -*- coding: utf-8 -*-
"""
Main Window with Mode Switching Support

This module implements the main application window with support for
switching between startup mode and edit mode.

Modes:
- Startup Mode: Home screen for browsing and managing projects
- Edit Mode: Project editing interface with timeline, canvas, etc.
"""
from enum import Enum
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QLineEdit, QTextEdit, QPlainTextEdit,
                               QStackedWidget)
from PySide6.QtCore import Qt, Signal

from app.data.workspace import Workspace


class WindowMode(Enum):
    """Enumeration of main window modes."""
    STARTUP = "startup"
    EDIT = "edit"


class MainWindow(QMainWindow):
    """
    Main application window with mode switching support.
    
    The window can switch between:
    - Startup mode: For browsing and managing projects
    - Edit mode: For editing the current project
    """
    
    mode_changed = Signal(str)  # Emitted when mode changes
    
    def __init__(self, workspace: Workspace):
        super(MainWindow, self).__init__()
        self.setGeometry(100, 100, 1600, 900)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.workspace = workspace
        self.project = workspace.get_project()
        
        # Set main window reference to workspace for access to preview components
        self.workspace._main_window = self
        
        # Current mode (None initially to force first switch)
        self._current_mode = None
        
        # Mode widgets (lazy initialization)
        self._startup_widget = None
        self._edit_widget = None
        
        # Set up the central widget with stacked layout for mode switching
        self._setup_ui()
        
        # Start in startup mode
        self.switch_mode(WindowMode.STARTUP)
    
    def _setup_ui(self):
        """Set up the UI with a stacked widget for mode switching."""
        central_widget = QWidget()
        central_widget.setObjectName("main_window")
        
        layout = QVBoxLayout()
        layout.setObjectName("main_window_layout")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget to hold different mode widgets
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("main_window_stack")
        layout.addWidget(self.stacked_widget)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def _ensure_startup_widget(self):
        """Ensure the startup widget is created."""
        if self._startup_widget is None:
            from .startup import StartupWidget
            self._startup_widget = StartupWidget(self, self.workspace)
            self._startup_widget.enter_edit_mode.connect(self._on_enter_edit_mode)
            self.stacked_widget.addWidget(self._startup_widget)
    
    def _ensure_edit_widget(self):
        """Ensure the edit widget is created."""
        if self._edit_widget is None:
            from .edit_widget import EditWidget
            self._edit_widget = EditWidget(self, self.workspace)
            self._edit_widget.go_home.connect(self._on_go_home)
            self.stacked_widget.addWidget(self._edit_widget)
    
    def switch_mode(self, mode: WindowMode):
        """
        Switch between window modes.
        
        Args:
            mode: The mode to switch to (WindowMode.STARTUP or WindowMode.EDIT)
        """
        if mode == self._current_mode:
            return
        
        if mode == WindowMode.STARTUP:
            self._ensure_startup_widget()
            self.stacked_widget.setCurrentWidget(self._startup_widget)
            # Refresh projects when returning to startup mode
            self._startup_widget.refresh_projects()
        elif mode == WindowMode.EDIT:
            self._ensure_edit_widget()
            self.stacked_widget.setCurrentWidget(self._edit_widget)
        
        self._current_mode = mode
        self.mode_changed.emit(mode.value)
    
    def get_current_mode(self) -> WindowMode:
        """Get the current window mode."""
        return self._current_mode
    
    def _on_enter_edit_mode(self, project_name: str):
        """Handle entering edit mode from startup."""
        # Project is already switched by the startup widget
        self.project = self.workspace.get_project()
        self.switch_mode(WindowMode.EDIT)
    
    def _on_go_home(self):
        """Handle returning to home/startup mode."""
        self.switch_mode(WindowMode.STARTUP)
    
    def get_workspace(self):
        """Get the workspace instance."""
        return self.workspace
    
    def get_project(self):
        """Get the current project instance."""
        return self.project
    
    # Properties for backward compatibility
    @property
    def top_bar(self):
        """Get the top bar (only available in edit mode)."""
        if self._edit_widget:
            return self._edit_widget.get_top_bar()
        return None
    
    @property
    def bottom_bar(self):
        """Get the bottom bar (only available in edit mode)."""
        if self._edit_widget:
            return self._edit_widget.get_bottom_bar()
        return None
    
    @property
    def h_layout(self):
        """Get the h_layout (only available in edit mode)."""
        if self._edit_widget:
            return self._edit_widget.get_h_layout()
        return None
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle global keyboard shortcuts.
        Spacebar toggles play/pause unless a text input is focused.
        """
        if event.key() == Qt.Key_Space:
            # Check if focus is on a text input widget
            focused_widget = self.focusWidget()
            
            # If focused widget is a text input, let it handle the spacebar
            if isinstance(focused_widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
                super().keyPressEvent(event)
                return
            
            # Only handle spacebar in edit mode with bottom bar available
            if self._current_mode == WindowMode.EDIT and self.bottom_bar:
                # Toggle play/pause
                play_control = self.bottom_bar.play_control
                play_control.set_playing(not play_control.is_playing())
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
