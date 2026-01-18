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