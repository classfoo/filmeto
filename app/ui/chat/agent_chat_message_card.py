"""Agent message card widget for multi-agent chat display.

This module provides a card widget for displaying individual agent messages
with support for structured data and visual differentiation.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy
)

from agent.chat.agent_chat_message import AgentMessage, StructureContent, ContentType
from app.ui.chat.message.button_widget import ButtonWidget
from app.ui.chat.message.code_block_widget import CodeBlockWidget
from app.ui.chat.message.link_widget import LinkWidget
from app.ui.chat.message.table_widget import TableWidget
# Import specialized widgets from the message subpackage
from app.ui.chat.message.text_content_widget import TextContentWidget
from app.ui.chat.message.structure_content_widget import StructureContentWidget
from app.ui.components.avatar_widget import AvatarWidget

if TYPE_CHECKING:
    pass


class BaseMessageCard(QFrame):
    """Base class for message cards with shared functionality."""

    # Signals
    clicked = Signal(str)  # message_id
    reference_clicked = Signal(str, str)  # ref_type, ref_id

    def __init__(
        self,
        sender_name: str,
        icon: str,
        color: str,
        parent=None,
        alignment: Qt.AlignmentFlag = Qt.AlignLeft,
        background_color: str = "#2b2d30",
        text_color: str = "#e1e1e1",
        avatar_size: int = 42,
        structured_content: Optional[List[StructureContent]] = None
    ):
        """Initialize base message card."""
        super().__init__(parent)
        self.sender_name = sender_name
        self.icon = icon
        self.color = color
        self.alignment = alignment
        self.background_color = background_color
        self.text_color = text_color
        self.avatar_size = avatar_size
        self.structured_content_list = structured_content or []

        # For backward compatibility
        self._is_thinking = False
        self._is_complete = False

        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        self.setObjectName("base_message_card")
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

        # Avatar - using agent-specific color and icon
        self.avatar = AvatarWidget(
            icon=self.icon,
            color=self.color,
            size=self.avatar_size,
            shape="rounded_rect",  # Match the original style
            parent=header_row
        )
        header_layout.addWidget(self.avatar)

        # Name and role
        self.name_widget = QWidget(header_row)
        name_layout = QVBoxLayout(self.name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(0)

        # Display name
        self.name_label = QLabel(self.sender_name, self.name_widget)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.color};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        name_layout.addWidget(self.name_label)

        # Add the name widget to the header layout
        header_layout.addWidget(self.name_widget)

        # Add stretch to push everything to the left for agent messages or to the right for user messages
        if self.alignment == Qt.AlignRight:
            # For user messages, we want avatar on the right, so we add stretch at the beginning
            header_layout.insertStretch(0, 1)
        else:
            # For agent messages, we want avatar on the left, so we add stretch at the end
            header_layout.addStretch()

        main_layout.addWidget(header_row)

        # Content area with padding to account for avatar width
        self.content_area = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setAlignment(self.alignment)
        avatar_width = self.avatar_size  # Same as avatar size
        # Add margins to content area to ensure spacing on both sides
        self.content_layout.setContentsMargins(avatar_width, 0, avatar_width, 0)  # Left and right margins same as avatar width
        self.content_layout.setSpacing(6)

        self.bubble_container = QFrame(self.content_area)
        self.bubble_container.setObjectName("message_bubble")
        self.bubble_container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.bubble_layout = QVBoxLayout(self.bubble_container)
        self.bubble_layout.setContentsMargins(10, 8, 10, 8)
        self.bubble_layout.setSpacing(0)

        # Calculate initial available bubble width
        self._available_bubble_width_value = self._calculate_available_bubble_width()

        # Create a layout specifically for structured content
        self.structured_content_layout = QVBoxLayout()
        self.structured_content_layout.setContentsMargins(0, 0, 0, 0)
        self.structured_content_layout.setSpacing(6)

        # Add the structured content layout to the bubble container
        self.bubble_layout.insertLayout(0, self.structured_content_layout)

        # Add all structured content widgets from the structured_content_list
        for structure_content in self.structured_content_list:
            self.add_structure_content_widget(structure_content)

        # Add the bubble container to the content area
        self.content_layout.addWidget(self.bubble_container)

        # Apply card styling
        self._apply_style()

    def _apply_style(self):
        """Apply card styling."""
        self.setStyleSheet("""
            QFrame#base_message_card {
                background-color: transparent;
                margin: 2px 0px;
            }
        """)
        self.bubble_container.setStyleSheet(f"""
            QFrame#message_bubble {{
                background-color: {self.background_color};
                border-radius: 5px;
            }}
        """)

    def _calculate_available_bubble_width(self) -> int:
        total_width = max(0, self.width())
        max_width = max(0, total_width - (self.avatar_size * 2))
        if self.content_layout:
            margins = self.content_layout.contentsMargins()
            content_width = max(0, self.content_area.width() - margins.left() - margins.right())
            max_width = min(max_width, content_width)
        return max(80, max_width)

    def _available_bubble_width(self) -> int:
        # Return the cached value
        return self._available_bubble_width_value

    def _calculate_text_width(self, max_text_width: int) -> int:
        # Find the text content widget and calculate its width
        max_line_width = 0
        for i in range(self.structured_content_layout.count()):
            item = self.structured_content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # If it's a TextContentWidget, calculate its text width
                if isinstance(widget, TextContentWidget):
                    text = str(widget.structure_content.data) if widget.structure_content.data else ""
                    if text:
                        font_metrics = widget.fontMetrics()
                        lines = text.splitlines() or [text]
                        for line in lines:
                            line_width = font_metrics.horizontalAdvance(line)
                            max_line_width = max(max_line_width, line_width)
        return min(max_line_width, max_text_width)

    def _calculate_structure_content_width(self, max_width: int) -> int:
        """Preferred width of structured content (skill, thinking, code, etc.) for bubble sizing."""
        max_content_width = 0

        # Iterate through all widgets in the structured content layout
        for i in range(self.structured_content_layout.count()):
            item = self.structured_content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Skip stretch items
                if widget is None:
                    continue

                # Calculate the preferred width for each structured content widget
                if hasattr(widget, 'sizeHint'):
                    widget_width = widget.sizeHint().width()
                    max_content_width = max(max_content_width, widget_width)

        return max_content_width

    def _update_bubble_width(self):
        self._available_bubble_width_value = self._calculate_available_bubble_width()
        max_width = self._available_bubble_width_value
        padding = self.bubble_layout.contentsMargins().left() + self.bubble_layout.contentsMargins().right()
        max_content_width = max(0, max_width - padding)

        text_width = self._calculate_text_width(max_content_width)
        structured_width = self._calculate_structure_content_width(max_content_width)
        content_width = max(text_width, structured_width)
        bubble_width = min(max_width, content_width + padding)
        actual_content_width = max(0, bubble_width - padding)

        self.bubble_container.setFixedWidth(max(1, bubble_width))

        # Update available width for all structured content widgets
        for i in range(self.structured_content_layout.count()):
            item = self.structured_content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget and hasattr(widget, 'update_available_width'):
                    widget.update_available_width(actual_content_width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_bubble_width()


    def add_structure_content_widget(self, structure_content: StructureContent):
        """Add a widget for the given StructureContent based on its type."""
        widget = None

        # Check if this is thinking content by looking at the content type
        if structure_content.content_type == ContentType.THINKING:
            # Use the ThinkingContentWidget for thinking content
            from app.ui.chat.message.thinking_content_widget import ThinkingContentWidget
            widget = ThinkingContentWidget(structure_content, self.bubble_container)
        elif structure_content.content_type == ContentType.TEXT:
            widget = TextContentWidget(structure_content, self.bubble_container)
        elif structure_content.content_type == ContentType.CODE_BLOCK:
            widget = CodeBlockWidget(structure_content, self.bubble_container)
        elif structure_content.content_type == ContentType.TABLE:
            widget = TableWidget(structure_content, self.bubble_container)
        elif structure_content.content_type == ContentType.LINK:
            widget = LinkWidget(structure_content, self.bubble_container)
        elif structure_content.content_type == ContentType.BUTTON:
            widget = ButtonWidget(structure_content, self.bubble_container)
        elif structure_content.content_type == ContentType.SKILL:
            from app.ui.chat.message.skill_content_widget import SkillContentWidget
            # Pass available width initially so the widget can adjust to bubble width
            widget = SkillContentWidget(structure_content, self.bubble_container, available_width=self._available_bubble_width_value)
        # Add more content types as needed
        else:
            # Default to text content for unrecognized types
            widget = TextContentWidget(structure_content, self.bubble_container)

        if widget:
            # Add the widget to the structured content layout
            self.structured_content_layout.addWidget(widget)
            # Trigger a width recalculation after adding structure content
            self._update_bubble_width()


    def set_content(self, content: str):
        """Set the content (replace)."""
        # Find the first TextContentWidget and update its content
        for i in range(self.structured_content_layout.count()):
            item = self.structured_content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, TextContentWidget):
                    # Update the structure content data
                    widget.structure_content.data = content
                    # Update the UI
                    for j in reversed(range(widget.layout().count())):
                        child = widget.layout().itemAt(j).widget()
                        if child is not None:
                            child.setParent(None)
                    widget._setup_ui()
                    return  # Exit after updating the first text widget
        # If no TextContentWidget was found, create one
        text_structure = StructureContent(
            content_type=ContentType.TEXT,
            data=content,
            title="",
            description=""
        )
        self.add_structure_content_widget(text_structure)
        self._update_bubble_width()

    def append_content(self, content: str):
        """Append content."""
        # Find the first TextContentWidget and append to its content
        for i in range(self.structured_content_layout.count()):
            item = self.structured_content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, TextContentWidget):
                    # Append to the structure content data
                    current_content = str(widget.structure_content.data) if widget.structure_content.data else ""
                    widget.structure_content.data = current_content + content
                    # Update the UI
                    for j in reversed(range(widget.layout().count())):
                        child = widget.layout().itemAt(j).widget()
                        if child is not None:
                            child.setParent(None)
                    widget._setup_ui()
                    self._update_bubble_width()
                    return  # Exit after updating the first text widget
        # If no TextContentWidget was found, create one with the content
        self.set_content(content)

    def get_content(self) -> str:
        """Get current content."""
        # Find the first TextContentWidget and return its content
        for i in range(self.structured_content_layout.count()):
            item = self.structured_content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, TextContentWidget):
                    return str(widget.structure_content.data) if widget.structure_content.data else ""
        # If no TextContentWidget is found, return empty string
        return ""

    def get_content_label(self):
        """Get the content label widget (for backward compatibility)."""
        # Find the first TextContentWidget and return its content label
        for i in range(self.structured_content_layout.count()):
            item = self.structured_content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, TextContentWidget):
                    # Return the actual QLabel that contains the text
                    for j in range(widget.layout().count()):
                        child_item = widget.layout().itemAt(j)
                        if child_item and child_item.widget() and isinstance(child_item.widget(), QLabel):
                            return child_item.widget()
        return None

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
        self.structure_content.get_content_label().setStyleSheet(f"""
            QLabel#message_content {{
                color: #e74c3c;
                font-size: 13px;
            }}
        """)

    def add_structured_content(self, structured: StructureContent):
        """Add structured content widget (alias for backward compatibility)."""
        self.add_structure_content_widget(structured)

    def clear_structured_content(self):
        """Clear all structured content."""
        # Remove all structured content widgets except the first text content widget if it exists
        # We'll iterate backwards to safely remove widgets
        text_widget_kept = False
        for i in reversed(range(self.bubble_layout.count())):
            item = self.bubble_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Keep the first TextContentWidget as the main content
                if isinstance(widget, TextContentWidget) and not text_widget_kept:
                    text_widget_kept = True
                    continue  # Don't remove this widget
                elif isinstance(widget, TextContentWidget) and text_widget_kept:
                    # Remove additional TextContentWidgets
                    widget.setParent(None)
                    widget.deleteLater()
                elif not isinstance(widget, TextContentWidget):
                    # Remove non-TextContentWidgets
                    widget.setParent(None)
                    widget.deleteLater()
        self._update_bubble_width()


class AgentMessageCard(BaseMessageCard):
    """Card widget for displaying an agent message in the chat.

    Features:
    - Visual differentiation by agent
    - Structured content display (text, code, tables, links, buttons)
    - Collapsible for long content
    """

    def __init__(
        self,
        agent_message: AgentMessage,
        parent=None,
        agent_color: str = "#4a90e2",  # Default color
        agent_icon: str = "🤖",  # Default icon
        crew_member_metadata: Optional[Dict[str, Any]] = None  # Metadata for crew member
    ):
        """Initialize agent message card."""
        self.agent_message = agent_message
        self.agent_color = agent_color  # Store the agent-specific color
        self.agent_icon = agent_icon  # Store the agent-specific icon
        self.crew_member_metadata = crew_member_metadata  # Store crew member metadata

        # Convert text content to StructureContent if it exists and add to structured_content
        all_structured_content = agent_message.structured_content.copy()
        text_content = agent_message.get_text_content()
        if text_content:
            text_structure = StructureContent(
                content_type=ContentType.TEXT,
                data=text_content,
                title="",
                description=""
            )
            all_structured_content.insert(0, text_structure)  # Insert at the beginning

        # Call parent constructor with agent-specific parameters
        super().__init__(
            sender_name=agent_message.sender_name or agent_message.sender_id,
            icon=self.agent_icon,
            color=self.agent_color,
            parent=parent,
            alignment=Qt.AlignLeft,
            background_color="#2b2d30",
            text_color="#e1e1e1",
            structured_content=all_structured_content
        )

        # Add crew title if available
        self._add_crew_title()

    def _add_crew_title(self):
        """Add crew title to the name widget if available."""
        if not self.crew_member_metadata or 'crew_title' not in self.crew_member_metadata:
            return

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

        # Add to the name layout - we now have a reference to name_widget
        name_layout = self.name_widget.layout()
        if name_layout:
            name_layout.addWidget(color_block_with_text)

    def update_from_agent_message(self, agent_message: AgentMessage):
        """Update the card from a new agent message."""
        # Clear existing structured content
        self.clear_structured_content()

        # Add new structured content including text content
        all_structured_content = agent_message.structured_content.copy()
        text_content = agent_message.get_text_content()
        if text_content:
            text_structure = StructureContent(
                content_type=ContentType.TEXT,
                data=text_content,
                title="",
                description=""
            )
            all_structured_content.insert(0, text_structure)  # Insert at the beginning

        # Add all structured content
        for structure_content in all_structured_content:
            self.add_structure_content_widget(structure_content)

class UserMessageCard(BaseMessageCard):
    """Card widget for displaying user messages."""

    def __init__(self, content: str = "", parent=None):
        """Initialize user message card."""
        # Convert content to structured content
        structured_content = []
        if content:
            text_structure = StructureContent(
                content_type=ContentType.TEXT,
                data=content,
                title="",
                description=""
            )
            structured_content.append(text_structure)

        super().__init__(
            sender_name="You",
            icon="👤",
            color="#35373a",
            parent=parent,
            alignment=Qt.AlignRight,
            background_color="#35373a",
            text_color="#e1e1e1",
            structured_content=structured_content
        )

        # Update the object name and styling for user messages
        self.setObjectName("user_message_card")
        self.setStyleSheet("""
            QFrame#user_message_card {
                background-color: transparent;
                margin: 2px 0px;
            }
        """)

        # Update name label styling for user messages
        self.name_label.setStyleSheet("""
            QLabel {
                color: #35373a;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        # Update bubble styling for user messages
        self.bubble_container.setStyleSheet(f"""
            QFrame#message_bubble {{
                background-color: {self.background_color};
                border-radius: 5px;
            }}
        """)
