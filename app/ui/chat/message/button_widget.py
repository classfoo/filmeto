"""Widget for displaying button content in chat messages."""

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


class ButtonWidget(BaseStructuredContentWidget):
    """Widget for displaying button content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize button widget."""
        super().__init__(structure_content=content, parent=parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Button data (should be a dict with 'text' and 'action')
        if isinstance(self.structure_content.data, dict):
            text = self.structure_content.data.get('text', 'Button')
            action = self.structure_content.data.get('action', '')
        else:
            text = str(self.structure_content.data)
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

    def _handle_button_click(self, action: str):
        """Handle button click."""
        # Find the parent AgentMessageCard and emit the reference clicked signal
        parent = self.parent()
        while parent:
            if hasattr(parent, 'reference_clicked'):
                parent.reference_clicked.emit('button', action)
                break
            parent = parent.parent()

        print(f"Button clicked with action: {action}")

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
        # Update the structure content with state data
        title = state.get("title", "")
        description = state.get("description", "")
        data = state.get("data", {})
        
        # Update the UI with the new state
        for i in reversed(range(self.layout().count())): 
            child = self.layout().itemAt(i).widget()
            if child is not None:
                child.setParent(None)
        self.structure_content.title = title
        self.structure_content.description = description
        self.structure_content.data = data
        self._setup_ui()