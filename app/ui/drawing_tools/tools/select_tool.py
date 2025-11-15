"""
Select tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox
from app.ui.drawing_tools.drawing_tool import DrawingTool


class SelectTool(DrawingTool):
    """Implementation of the selection tool."""

    def __init__(self):
        self.config = {
            "mode": "矩形选择"
        }
        self.config_panel = None

    def get_id(self) -> str:
        return "select"

    def get_name(self) -> str:
        return "框选工具"

    def get_icon(self) -> str:
        return "\uE9E8"  # mti-圈选

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Selection mode label
        label = QLabel("选择模式:")
        layout.addWidget(label, 0, 0)

        # Selection mode combo box
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["矩形选择", "椭圆选择", "套索选择", "智能选择"])
        self.mode_combo.setCurrentText(self.config["mode"])
        layout.addWidget(self.mode_combo, 0, 1)

        # Add some spacing
        layout.setRowStretch(1, 1)
        
        # Connect signals
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        return widget
    
    def _on_mode_changed(self, mode: str):
        self.config["mode"] = mode

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "mode" in config:
            self.config["mode"] = config["mode"]
            if self.config_panel and hasattr(self, 'mode_combo'):
                self.mode_combo.setCurrentText(self.config["mode"])