"""Agent message card widget for multi-agent chat display.

This module provides a card widget for displaying individual agent messages
with support for structured data and visual differentiation.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QScrollArea, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QPen

from app.ui.base_widget import BaseWidget
from app.ui.components.avatar_widget import AvatarWidget
from agent.chat.agent_chat_message import AgentMessage, StructureContent, ContentType

# Import specialized widgets from the message subpackage
from app.ui.chat.message.text_content_widget import TextContentWidget
from app.ui.chat.message.code_block_widget import CodeBlockWidget
from app.ui.chat.message.table_widget import TableWidget
from app.ui.chat.message.link_widget import LinkWidget
from app.ui.chat.message.button_widget import ButtonWidget

if TYPE_CHECKING:
    from app.data.workspace import Workspace


class AgentMessageCard(QFrame):
    """Card widget for displaying an agent message in the chat.

    Features:
    - Visual differentiation by agent
    - Structured content display (text, code, tables, links, buttons)
    - Collapsible for long content
    """

    # Signals
    clicked = Signal(str)  # message_id
    reference_clicked = Signal(str, str)  # ref_type, ref_id

    def __init__(
        self,
        agent_message: AgentMessage,
        parent=None,
        agent_color: str = "#4a90e2",  # Default color
        agent_icon: str = "🤖",  # Default icon
        crew_member_metadata: Optional[Dict[str, Any]] = None  # Metadata for crew member
    ):
        """Initialize agent message card."""
        super().__init__(parent)
        self.agent_message = agent_message
        self.agent_color = agent_color  # Store the agent-specific color
        self.agent_icon = agent_icon  # Store the agent-specific icon
        self.crew_member_metadata = crew_member_metadata  # Store crew member metadata

        # For backward compatibility
        self._is_thinking = False
        self._is_complete = False

        self._setup_ui()

    @property
    def is_thinking(self):
        return self._is_thinking

    @property
    def is_complete(self):
        return self._is_complete

    def _setup_ui(self):
        """Set up UI."""
        self.setObjectName("agent_message_card")
        self.setFrameShape(QFrame.NoFrame)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 8, 5, 8)
        main_layout.setSpacing(6)

        # Header row (avatar + name)
        header_row = QWidget(self)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Use the agent-specific color and icon passed to the constructor
        # Avatar - using agent-specific color and icon
        self.avatar = AvatarWidget(
            icon=self.agent_icon,
            color=self.agent_color,
            size=42,
            shape="rounded_rect",  # Match the original style
            parent=header_row
        )
        header_layout.addWidget(self.avatar)

        # Name and role
        name_widget = QWidget(header_row)
        name_layout = QVBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(0)

        # Display name
        self.name_label = QLabel(self.agent_message.sender_name or self.agent_message.sender_id, name_widget)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #4a90d9;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        name_layout.addWidget(self.name_label)

        # Add crew title with colored block in place of the role/ID label
        crew_title_widget = self._create_crew_title_widget()
        if crew_title_widget:
            # Add the crew title layout in place of the role label
            name_layout.addWidget(crew_title_widget)

        header_layout.addWidget(name_widget)
        header_layout.addStretch()

        main_layout.addWidget(header_row)

        # Content area with padding to account for avatar width
        content_area = QWidget(self)
        content_layout = QVBoxLayout(content_area)
        content_layout.setAlignment(Qt.AlignLeft)  # Align content to the left
        avatar_width = 42  # Same as avatar size
        # Add margins to content area to ensure spacing on both sides
        content_layout.setContentsMargins(avatar_width, 0, avatar_width, 0)  # Left and right margins same as avatar width

        self.content_label = QLabel(self.agent_message.content, content_area)
        self.content_label.setObjectName("message_content")
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.content_label.setStyleSheet("""
            QLabel#message_content {
                color: #e1e1e1;
                font-size: 13px;
                padding: 10px 10px;
                background-color: #2b2d30;
                border-radius: 5px;
            }
        """)
        # Set size policy to adapt to content width
        self.content_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        content_layout.addWidget(self.content_label)

        # Structured content container with same padding
        self.structured_container = QWidget(content_area)
        self.structured_layout = QVBoxLayout(self.structured_container)
        self.structured_layout.setContentsMargins(0, 4, 0, 0)  # No extra margins since handled by parent
        self.structured_layout.setSpacing(6)
        content_layout.addWidget(self.structured_container)

        main_layout.addWidget(content_area)

        # Add structured content widgets based on the agent_message
        for structure_content in self.agent_message.structured_content:
            self.add_structure_content_widget(structure_content)

        # Apply card styling
        self._apply_style()

    def _create_crew_title_widget(self):
        """Create a widget to display the crew title with text inside the colored block."""
        if not self.crew_member_metadata or 'crew_title' not in self.crew_member_metadata:
            return None

        crew_title = self.crew_member_metadata['crew_title']

        # Create the colored block with text inside
        title_text = crew_title.replace('_', ' ').title()
        color_block_with_text = QLabel(title_text)
        color_block_with_text.setAlignment(Qt.AlignCenter)
        color_block_with_text.setStyleSheet(f"""
            QLabel {{
                background-color: {self.agent_color};
                color: white;
                font-size: 9px;
                font-weight: bold;
                border-radius: 3px;
                padding: 3px 8px;  /* Adjust padding for better appearance */
            }}
        """)

        # Adjust the width based on the text content
        font_metrics = color_block_with_text.fontMetrics()
        text_width = font_metrics.horizontalAdvance(title_text) + 16  # Add some extra space
        color_block_with_text.setFixedWidth(max(text_width, 60))  # Minimum width of 60

        return color_block_with_text

    def _apply_style(self):
        """Apply card styling."""
        self.setStyleSheet("""
            QFrame#agent_message_card {
                background-color: transparent;
                margin: 2px 0px;
            }
        """)

    def add_structure_content_widget(self, structure_content: StructureContent):
        """Add a widget for the given StructureContent based on its type."""
        widget = None

        if structure_content.content_type == ContentType.TEXT:
            widget = TextContentWidget(structure_content, self.structured_container)
        elif structure_content.content_type == ContentType.CODE_BLOCK:
            widget = CodeBlockWidget(structure_content, self.structured_container)
        elif structure_content.content_type == ContentType.TABLE:
            widget = TableWidget(structure_content, self.structured_container)
        elif structure_content.content_type == ContentType.LINK:
            widget = LinkWidget(structure_content, self.structured_container)
        elif structure_content.content_type == ContentType.BUTTON:
            widget = ButtonWidget(structure_content, self.structured_container)
        # Add more content types as needed
        else:
            # Default to text content for unrecognized types
            widget = TextContentWidget(structure_content, self.structured_container)

        if widget:
            self.structured_layout.addWidget(widget)

    def set_content(self, content: str):
        """Set the content (replace)."""
        self.agent_message.content = content
        self.content_label.setText(content)

    def append_content(self, content: str):
        """Append content."""
        self.agent_message.content += content
        self.content_label.setText(self.agent_message.content)

    def get_content(self) -> str:
        """Get current content."""
        return self.agent_message.content

    def set_thinking(self, is_thinking: bool, thinking_text: str = ""):
        """Set thinking state (placeholder for backward compatibility)."""
        self._is_thinking = is_thinking
        # The new structure doesn't have a thinking indicator, so we'll just ignore this for now
        pass

    def set_complete(self, is_complete: bool):
        """Set completion state (placeholder for backward compatibility)."""
        self._is_complete = is_complete
        # The new structure doesn't have a completion state, so we'll just ignore this for now
        pass

    def set_error(self, error_message: str):
        """Set error state."""
        # Show error in content
        error_content = f"❌ Error: {error_message}"
        self.set_content(error_content)
        self.content_label.setStyleSheet("""
            QLabel#message_content {
                color: #e74c3c;
                font-size: 13px;
                padding: 4px 0px;
            }
        """)

    def add_structured_content(self, structured: StructureContent):
        """Add structured content widget (alias for backward compatibility)."""
        self.add_structure_content_widget(structured)

    def clear_structured_content(self):
        """Clear all structured content."""
        for i in reversed(range(self.structured_layout.count())):
            widget = self.structured_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def update_from_agent_message(self, agent_message: AgentMessage):
        """Update the card from a new agent message."""
        # Update basic content
        self.content_label.setText(agent_message.content)

        # Clear existing structured content
        for i in reversed(range(self.structured_layout.count())):
            widget = self.structured_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        # Add new structured content
        for structure_content in agent_message.structured_content:
            self.add_structure_content_widget(structure_content)


class UserMessageCard(QFrame):
    """Card widget for displaying user messages."""

    def __init__(self, content: str, parent=None):
        """Initialize user message card."""
        super().__init__(parent)
        self.setObjectName("user_message_card")
        self._setup_ui(content)

    def _setup_ui(self, content: str):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 8, 5, 8)
        layout.setSpacing(6)

        # Header row
        header_row = QWidget(self)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Spacer to push to right
        header_layout.addStretch()

        # Name
        name_label = QLabel("You", header_row)
        name_label.setStyleSheet("""
            QLabel {
                color: #35373a;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(name_label)

        # Avatar - using user-specific color
        avatar = AvatarWidget(icon="👤", color="#35373a", size=42, shape="rounded_rect", parent=header_row)
        header_layout.addWidget(avatar)

        layout.addWidget(header_row)

        # Content area with padding to account for avatar width
        content_area = QWidget(self)
        content_layout = QVBoxLayout(content_area)
        content_layout.setAlignment(Qt.AlignRight)  # Align content to the right for user messages
        avatar_width = 42  # Same as avatar size
        # Add margins to content area to ensure spacing on both sides
        content_layout.setContentsMargins(avatar_width, 0, avatar_width, 0)  # Left and right margins same as avatar width

        content_label = QLabel(content, content_area)
        content_label.setObjectName("user_content")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setStyleSheet("""
            QLabel#user_content {
                color: #e1e1e1;
                font-size: 13px;
                padding: 8px 0px; /* No horizontal padding since it's handled by the layout margins */
                background-color: #35373a;
                border-radius: 5px;
            }
        """)
        # Set size policy to adapt to content width
        content_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        content_layout.addWidget(content_label)

        layout.addWidget(content_area)

        self.setStyleSheet("""
            QFrame#user_message_card {
                background-color: transparent;
                margin: 2px 0px;
            }
        """)
