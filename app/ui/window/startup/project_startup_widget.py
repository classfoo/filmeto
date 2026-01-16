# -*- coding: utf-8 -*-
"""
Project Startup Widget

This is the main container widget for a single project's startup view.
It focuses on a single project with tabs for project info and chat.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QTabWidget, QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr
from .project_list_widget import ProjectListWidget
from .project_info_widget import ProjectInfoWidget
from app.ui.prompt.agent_prompt_widget import AgentPromptWidget

logger = logging.getLogger(__name__)


class ProjectStartupWidget(BaseWidget):
    """
    Main container widget for a single project's startup view.

    Structure:
    - Main area: Tab widget for switching between project info and chat
    """

    enter_edit_mode = Signal(str)  # Emits project name when entering edit mode

    def __init__(self, window, workspace: Workspace, project_name: str = None, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)

        self.window = window
        self.project_name = project_name
        self.setObjectName("project_startup_widget")

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        # Set the project info if a project name is provided
        if self.project_name:
            self.set_project(self.project_name)
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create a horizontal layout for the tab buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        # Create buttons to simulate tabs
        self.chat_button = QPushButton(tr("Chat"))
        self.chat_button.setObjectName("chat_tab_button")
        self.chat_button.setCheckable(True)
        self.chat_button.setChecked(True)  # Default selection
        self.chat_button.clicked.connect(lambda: self._switch_to_tab(0))

        self.project_info_button = QPushButton(tr("Project Info"))
        self.project_info_button.setObjectName("project_info_tab_button")
        self.project_info_button.setCheckable(True)
        self.project_info_button.clicked.connect(lambda: self._switch_to_tab(1))

        # Add buttons to the layout
        button_layout.addWidget(self.chat_button)
        button_layout.addWidget(self.project_info_button)

        # Create stacked widget to hold the different views
        self.stacked_widget = QStackedWidget()

        # Chat tab
        self.chat_tab = QWidget()
        self._setup_chat_tab(self.chat_tab)
        self.stacked_widget.addWidget(self.chat_tab)

        # Project info tab
        self.project_info = ProjectInfoWidget(self.workspace)
        self.stacked_widget.addWidget(self.project_info)

        # Add widgets to main layout
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.stacked_widget, 1)

        # Initially show chat tab
        self.stacked_widget.setCurrentIndex(0)
    
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
        # Edit project (from info widget)
        self.project_info.edit_project.connect(self._on_edit_project)

        # Connect prompt submission to the agent chat component
        # We'll connect to the agent chat component directly instead of the old prompt widget
        # The agent chat component has its own prompt widget

    def _switch_to_tab(self, index):
        """Switch to the specified tab."""
        # Update the button states
        if index == 0:  # Chat tab
            self.chat_button.setChecked(True)
            self.project_info_button.setChecked(False)
        elif index == 1:  # Project Info tab
            self.chat_button.setChecked(False)
            self.project_info_button.setChecked(True)

            # Refresh the project info when switching to the project info tab
            if self.project_name:
                self.project_info.set_project(self.project_name)

        # Switch the displayed widget
        self.stacked_widget.setCurrentIndex(index)
    
    def _apply_styles(self):
        """Apply styles to the widget."""
        # Styles are now in the global stylesheet
        pass
    
    def _on_edit_project(self, project_name: str = None):
        """Handle edit project request."""
        # Use the provided project name or the one set during initialization
        project_to_edit = project_name or self.project_name

        # Switch to the project and enter edit mode
        if project_to_edit:
            self.workspace.switch_project(project_to_edit)
            self.enter_edit_mode.emit(project_to_edit)
        else:
            # If no project name is provided, emit the signal anyway
            # This allows the caller to determine the project to edit
            self.enter_edit_mode.emit(self.workspace.project_name)
    
    def _on_prompt_submitted(self, prompt: str):
        """Handle prompt submission."""
        # Check which tab is currently active
        current_tab_index = self.stacked_widget.currentIndex()

        # If the current tab is the chat tab (index 0), send the prompt to the agent chat component
        if current_tab_index == 0:  # "Chat" tab
            # Make sure the agent chat component is initialized
            if hasattr(self, 'agent_chat_component') and self.agent_chat_component:
                # Send the message to the agent chat component
                self.agent_chat_component._on_message_submitted(prompt)
        else:
            # For other tabs, we can implement different behaviors
            logger.info(f"Prompt submitted in non-chat tab: {prompt}")
    
    
    def refresh_project(self):
        """Refresh the current project info."""
        if self.project_name:
            self.project_info.set_project(self.project_name)

    def set_project(self, project_name: str):
        """Set the project to display."""
        self.project_name = project_name
        self.project_info.set_project(project_name)

        # Update the agent chat component with the new project context
        # and clear the chat history for the new project
        if hasattr(self, 'agent_chat_component') and self.agent_chat_component:
            # Update the agent's project context
            project = self.workspace.get_project()
            if project:
                self.agent_chat_component.update_project(project)

            # Clear the chat history for the new project
            self.agent_chat_component.chat_history_widget.clear()
