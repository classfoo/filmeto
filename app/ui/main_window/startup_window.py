# -*- coding: utf-8 -*-
"""
Startup Window

Independent window for startup/home mode with its own size management.
"""
import json
import os
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from app.data.workspace import Workspace
from app.ui.dialog.left_panel_dialog import LeftPanelDialog
from .startup.project_list_widget import ProjectListWidget
from .startup.project_info_widget import ProjectInfoWidget
from .startup.startup_prompt_widget import StartupPromptWidget

logger = logging.getLogger(__name__)


class StartupWindow(LeftPanelDialog):
    """
    Independent window for startup/home mode.
    
    This window displays the project list and project info,
    allowing users to browse and manage projects.
    """
    
    enter_edit_mode = Signal(str)  # Emits project name when entering edit mode
    
    def __init__(self, workspace: Workspace):
        super(StartupWindow, self).__init__(parent=None, left_panel_width=250)
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
        """Set up the UI with left panel and right work area."""
        # Left panel: Project list
        self.project_list = ProjectListWidget(self.workspace)
        self.set_left_content_widget(self.project_list)
        
        # Right work area: Project info + Prompt input
        right_container = QWidget()
        right_container.setObjectName("startup_right_container")
        right_layout = QVBoxLayout(right_container)
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
        
        self.set_right_work_widget(right_container)
        
        # Connect signals
        self._connect_signals()
        
        # Apply styles
        self._apply_styles()
    
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
            QWidget#startup_right_container {
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
    
    def refresh_projects(self):
        """Refresh the project list."""
        if self.project_list:
            self.project_list.refresh()
            
            # Update project info if there's a selected project
            selected = self.project_list.get_selected_project()
            if selected:
                self.project_info.set_project(selected)
    
    def get_selected_project(self) -> str:
        """Get the currently selected project name."""
        if self.project_list:
            return self.project_list.get_selected_project()
        return None
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        # Let the startup widget handle its own keyboard events
        super().keyPressEvent(event)

