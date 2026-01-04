"""Context item widget for displaying and managing context entries."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QCursor
from utils.i18n_utils import tr


class ContextItemWidget(QWidget):
    """Widget for displaying a single context item with remove button."""
    
    removed = Signal(str)  # Emitted when remove button is clicked
    
    def __init__(self, context_id: str, context_name: str, parent=None):
        """
        Initialize context item widget.
        
        Args:
            context_id: Unique identifier for the context
            context_name: Display name for the context
            parent: Parent widget
        """
        super().__init__(parent)
        self._context_id = context_id
        self._context_name = context_name
        self._is_hovered = False
        
        # Set size policy to allow widget to shrink but prefer its content size
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        self._setup_ui()
        self._apply_style()
        self.setMouseTracking(True)
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        
        # Context name label
        self.name_label = QLabel(self._context_name)
        self.name_label.setObjectName("context_item_name")
        self.name_label.setWordWrap(False)
        
        # Remove button (X icon)
        self.remove_button = QPushButton("×")
        self.remove_button.setObjectName("context_item_remove")
        self.remove_button.setFixedSize(18, 18)
        self.remove_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.remove_button.clicked.connect(lambda: self.removed.emit(self._context_id))
        
        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.remove_button, 0)
    
    def _apply_style(self):
        """Apply styling."""
        self.setStyleSheet("""
            QWidget {
                background-color: #3d3f4e;
                border: 1px solid #505254;
                border-radius: 6px;
            }
            QWidget:hover {
                background-color: #4a4c5a;
                border: 1px solid #606264;
            }
        """)
        
        self.name_label.setStyleSheet("""
            QLabel#context_item_name {
                color: #e1e1e1;
                font-size: 12px;
                background-color: transparent;
            }
        """)
        
        self.remove_button.setStyleSheet("""
            QPushButton#context_item_remove {
                background-color: transparent;
                border: none;
                border-radius: 9px;
                color: #a0a0a0;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#context_item_remove:hover {
                background-color: #5a5c6a;
                color: #ffffff;
            }
            QPushButton#context_item_remove:pressed {
                background-color: #6a6c7a;
            }
        """)
    
    def get_context_id(self) -> str:
        """Get the context ID."""
        return self._context_id
    
    def get_context_name(self) -> str:
        """Get the context name."""
        return self._context_name
    
    def sizeHint(self) -> QSize:
        """Return the preferred size of the widget."""
        # Calculate size based on content
        hint = super().sizeHint()
        # Ensure minimum width for readability
        hint.setWidth(max(hint.width(), 60))
        return hint

