"""Widget for displaying text content in chat messages."""

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
from app.ui.chat.message.base_structured_content_widget import BaseStructuredContentWidget


class TextContentWidget(BaseStructuredContentWidget):
    """Widget for displaying text content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize text content widget."""
        super().__init__(structure_content=content, parent=parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Title if available
        if self.structure_content.title:
            title_label = QLabel(self.structure_content.title, self)
            title_label.setStyleSheet("""
                QLabel {
                    color: #7c4dff;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            layout.addWidget(title_label)

        # Description if available
        if self.structure_content.description:
            desc_label = QLabel(self.structure_content.description, self)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 11px;
                }
            """)
            layout.addWidget(desc_label)

        # Actual text content
        text_label = QLabel(str(self.structure_content.data), self)
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

    def update_content(self, structure_content: StructureContent):
        """
        Update the widget with new structure content.
        
        Args:
            structure_content: The new structure content to display
        """
        self.structure_content = structure_content
        # Clear and re-layout the widget
        for i in reversed(range(self.layout().count())): 
            child = self.layout().itemAt(i).widget()
            if child is not None:
                child.setParent(None)
        self._setup_ui()

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the widget.
        
        Returns:
            Dictionary representing the current state
        """
        return {
            "title": self.structure_content.title,
            "description": self.structure_content.description,
            "data": self.structure_content.data,
        }

    def set_state(self, state: Dict[str, Any]):
        """
        Set the state of the widget.
        
        Args:
            state: Dictionary representing the state to set
        """
        # Create a new StructureContent with the state data
        # Note: This assumes we can modify the structure_content in place
        # For a complete implementation, we might need to update the actual content
        # based on the state provided
        title = state.get("title", "")
        description = state.get("description", "")
        data = state.get("data", "")
        
        # Update the UI with the new state
        for i in reversed(range(self.layout().count())): 
            child = self.layout().itemAt(i).widget()
            if child is not None:
                child.setParent(None)
        self.structure_content.title = title
        self.structure_content.description = description
        self.structure_content.data = data
        self._setup_ui()