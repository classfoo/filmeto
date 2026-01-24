"""Widget for displaying link content in chat messages."""

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


class LinkWidget(BaseStructuredContentWidget):
    """Widget for displaying link content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize link widget."""
        super().__init__(structure_content=content, parent=parent)
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
        if isinstance(self.structure_content.data, dict):
            url = self.structure_content.data.get('url', '')
            text = self.structure_content.data.get('text', url)
        else:
            url = str(self.structure_content.data)
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