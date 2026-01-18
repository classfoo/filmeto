"""Widget for displaying table content in chat messages."""

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


class TableWidget(QWidget):
    """Widget for displaying table content."""

    def __init__(self, content: StructureContent, parent=None):
        """Initialize table widget."""
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

        # Table content
        table_widget = QTableWidget(self)
        table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #d4d4d4;
                gridline-color: #3c3c3c;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #333337;
                color: #cccccc;
                padding: 4px;
                border: 1px solid #444;
            }
        """)

        # Populate table from data (should be a dict with 'headers' and 'rows')
        if isinstance(self.content.data, dict):
            headers = self.content.data.get('headers', [])
            rows = self.content.data.get('rows', [])

            if headers:
                table_widget.setColumnCount(len(headers))
                table_widget.setHorizontalHeaderLabels(headers)

            if rows:
                table_widget.setRowCount(len(rows))
                for row_idx, row_data in enumerate(rows):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data))
                        table_widget.setItem(row_idx, col_idx, item)
        elif isinstance(self.content.data, list):
            # If data is a list of lists, treat each inner list as a row
            if self.content.data:
                num_cols = max(len(row) for row in self.content.data) if self.content.data else 0
                table_widget.setColumnCount(num_cols)
                table_widget.setRowCount(len(self.content.data))

                for row_idx, row_data in enumerate(self.content.data):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data))
                        table_widget.setItem(row_idx, col_idx, item)

        layout.addWidget(table_widget)

        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)