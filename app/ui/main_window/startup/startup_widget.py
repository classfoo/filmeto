# -*- coding: utf-8 -*-
"""
Startup Widget

This is the main container widget for the startup/home mode.
It combines the project list (left panel) with the project info workspace (right panel).
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.dialog.mac_button import MacTitleBar
from .project_list_widget import ProjectListWidget
from .project_info_widget import ProjectInfoWidget
from .startup_prompt_widget import StartupPromptWidget

logger = logging.getLogger(__name__)


class StartupWidget(BaseWidget):
    """
    Main startup mode container widget.
    
    Structure:
    - Top: Title bar (with window controls)
    - Main area (horizontal split):
      - Left: Project list panel
      - Right: Project info workspace + Prompt input
    """
    
    enter_edit_mode = Signal(str)  # Emits project name when entering edit mode
    
    def __init__(self, window, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.window = window
        self.setObjectName("startup_widget")
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar with window controls
        self.top_bar = QWidget()
        self.top_bar.setObjectName("startup_top_bar")
        self.top_bar.setFixedHeight(40)
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)
        
        # Mac-style title bar (window controls)
        self.title_bar = MacTitleBar(self.window)
        top_bar_layout.addWidget(self.title_bar)
        top_bar_layout.addStretch()
        
        # Enable dragging
        self.top_bar.mousePressEvent = self._on_top_bar_mouse_press
        self.top_bar.mouseMoveEvent = self._on_top_bar_mouse_move
        self.top_bar.mouseReleaseEvent = self._on_top_bar_mouse_release
        self._draggable = False
        self._drag_start_position = None
        
        main_layout.addWidget(self.top_bar)
        
        # Main content area (horizontal layout)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left panel: Project list
        self.project_list = ProjectListWidget(self.workspace)
        content_layout.addWidget(self.project_list)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #3c3f41;")
        separator.setFixedWidth(1)
        content_layout.addWidget(separator)
        
        # Right panel: Project info + Prompt
        right_panel = QWidget()
        right_panel.setObjectName("startup_right_panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Project info area (takes most of the space)
        self.project_info = ProjectInfoWidget(self.workspace)
        right_layout.addWidget(self.project_info, 1)
        
        # Prompt input area (at the bottom)
        prompt_container = QWidget()
        prompt_container.setObjectName("startup_prompt_container")
        prompt_layout = QVBoxLayout(prompt_container)
        prompt_layout.setContentsMargins(16, 8, 16, 16)
        
        self.prompt_widget = StartupPromptWidget(self.workspace)
        prompt_layout.addWidget(self.prompt_widget)
        
        right_layout.addWidget(prompt_container)
        
        content_layout.addWidget(right_panel, 1)
        
        main_layout.addWidget(content_widget, 1)
    
    def _connect_signals(self):
        """Connect signals between components."""
        # Project selection changes
        self.project_list.project_selected.connect(self._on_project_selected)
        
        # Edit project (from list or info widget)
        self.project_list.project_edit.connect(self._on_edit_project)
        self.project_info.edit_project.connect(self._on_edit_project)
        
        # New project created
        self.project_list.project_created.connect(self._on_project_created)
        
        # Prompt submitted
        self.prompt_widget.prompt_submitted.connect(self._on_prompt_submitted)
    
    def _apply_styles(self):
        """Apply styles to the widget."""
        self.setStyleSheet("""
            QWidget#startup_widget {
                background-color: #2b2b2b;
            }
            QWidget#startup_top_bar {
                background-color: #1e1f22;
                border-bottom: 1px solid #3c3f41;
            }
            QWidget#startup_right_panel {
                background-color: #2b2b2b;
            }
            QWidget#startup_prompt_container {
                background-color: #2b2b2b;
            }
        """)
    
    def _on_project_selected(self, project_name: str):
        """Handle project selection from the list."""
        self.project_info.set_project(project_name)
    
    def _on_edit_project(self, project_name: str):
        """Handle edit project request."""
        # Switch to the project and enter edit mode
        self.workspace.switch_project(project_name)
        self.enter_edit_mode.emit(project_name)
    
    def _on_project_created(self, project_name: str):
        """Handle new project creation."""
        # The project list already updates itself
        # Just update the info display
        self.project_info.set_project(project_name)
    
    def _on_prompt_submitted(self, prompt: str, contexts: list, model: str):
        """Handle prompt submission."""
        # TODO: Handle prompt submission in startup mode
        # This could be used to interact with an AI assistant
        # for project-level operations
        logger.info(f"Prompt submitted: {prompt}")
        logger.info(f"Model: {model}")
        logger.info(f"Contexts: {contexts}")
    
    # Window dragging support
    def _on_top_bar_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._draggable = True
            self._drag_start_position = event.globalPosition().toPoint() - self.window.pos()
    
    def _on_top_bar_mouse_move(self, event: QMouseEvent):
        if self._draggable and self._drag_start_position:
            self.window.move(event.globalPosition().toPoint() - self._drag_start_position)
    
    def _on_top_bar_mouse_release(self, event: QMouseEvent):
        self._draggable = False
        self._drag_start_position = None
    
    def refresh_projects(self):
        """Refresh the project list."""
        self.project_list.refresh()
        
        # Update project info if there's a selected project
        selected = self.project_list.get_selected_project()
        if selected:
            self.project_info.set_project(selected)
    
    def get_selected_project(self) -> str:
        """Get the currently selected project name."""
        return self.project_list.get_selected_project()
