"""Attachments panel for reference management."""

from PySide6.QtWidgets import QVBoxLayout, QLabel
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace


class AttachmentsPanel(BasePanel):
    """Panel for managing attachments and references."""
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the attachments panel."""
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components."""
        self.set_panel_title("Attachments")
        
        label = QLabel("Attachments Panel\n(Coming soon)", self)
        label.setObjectName("panel_placeholder_label")
        label.setStyleSheet("""
            QLabel#panel_placeholder_label {
                color: #bbbbbb;
                font-size: 14px;
                padding: 20px;
            }
        """)
        self.content_layout.addWidget(label)
