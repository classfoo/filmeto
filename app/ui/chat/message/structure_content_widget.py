"""
Structure content widget for displaying both plain text and structured content in message bubbles.
This widget combines text content and structured content in a unified way.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSizePolicy
)


class StructureContentWidget(QWidget):
    """Widget to display both plain text content and structured content in a unified way."""
    
    def __init__(self, initial_content: str = "", parent=None):
        """Initialize the structure content widget."""
        super().__init__(parent)
        
        self._setup_ui(initial_content)
    
    def _setup_ui(self, initial_content: str):
        """Set up the UI for the structure content widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create the main content label for text content
        self.content_label = QLabel(initial_content, self)
        self.content_label.setObjectName("message_content")
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        layout.addWidget(self.content_label)
        
        # Container for additional structured content widgets
        self.structured_content_container = QWidget(self)
        self.structured_content_layout = QVBoxLayout(self.structured_content_container)
        self.structured_content_layout.setContentsMargins(0, 0, 0, 0)
        self.structured_content_layout.setSpacing(6)
        
        layout.addWidget(self.structured_content_container)
    
    def set_content(self, content: str):
        """Set the text content."""
        self.content_label.setText(content)
    
    def append_content(self, content: str):
        """Append text content."""
        current_text = self.content_label.text()
        self.content_label.setText(current_text + content)
    
    def get_content(self) -> str:
        """Get the current text content."""
        return self.content_label.text()
    
    def add_structured_content_widget(self, widget):
        """Add a structured content widget."""
        self.structured_content_layout.addWidget(widget)
    
    def clear_structured_content(self):
        """Clear all structured content widgets."""
        for i in reversed(range(self.structured_content_layout.count())):
            widget = self.structured_content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
    
    def get_content_label(self):
        """Get the content label widget."""
        return self.content_label
    
    def sizeHint(self):
        """Return the recommended size for this widget."""
        # Calculate the combined size hint of all child widgets
        content_hint = self.content_label.sizeHint()
        structured_hint = self.structured_content_container.sizeHint()

        # Return the combined size
        width = max(content_hint.width(), structured_hint.width())
        height = content_hint.height() + structured_hint.height()

        return QSize(width, height)

    def minimumSizeHint(self):
        """Return the minimum size for this widget."""
        content_min = self.content_label.minimumSizeHint()
        structured_min = self.structured_content_container.minimumSizeHint()

        # Return the combined minimum size
        width = max(content_min.width(), structured_min.width())
        height = content_min.height() + structured_min.height()

        return QSize(width, height)

    def heightForWidth(self, width: int) -> int:
        """Calculate the height for a given width."""
        content_height = self.content_label.heightForWidth(width)
        structured_height = self.structured_content_container.heightForWidth(width)
        return content_height + structured_height

    def get_content_size(self) -> tuple[int, int]:
        """Get the size of the content area."""
        return (self.content_label.width(), self.content_label.height())

    def get_structured_content_size(self) -> tuple[int, int]:
        """Get the size of the structured content area."""
        return (self.structured_content_container.width(), self.structured_content_container.height())

    def get_total_size(self) -> tuple[int, int]:
        """Get the total size of the widget."""
        content_size = self.get_content_size()
        structured_size = self.get_structured_content_size()

        width = max(content_size[0], structured_size[0])
        height = content_size[1] + structured_size[1]

        return (width, height)