"""
Agent Chat Members Component

This component displays a list of crew members for a project.
"""
from typing import List, Optional
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QPushButton, QToolBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QAction

from agent.crew import CrewMember, CrewMemberConfig, CrewTitle
from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.components.avatar_widget import AvatarWidget
from utils.i18n_utils import tr
import logging

logger = logging.getLogger(__name__)


class CrewMemberListItem(QWidget):
    """Custom widget for displaying a crew member in the list."""

    def __init__(self, crew_member: CrewMember, parent=None):
        super().__init__(parent)
        self.crew_member = crew_member

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI for the crew member item."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)  # Increased margins for better spacing
        layout.setSpacing(10)  # Increased spacing between elements
        layout.setAlignment(Qt.AlignVCenter)  # Vertically center all elements

        # Avatar widget
        self.avatar_widget = AvatarWidget(
            icon=self.crew_member.config.icon,
            color=self.crew_member.config.color,
            size=28  # Slightly larger size for better visibility
        )
        layout.addWidget(self.avatar_widget, 0, Qt.AlignVCenter)  # Align to center vertically

        # Name label
        self.name_label = QLabel(self.crew_member.config.name.title())
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        layout.addWidget(self.name_label, 1, Qt.AlignVCenter)  # Expanding with vertical center alignment

        # Position label
        self.position_label = QLabel(self._get_position_title())
        self.position_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        layout.addWidget(self.position_label, 0, Qt.AlignVCenter)  # Align to center vertically

        # Set minimum height to ensure full icon visibility and proper spacing
        self.setMinimumHeight(50)
        
    def _get_position_title(self) -> str:
        """Get the position title for the crew member."""
        # First, try to get the crew_title from metadata
        crew_title_value = self.crew_member.config.metadata.get('crew_title')
        if crew_title_value:
            # Create a temporary CrewTitle instance to get the display title
            title_instance = CrewTitle.create_from_title(crew_title_value)
            if title_instance and title_instance.title:
                return title_instance.get_title_display()
            # If no matching title found, return the crew_title as is
            return crew_title_value.replace('_', ' ').title()

        # Fallback: Try to map the crew member's name to a CrewTitle
        try:
            # Convert the name to uppercase and replace spaces/underscores with underscores for enum lookup
            name_upper = self.crew_member.config.name.upper().replace('-', '_').replace(' ', '_')

            # Special case handling for common variations
            if name_upper == "STORYBOARD_ARTIST":
                name_upper = "STORYBOARD_ARTIST"
            elif name_upper == "VFX_SUPERVISOR":
                name_upper = "VFX_SUPERVISOR"
            elif name_upper == "SOUND_DESIGNER":
                name_upper = "SOUND_DESIGNER"

            # Try to create a CrewTitle instance from the name
            title_instance = CrewTitle.create_from_title(name_upper.lower())
            if title_instance and title_instance.title:
                return title_instance.get_title_display()

            # If no exact match, try to match by lowercase name
            title_instance = CrewTitle.create_from_title(self.crew_member.config.name.lower())
            if title_instance and title_instance.title:
                return title_instance.get_title_display()

            # If no match found, return the name as is
            return self.crew_member.config.name.title()
        except:
            # If anything goes wrong, return the name as is
            return self.crew_member.config.name.title()


class AgentChatMembersWidget(BaseWidget):
    """Agent chat members component showing crew members for a project."""
    
    member_selected = Signal(CrewMember)  # Emitted when a member is selected
    add_member_requested = Signal()       # Emitted when add member button is clicked
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the agent chat members component."""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
            
        self.members: List[CrewMember] = []
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar for search and add member
        self.toolbar = QToolBar()
        self.toolbar.setObjectName("agent_chat_members_toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        layout.addWidget(self.toolbar)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("agent_chat_members_search")
        self.search_input.setPlaceholderText(tr("Search members..."))
        self.search_input.setMaximumWidth(200)
        self.toolbar.addWidget(self.search_input)

        # Spacer to push add button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)

        # Add member button
        self.add_member_button = QPushButton("")  # Plus icon from iconfont
        self.add_member_button.setObjectName("agent_chat_members_add_button")
        self.add_member_button.clicked.connect(self.add_member_requested.emit)
        self.add_member_button.setToolTip(tr("Add Member"))
        self.toolbar.addWidget(self.add_member_button)

        # List widget for crew members
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("agent_chat_members_list")
        self.list_widget.itemSelectionChanged.connect(self._on_item_selection_changed)
        # Set spacing between items
        self.list_widget.setSpacing(4)
        # Set uniform item heights to ensure proper alignment
        self.list_widget.setUniformItemSizes(True)
        layout.addWidget(self.list_widget)
        
    def _connect_signals(self):
        """Connect internal signals."""
        self.search_input.textChanged.connect(self._filter_members)
        
    def _on_item_selection_changed(self):
        """Handle when a list item is selected."""
        current_item = self.list_widget.currentItem()
        if current_item:
            crew_member = current_item.data(Qt.UserRole)
            if crew_member:
                self.member_selected.emit(crew_member)
                
    def _filter_members(self, text: str):
        """Filter the member list based on search text."""
        text_lower = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            crew_member = item.data(Qt.UserRole)
            
            # Show/hide item based on whether name contains search text
            visible = text_lower in crew_member.config.name.lower()
            item.setHidden(not visible)
            
    def set_members(self, members: List[CrewMember]):
        """Set the list of crew members to display."""
        self.members = members
        self._update_member_list()
        
    def _update_member_list(self):
        """Update the list widget with current members."""
        self.list_widget.clear()

        for member in self.members:
            # Create custom widget for the list item
            item_widget = CrewMemberListItem(member)

            # Create list item and set the custom widget
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, member)

            # Add to list
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, item_widget)
            
    def refresh_members(self):
        """Refresh the member list."""
        self._update_member_list()
        
    def get_selected_member(self) -> Optional[CrewMember]:
        """Get the currently selected crew member."""
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None