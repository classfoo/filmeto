"""
Zoom tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QPushButton
from app.ui.drawing_tools.drawing_tool import DrawingTool


class ZoomTool(DrawingTool):
    """Implementation of the zoom tool."""

    def __init__(self):
        self.config = {
            "level": "100%"
        }
        self.config_panel = None

    def get_id(self) -> str:
        return "zoom"

    def get_name(self) -> str:
        return "缩放工具"

    def get_icon(self) -> str:
        return "\uE6E2"  # zoom

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Zoom level label and combo
        zoom_label = QLabel("缩放级别:")
        layout.addWidget(zoom_label, 0, 0)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["25%", "50%", "75%", "100%", "150%", "200%", "400%"])
        self.level_combo.setCurrentText(self.config["level"])
        layout.addWidget(self.level_combo, 0, 1)

        # Fit to screen button
        self.fit_screen_btn = QPushButton()
        self.fit_screen_btn.setText("适应屏幕")
        layout.addWidget(self.fit_screen_btn, 1, 0, 1, 2)

        # Add some spacing
        layout.setRowStretch(2, 1)
        
        # Connect signals
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        self.fit_screen_btn.clicked.connect(self._on_fit_screen_clicked)
        
        return widget
    
    def _on_level_changed(self, level: str):
        self.config["level"] = level
    
    def _on_fit_screen_clicked(self):
        # In a full implementation, this would trigger fit to screen functionality
        pass

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "level" in config:
            self.config["level"] = config["level"]
            if self.config_panel and hasattr(self, 'level_combo'):
                self.level_combo.setCurrentText(self.config["level"])