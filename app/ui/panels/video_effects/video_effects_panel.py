"""Video effects panel for video processing."""

from PySide6.QtWidgets import QVBoxLayout, QLabel
from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace


class VideoEffectsPanel(BasePanel):
    """Panel for video filters and effects."""
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the video effects panel."""
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        label = QLabel("Video Effects Panel\n(Coming soon)", self)
        label.setObjectName("panel_placeholder_label")
        label.setStyleSheet("""
            QLabel#panel_placeholder_label {
                color: #bbbbbb;
                font-size: 14px;
                padding: 20px;
            }
        """)
        layout.addWidget(label)
