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

    def __init__(self, structure_content: StructureContent, parent=None):
        """Initialize text content widget."""
        super().__init__(structure_content, parent)
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
        text = str(self.structure_content.data) or ""
        if not text:
            return 0
        # Get the font metrics for the text label
        # Since we don't have a direct reference to the label in the layout,
        # we'll create a temporary label to get the font metrics
        temp_label = QLabel(text)
        font_metrics = temp_label.fontMetrics()
        lines = text.splitlines() or [text]
        max_line_width = 0
        for line in lines:
            max_line_width = max(max_line_width, font_metrics.horizontalAdvance(line))
        return min(max_line_width, max_width)