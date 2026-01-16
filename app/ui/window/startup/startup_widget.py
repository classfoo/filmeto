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
from app.ui.prompt.agent_prompt_widget import AgentPromptWidget

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
        separator.setObjectName("startup_separator")
        separator.setFrameShape(QFrame.VLine)
        separator.setFixedWidth(1)
        content_layout.addWidget(separator)
        
        # Right panel: Tab widget for switching between project info and chat
        right_panel = QWidget()
        right_panel.setObjectName("startup_right_panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Create tab widget for switching between project info and chat
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("startup_tabs")

        # Project info tab
        self.project_info = ProjectInfoWidget(self.workspace)
        self.tab_widget.addTab(self.project_info, tr("项目信息"))

        # Chat tab
        self.chat_tab = QWidget()
        self._setup_chat_tab(self.chat_tab)
        self.tab_widget.addTab(self.chat_tab, tr("聊天"))

        # Set chat tab as default selected
        self.tab_widget.setCurrentIndex(1)

        right_layout.addWidget(self.tab_widget, 1)

        content_layout.addWidget(right_panel, 1)
        
        main_layout.addWidget(content_widget, 1)
    
    def _setup_chat_tab(self, tab: QWidget):
        """Set up the chat tab."""
        # Import the agent chat component
        from app.ui.chat.agent_chat_component import AgentChatComponent

        # Create the agent chat component
        self.agent_chat_component = AgentChatComponent(self.workspace, tab)

        # Set up the layout for the chat tab
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.agent_chat_component)

    def _connect_signals(self):
        """Connect signals between components."""
        # Project selection changes
        self.project_list.project_selected.connect(self._on_project_selected)

        # Edit project (from list or info widget)
        self.project_list.project_edit.connect(self._on_edit_project)
        self.project_info.edit_project.connect(self._on_edit_project)

        # New project created
        self.project_list.project_created.connect(self._on_project_created)

        # Connect prompt submission to the agent chat component
        # We'll connect to the agent chat component directly instead of the old prompt widget
        # The agent chat component has its own prompt widget
    
    def _apply_styles(self):
        """Apply styles to the widget."""
        # Styles are now in the global stylesheet
        pass
    
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
    
    def _on_prompt_submitted(self, prompt: str):
        """Handle prompt submission."""
        # Get the current tab index
        current_tab_index = self.tab_widget.currentIndex()
        current_tab_text = self.tab_widget.tabText(current_tab_index)

        # If the current tab is the chat tab, send the prompt to the agent chat component
        if current_tab_text == tr("聊天"):  # "Chat" tab
            # Make sure the agent chat component is initialized
            if hasattr(self, 'agent_chat_component') and self.agent_chat_component:
                # Send the message to the agent chat component
                self.agent_chat_component._on_message_submitted(prompt)
        else:
            # For other tabs, we can implement different behaviors
            logger.info(f"Prompt submitted in non-chat tab: {prompt}")
    
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
