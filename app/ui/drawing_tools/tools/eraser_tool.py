"""
Eraser tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QComboBox

from app.ui.drawing_tools.drawing_tool import DrawingTool


class EraserTool(DrawingTool):
    """Implementation of the eraser tool."""

    def __init__(self):
        self.config = {
            "size": 10,
            "hardness": 50,
            "opacity": 100
        }
        self.config_panel = None

    def get_id(self) -> str:
        return "eraser"

    def get_name(self) -> str:
        return "橡皮擦工具"

    def get_icon(self) -> str:
        return "\uE7F1"  # 假设这是橡皮擦的图标代码

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

        # Hardness label and combo
        hardness_label = QLabel("硬度:")
        layout.addWidget(hardness_label, 1, 0)

        self.hardness_combo = QComboBox()
        self.hardness_combo.addItems(["柔和", "中等", "坚硬"])
        if self.config["hardness"] <= 33:
            self.hardness_combo.setCurrentText("柔和")
        elif self.config["hardness"] <= 66:
            self.hardness_combo.setCurrentText("中等")
        else:
            self.hardness_combo.setCurrentText("坚硬")
        layout.addWidget(self.hardness_combo, 1, 1)

        # Opacity label and spinner
        opacity_label = QLabel("不透明度:")
        layout.addWidget(opacity_label, 2, 0)

        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(1, 100)
        self.opacity_spin.setValue(self.config["opacity"])
        self.opacity_spin.setSuffix("%")
        layout.addWidget(self.opacity_spin, 2, 1)

        # Add some spacing
        layout.setRowStretch(3, 1)
        
        # Connect signals
        self.size_spin.valueChanged.connect(self._on_size_changed)
        self.hardness_combo.currentTextChanged.connect(self._on_hardness_changed)
        self.opacity_spin.valueChanged.connect(self._on_opacity_changed)
        
        return widget
    
    def _on_size_changed(self, size: int):
        self.config["size"] = size
    
    def _on_hardness_changed(self, hardness: str):
        if hardness == "柔和":
            self.config["hardness"] = 25
        elif hardness == "中等":
            self.config["hardness"] = 50
        else:  # 坚硬
            self.config["hardness"] = 75
    
    def _on_opacity_changed(self, opacity: int):
        self.config["opacity"] = opacity

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "size" in config:
            self.config["size"] = config["size"]
            if self.config_panel and hasattr(self, 'size_spin'):
                self.size_spin.setValue(self.config["size"])
        if "hardness" in config:
            self.config["hardness"] = config["hardness"]
            if self.config_panel and hasattr(self, 'hardness_combo'):
                if self.config["hardness"] <= 33:
                    self.hardness_combo.setCurrentText("柔和")
                elif self.config["hardness"] <= 66:
                    self.hardness_combo.setCurrentText("中等")
                else:
                    self.hardness_combo.setCurrentText("坚硬")
        if "opacity" in config:
            self.config["opacity"] = config["opacity"]
            if self.config_panel and hasattr(self, 'opacity_spin'):
                self.opacity_spin.setValue(self.config["opacity"])