"""
Adjust tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox
from app.ui.drawing_tools.drawing_tool import DrawingTool


class AdjustTool(DrawingTool):
    """Implementation of the color adjustment tool."""

    def __init__(self):
        self.config = {
            "brightness": 0,
            "contrast": 0,
            "saturation": 0
        }
        self.config_panel = None

    def get_id(self) -> str:
        return "adjust"

    def get_name(self) -> str:
        return "色彩调整工具"

    def get_icon(self) -> str:
        return "\uE619"  # 调色板

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Brightness label and spinner
        bright_label = QLabel("亮度:")
        layout.addWidget(bright_label, 0, 0)

        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(-100, 100)
        self.brightness_spin.setValue(self.config["brightness"])
        layout.addWidget(self.brightness_spin, 0, 1)

        # Contrast label and spinner
        contrast_label = QLabel("对比度:")
        layout.addWidget(contrast_label, 1, 0)

        self.contrast_spin = QSpinBox()
        self.contrast_spin.setRange(-100, 100)
        self.contrast_spin.setValue(self.config["contrast"])
        layout.addWidget(self.contrast_spin, 1, 1)

        # Saturation label and spinner
        sat_label = QLabel("饱和度:")
        layout.addWidget(sat_label, 2, 0)

        self.saturation_spin = QSpinBox()
        self.saturation_spin.setRange(-100, 100)
        self.saturation_spin.setValue(self.config["saturation"])
        layout.addWidget(self.saturation_spin, 2, 1)

        # Add some spacing
        layout.setRowStretch(3, 1)
        
        # Connect signals
        self.brightness_spin.valueChanged.connect(self._on_brightness_changed)
        self.contrast_spin.valueChanged.connect(self._on_contrast_changed)
        self.saturation_spin.valueChanged.connect(self._on_saturation_changed)
        
        return widget
    
    def _on_brightness_changed(self, brightness: int):
        self.config["brightness"] = brightness
    
    def _on_contrast_changed(self, contrast: int):
        self.config["contrast"] = contrast
    
    def _on_saturation_changed(self, saturation: int):
        self.config["saturation"] = saturation

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "brightness" in config:
            self.config["brightness"] = config["brightness"]
            if self.config_panel and hasattr(self, 'brightness_spin'):
                self.brightness_spin.setValue(self.config["brightness"])
        if "contrast" in config:
            self.config["contrast"] = config["contrast"]
            if self.config_panel and hasattr(self, 'contrast_spin'):
                self.contrast_spin.setValue(self.config["contrast"])
        if "saturation" in config:
            self.config["saturation"] = config["saturation"]
            if self.config_panel and hasattr(self, 'saturation_spin'):
                self.saturation_spin.setValue(self.config["saturation"])