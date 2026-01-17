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

if TYPE_CHECKING:
    from app.data.workspace import Workspace




class TextContentWidget(QWidget):
    """Widget for displaying text content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize text content widget."""
        super().__init__(parent)
        self.content = content
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Title if available
        if self.content.title:
            title_label = QLabel(self.content.title, self)
            title_label.setStyleSheet("""
                QLabel {
                    color: #7c4dff;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            layout.addWidget(title_label)

        # Description if available
        if self.content.description:
            desc_label = QLabel(self.content.description, self)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(desc_label)

        # Actual text content
        text_label = QLabel(str(self.content.data), self)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            QLabel {
                color: #e1e1e1;
                font-size: 12px;
                padding-top: 4px;
            }
        """)
        layout.addWidget(text_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)


class CodeBlockWidget(QWidget):
    """Widget for displaying code blocks."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize code block widget."""
        super().__init__(parent)
        self.content = content
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Title if available
        if self.content.title:
            title_label = QLabel(self.content.title, self)
            title_label.setStyleSheet("""
                QLabel {
                    color: #7c4dff;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            layout.addWidget(title_label)

        # Description if available
        if self.content.description:
            desc_label = QLabel(self.content.description, self)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(desc_label)

        # Code content
        code_text = QTextEdit(self)
        code_text.setReadOnly(True)
        code_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 6px;
            }
        """)

        # Extract code from data (which should be a dict with 'language' and 'code')
        if isinstance(self.content.data, dict):
            code_str = self.content.data.get('code', str(self.content.data))
            language = self.content.data.get('language', '')
        else:
            code_str = str(self.content.data)
            language = ''

        code_text.setPlainText(code_str)
        layout.addWidget(code_text)

        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)


class TableWidget(QWidget):
    """Widget for displaying table content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize table widget."""
        super().__init__(parent)
        self.content = content
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Title if available
        if self.content.title:
            title_label = QLabel(self.content.title, self)
            title_label.setStyleSheet("""
                QLabel {
                    color: #7c4dff;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            layout.addWidget(title_label)

        # Description if available
        if self.content.description:
            desc_label = QLabel(self.content.description, self)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(desc_label)

        # Table content
        table_widget = QTableWidget(self)
        table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #d4d4d4;
                gridline-color: #3c3c3c;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #333337;
                color: #cccccc;
                padding: 4px;
                border: 1px solid #444;
            }
        """)

        # Populate table from data (should be a dict with 'headers' and 'rows')
        if isinstance(self.content.data, dict):
            headers = self.content.data.get('headers', [])
            rows = self.content.data.get('rows', [])

            if headers:
                table_widget.setColumnCount(len(headers))
                table_widget.setHorizontalHeaderLabels(headers)

            if rows:
                table_widget.setRowCount(len(rows))
                for row_idx, row_data in enumerate(rows):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data))
                        table_widget.setItem(row_idx, col_idx, item)
        elif isinstance(self.content.data, list):
            # If data is a list of lists, treat each inner list as a row
            if self.content.data:
                num_cols = max(len(row) for row in self.content.data) if self.content.data else 0
                table_widget.setColumnCount(num_cols)
                table_widget.setRowCount(len(self.content.data))

                for row_idx, row_data in enumerate(self.content.data):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data))
                        table_widget.setItem(row_idx, col_idx, item)

        layout.addWidget(table_widget)

        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)


class LinkWidget(QWidget):
    """Widget for displaying link content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize link widget."""
        super().__init__(parent)
        self.content = content
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Link icon
        icon_label = QLabel("🔗", self)
        layout.addWidget(icon_label)

        # Link data (should be a dict with 'url' and 'text')
        if isinstance(self.content.data, dict):
            url = self.content.data.get('url', '')
            text = self.content.data.get('text', url)
        else:
            url = str(self.content.data)
            text = url

        # Link button
        link_button = QPushButton(text, self)
        link_button.setStyleSheet("""
            QPushButton {
                color: #4a90d9;
                text-align: left;
                border: none;
                background: transparent;
                font-size: 11px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #5aa0ff;
            }
        """)
        link_button.clicked.connect(lambda: self._handle_link_click(url))
        layout.addWidget(link_button)
        layout.addStretch()

        self.setStyleSheet("""
            QWidget {
                background-color: #1a3a5a;
                border-radius: 3px;
            }
        """)

    def _handle_link_click(self, url: str):
        """Handle link click and emit reference clicked signal."""
        self.open_link(url)

        # Find the parent AgentMessageCard and emit the reference clicked signal
        parent = self.parent()
        while parent:
            if hasattr(parent, 'reference_clicked'):
                parent.reference_clicked.emit('link', url)
                break
            parent = parent.parent()

    def open_link(self, url: str):
        """Open the link in browser."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))


class ButtonWidget(QWidget):
    """Widget for displaying button content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize button widget."""
        super().__init__(parent)
        self.content = content
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Button data (should be a dict with 'text' and 'action')
        if isinstance(self.content.data, dict):
            text = self.content.data.get('text', 'Button')
            action = self.content.data.get('action', '')
        else:
            text = str(self.content.data)
            action = ''

        # Button
        button = QPushButton(text, self)
        button.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5aa0ff;
            }
            QPushButton:pressed {
                background-color: #3a80c9;
            }
        """)
        # Connect button click to a placeholder action
        button.clicked.connect(lambda: self._handle_button_click(action))
        layout.addWidget(button)
        layout.addStretch()

        self.setStyleSheet("""
            QWidget {
                background-color: #2a2d3e;
                border-radius: 4px;
            }
        """)

    def button_clicked(self, action: str):
        """Handle button click."""
        # Find the parent AgentMessageCard and emit the reference clicked signal
        parent = self.parent()
        while parent:
            if hasattr(parent, 'reference_clicked'):
                parent.reference_clicked.emit('button', action)
                break
            parent = parent.parent()

        print(f"Button clicked with action: {action}")


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

        # Horizontal layout to put name and crew title on the same line
        name_and_title_layout = QHBoxLayout()
        name_and_title_layout.setContentsMargins(0, 0, 0, 0)
        name_and_title_layout.setSpacing(5)

        self.name_label = QLabel(self.agent_message.sender_name or self.agent_message.sender_id, name_widget)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #4a90d9;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        name_and_title_layout.addWidget(self.name_label)

        # Add crew title with colored block
        crew_title_widget = self._create_crew_title_widget()
        if crew_title_widget:
            name_and_title_layout.addWidget(crew_title_widget)

        # Add the horizontal layout to the vertical layout
        name_layout.addLayout(name_and_title_layout)

        # Role/ID label
        role_label = QLabel(self.agent_message.sender_id, name_widget)
        role_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
            }
        """)
        name_layout.addWidget(role_label)

        header_layout.addWidget(name_widget)
        header_layout.addStretch()

        main_layout.addWidget(header_row)

        # Content area with padding to account for avatar width
        content_area = QWidget(self)
        content_layout = QVBoxLayout(content_area)
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
                padding: 4px 0px; /* No horizontal padding since it's handled by the layout margins */
                background-color: #2b2d30; /* Similar to agent background but subtle */
                border-radius: 5px;
            }
        """)
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
        """Create a widget to display the crew title with a colored block."""
        if not self.crew_member_metadata or 'crew_title' not in self.crew_member_metadata:
            return None

        crew_title = self.crew_member_metadata['crew_title']

        # Create a horizontal layout for the colored block and title
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        # Create the colored block
        color_block = QLabel()
        color_block.setFixedSize(10, 10)  # Small square block
        color_block.setStyleSheet(f"background-color: {self.agent_color}; border-radius: 2px;")

        # Create the title label
        title_label = QLabel(crew_title.replace('_', ' ').title())
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 10px;
                font-weight: normal;
            }
        """)

        # Add widgets to layout
        title_layout.addWidget(color_block)
        title_layout.addWidget(title_label)
        title_layout.addStretch()  # Add stretch to prevent expansion

        return title_widget

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
        content_layout.addWidget(content_label)

        layout.addWidget(content_area)

        self.setStyleSheet("""
            QFrame#user_message_card {
                background-color: transparent;
                margin: 2px 0px;
            }
        """)
