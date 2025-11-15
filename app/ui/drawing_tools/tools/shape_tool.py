"""
Shape tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QSpinBox
from app.ui.drawing_tools.drawing_tool import DrawingTool


class ShapeTool(DrawingTool):
    """Implementation of the shape tool."""

    def __init__(self):
        self.config = {
            "type": "矩形",
            "fill": "实心",
            "width": 2
        }
        self.config_panel = None

    def get_id(self) -> str:
        return "shape"

    def get_name(self) -> str:
        return "图形工具"

    def get_icon(self) -> str:
        return "\uE716"  # shape

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Shape type label and combo
        type_label = QLabel("形状类型:")
        layout.addWidget(type_label, 0, 0)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["矩形", "椭圆", "直线", "多边形"])
        self.type_combo.setCurrentText(self.config["type"])
        layout.addWidget(self.type_combo, 0, 1)

        # Fill style label and combo
        fill_label = QLabel("填充样式:")
        layout.addWidget(fill_label, 1, 0)

        self.fill_combo = QComboBox()
        self.fill_combo.addItems(["实心", "空心", "渐变"])
        self.fill_combo.setCurrentText(self.config["fill"])
        layout.addWidget(self.fill_combo, 1, 1)

        # Line width label and spinner
        width_label = QLabel("线条宽度:")
        layout.addWidget(width_label, 2, 0)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 20)
        self.width_spin.setValue(self.config["width"])
        layout.addWidget(self.width_spin, 2, 1)

        # Add some spacing
        layout.setRowStretch(3, 1)
        
        # Connect signals
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.fill_combo.currentTextChanged.connect(self._on_fill_changed)
        self.width_spin.valueChanged.connect(self._on_width_changed)
        
        return widget
    
    def _on_type_changed(self, shape_type: str):
        self.config["type"] = shape_type
    
    def _on_fill_changed(self, fill: str):
        self.config["fill"] = fill
    
    def _on_width_changed(self, width: int):
        self.config["width"] = width

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "type" in config:
            self.config["type"] = config["type"]
            if self.config_panel and hasattr(self, 'type_combo'):
                self.type_combo.setCurrentText(self.config["type"])
        if "fill" in config:
            self.config["fill"] = config["fill"]
            if self.config_panel and hasattr(self, 'fill_combo'):
                self.fill_combo.setCurrentText(self.config["fill"])
        if "width" in config:
            self.config["width"] = config["width"]
            if self.config_panel and hasattr(self, 'width_spin'):
                self.width_spin.setValue(self.config["width"])