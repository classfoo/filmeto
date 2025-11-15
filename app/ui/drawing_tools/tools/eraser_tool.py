"""
Eraser tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting
from app.ui.drawing_tools.settings import SizeSetting


class EraserTool(DrawingTool):
    """Implementation of the eraser tool."""

    def __init__(self):
        self.config = {
            "size": 20
        }
        self.config_panel = None
        # Define settings for this tool
        self._settings = [
            SizeSetting("Size", min_size=5, max_size=100, default_size=20)
        ]

    def get_id(self) -> str:
        return "eraser"

    def get_name(self) -> str:
        return "橡皮擦工具"

    def get_icon(self) -> str:
        return "\uE6E4"  # 橡皮擦

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Eraser size label and spinner
        size_label = QLabel("橡皮擦大小:")
        layout.addWidget(size_label, 0, 0)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 100)
        self.size_spin.setValue(self.config["size"])
        layout.addWidget(self.size_spin, 0, 1)

        # Add some spacing
        layout.setRowStretch(1, 1)
        
        # Connect signals
        self.size_spin.valueChanged.connect(self._on_size_changed)
        
        return widget
    
    def _on_size_changed(self, size: int):
        self.config["size"] = size

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "size" in config:
            self.config["size"] = config["size"]
            if self.config_panel and hasattr(self, 'size_spin'):
                self.size_spin.setValue(self.config["size"])

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the eraser tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings