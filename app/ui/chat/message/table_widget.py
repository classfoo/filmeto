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
from app.ui.chat.message.base_structured_content_widget import BaseStructuredContentWidget


class TableWidget(BaseStructuredContentWidget):
    """Widget for displaying table content."""

    def __init__(self, structure_content: StructureContent, parent=None):
        """Initialize table widget."""
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
        if isinstance(self.structure_content.data, dict):
            headers = self.structure_content.data.get('headers', [])
            rows = self.structure_content.data.get('rows', [])

            if headers:
                table_widget.setColumnCount(len(headers))
                table_widget.setHorizontalHeaderLabels(headers)

            if rows:
                table_widget.setRowCount(len(rows))
                for row_idx, row_data in enumerate(rows):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data))
                        table_widget.setItem(row_idx, col_idx, item)
        elif isinstance(self.structure_content.data, list):
            # If data is a list of lists, treat each inner list as a row
            if self.structure_content.data:
                num_cols = max(len(row) for row in self.structure_content.data) if self.structure_content.data else 0
                table_widget.setColumnCount(num_cols)
                table_widget.setRowCount(len(self.structure_content.data))

                for row_idx, row_data in enumerate(self.structure_content.data):
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
        # For table widget, we'll calculate based on the table content
        # Calculate the width based on the number of columns and content
        estimated_width = 0

        # If data is a dict with headers and rows
        if isinstance(self.structure_content.data, dict):
            headers = self.structure_content.data.get('headers', [])
            rows = self.structure_content.data.get('rows', [])

            # Estimate width based on headers
            for header in headers:
                temp_label = QLabel(str(header))
                font_metrics = temp_label.fontMetrics()
                estimated_width += font_metrics.horizontalAdvance(str(header)) + 20  # Add padding

            # If no headers, estimate based on first row
            if not headers and rows:
                first_row = rows[0] if rows else []
                for cell in first_row:
                    temp_label = QLabel(str(cell))
                    font_metrics = temp_label.fontMetrics()
                    estimated_width += font_metrics.horizontalAdvance(str(cell)) + 20  # Add padding
        elif isinstance(self.structure_content.data, list):
            # If data is a list of lists
            if self.structure_content.data:
                first_row = self.structure_content.data[0]
                for cell in first_row:
                    temp_label = QLabel(str(cell))
                    font_metrics = temp_label.fontMetrics()
                    estimated_width += font_metrics.horizontalAdvance(str(cell)) + 20  # Add padding

        # Add some extra space for table borders and margins
        estimated_width += 40  # Additional padding for table elements

        return min(estimated_width, max_width)