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

    def __init__(self, structure_content: StructureContent, parent=None):
        """Initialize link widget."""
        super().__init__(structure_content, parent)
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

    def update_content(self, structure_content: StructureContent):
        """Update the widget with new structure content."""
        # Update the content
        self.structure_content = structure_content
        # Rebuild UI to reflect changes
        for i in reversed(range(self.layout().count())):
            child = self.layout().itemAt(i).widget()
            if child is not None:
                child.setParent(None)
        self._setup_ui()

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the widget."""
        return {}

    def set_state(self, state: Dict[str, Any]):
        """Set the state of the widget."""
        pass

    def get_width(self, max_width: int) -> int:
        """Get the width of the widget based on its content."""
        # For link widget, we'll calculate based on the text content
        # Link data (should be a dict with 'url' and 'text')
        if isinstance(self.structure_content.data, dict):
            text = self.structure_content.data.get('text', self.structure_content.data.get('url', ''))
        else:
            text = str(self.structure_content.data)

        if not text:
            return 0

        # Create a temporary button to measure the content width
        temp_button = QPushButton(text)
        font_metrics = temp_button.fontMetrics()

        # Calculate the width of the text
        text_width = font_metrics.horizontalAdvance(text)

        # Add some padding for the icon and spacing
        icon_width = font_metrics.horizontalAdvance("🔗")
        spacing = 16  # Approximate spacing

        total_width = text_width + icon_width + spacing
        return min(total_width, max_width)

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