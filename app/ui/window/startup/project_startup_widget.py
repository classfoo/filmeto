# -*- coding: utf-8 -*-
"""
Project Startup Widget

This is the main container widget for a single project's startup view.
It focuses on a single project with only chat functionality.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)
from PySide6.QtCore import Signal

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr

logger = logging.getLogger(__name__)


class ProjectStartupWidget(BaseWidget):
    """
    Main container widget for a single project's startup view.

    Structure:
    - Main area: Chat functionality only
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

        # Create the chat component directly without tabs
        self.chat_tab = QWidget()
        self._setup_chat_tab(self.chat_tab)

        # Add the chat component to the main layout
        main_layout.addWidget(self.chat_tab)
    
    def _setup_chat_tab(self, tab: QWidget):
        """Set up the chat tab."""
        # Import the agent chat component
        from app.ui.chat.agent_chat import AgentChatWidget

        # Create the agent chat component
        self.agent_chat_component = AgentChatWidget(self.workspace, tab)

        # Set up the layout for the chat tab
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.agent_chat_component)

    def _connect_signals(self):
        """Connect signals between components."""
        # Connect prompt submission to the agent chat component
        # We'll connect to the agent chat component directly instead of the old prompt widget
        # The agent chat component has its own prompt widget

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
        # Make sure the agent chat component is initialized
        if hasattr(self, 'agent_chat_component') and self.agent_chat_component:
            # Send the message to the agent chat component
            self.agent_chat_component._on_message_submitted(prompt)


    def refresh_project(self):
        """Refresh the current project info."""
        pass  # No-op since we removed project info functionality

    def set_project(self, project_name: str):
        """Set the project to display."""
        self.project_name = project_name

        # Update the agent chat component with the new project context
        # and clear the chat history for the new project
        if hasattr(self, 'agent_chat_component') and self.agent_chat_component:
            # Update the agent's project context
            project = self.workspace.get_project()
            if project:
                self.agent_chat_component.update_project(project)

            # Clear the chat history for the new project
            self.agent_chat_component.chat_history_widget.clear()
