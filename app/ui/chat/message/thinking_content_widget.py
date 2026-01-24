"""
Thinking content widget for displaying agent thought processes in message bubbles.
This widget displays the agent's thinking process with a distinct visual style.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QFrame
)
from agent.chat.agent_chat_message import StructureContent, ContentType
from app.ui.chat.message.base_structured_content_widget import BaseStructuredContentWidget


class ThinkingContentWidget(BaseStructuredContentWidget):
    """Widget to display agent thinking process with a distinct visual style."""

    def __init__(self, structure_content: StructureContent, parent=None):
        """
        Initialize the thinking content widget.

        Args:
            structure_content: StructureContent object containing thinking data
            parent: Parent widget
        """
        # If no structure_content is provided, create a default one for thinking
        if structure_content is None:
            from agent.chat.agent_chat_message import StructureContent
            structure_content = StructureContent(
                content_type=ContentType.THINKING,
                data="",
                title="Thinking Process",
                description="Agent's thought process"
            )
        super().__init__(structure_content, parent)

    def _setup_ui(self):
        """Set up the UI for the thinking content widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Create a container frame for the thinking content
        thinking_frame = QFrame(self)
        thinking_frame.setObjectName("thinking_frame")
        thinking_frame.setStyleSheet("""
            QFrame#thinking_frame {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px;
            }
        """)

        # Layout for the thinking frame
        frame_layout = QVBoxLayout(thinking_frame)
        frame_layout.setContentsMargins(8, 8, 8, 8)
        frame_layout.setSpacing(4)

        # Add a header label for the thinking section
        header_label = QLabel("🤔 Thinking Process", thinking_frame)
        header_label.setObjectName("thinking_header")
        header_label.setStyleSheet("""
            QLabel#thinking_header {
                color: #a0a0a0;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 4px;
            }
        """)
        header_label.setAlignment(Qt.AlignLeft)

        # Create the thinking content label
        self.thinking_label = QLabel("", thinking_frame)  # Initially empty, will be set by update_content
        self.thinking_label.setObjectName("thinking_content")
        self.thinking_label.setWordWrap(True)
        self.thinking_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.thinking_label.setStyleSheet("""
            QLabel#thinking_content {
                color: #c0c0c0;
                font-size: 13px;
                font-style: italic;
            }
        """)

        # Add header and content to frame layout
        frame_layout.addWidget(header_label)
        frame_layout.addWidget(self.thinking_label)

        # Add the frame to the main layout
        layout.addWidget(thinking_frame)

        # Apply the initial content
        self.update_content(self.structure_content)

    def update_content(self, structure_content):
        """
        Update the widget with new structure content.

        Args:
            structure_content: The new structure content to display
        """
        self.structure_content = structure_content
        # Extract the thinking content from the structure_content data
        if isinstance(structure_content.data, str):
            content = structure_content.data
        elif isinstance(structure_content.data, dict) and "thinking" in structure_content.data:
            content = structure_content.data["thinking"]
        else:
            content = str(structure_content.data) if structure_content.data else ""

        self.thinking_label.setText(content)

    def get_state(self):
        """
        Get the current state of the widget.

        Returns:
            Dictionary representing the current state
        """
        return {
            "content": self.thinking_label.text(),
            "title": self.structure_content.title,
            "description": self.structure_content.description
        }

    def set_state(self, state):
        """
        Set the state of the widget.

        Args:
            state: Dictionary representing the state to set
        """
        if "content" in state:
            self.thinking_label.setText(state["content"])
        if "title" in state:
            self.structure_content.title = state["title"]
        if "description" in state:
            self.structure_content.description = state["description"]

    def update_available_width(self, width: int):
        """Update the available width."""
        # Update the maximum width of the content label
        self.thinking_label.setMaximumWidth(width - 20)  # Account for margins