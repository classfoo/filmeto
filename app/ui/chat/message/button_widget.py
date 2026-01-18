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