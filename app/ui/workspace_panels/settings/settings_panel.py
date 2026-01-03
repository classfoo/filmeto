"""Settings panel for application settings."""

from PySide6.QtWidgets import QVBoxLayout
from app.ui.workspace_panels.base_panel import BasePanel
from app.data.workspace import Workspace
from app.ui.settings import SettingsWidget


class SettingsPanel(BasePanel):
    """Panel for application settings."""
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the settings panel."""
        super().__init__(workspace, parent)
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Use existing SettingsWidget
        self.settings_widget = SettingsWidget(self.workspace, self)
        layout.addWidget(self.settings_widget)
    
    def on_activated(self):
        """Called when panel becomes visible."""
        super().on_activated()
        print("✅ Settings panel activated")
    
    def on_deactivated(self):
        """Called when panel is hidden."""
        super().on_deactivated()
        print("⏸️ Settings panel deactivated")

