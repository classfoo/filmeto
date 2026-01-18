"""Widget for displaying code blocks in chat messages."""

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