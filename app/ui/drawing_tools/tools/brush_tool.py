"""
Brush tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QSpinBox
from app.ui.drawing_tools.drawing_tool import DrawingTool


class BrushTool(DrawingTool):
    """Implementation of the brush tool."""

    def __init__(self):
        self.config = {
            "style": "圆形",
            "size": 5,
            "opacity": 100
        }
        self.config_panel = None

    def get_id(self) -> str:
        return "brush"

    def get_name(self) -> str:
        return "画笔工具"

    def get_icon(self) -> str:
        return "\uE648"  # 37画笔

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Brush style label and combo
        style_label = QLabel("笔刷样式:")
        layout.addWidget(style_label, 0, 0)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["圆形", "方块", "纹理1", "纹理2"])
        self.style_combo.setCurrentText(self.config["style"])
        layout.addWidget(self.style_combo, 0, 1)

        # Brush size label and spinner
        size_label = QLabel("笔尖粗细:")
        layout.addWidget(size_label, 1, 0)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(self.config["size"])
        layout.addWidget(self.size_spin, 1, 1)

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
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        self.opacity_spin.valueChanged.connect(self._on_opacity_changed)
        
        return widget
    
    def _on_style_changed(self, style: str):
        self.config["style"] = style
    
    def _on_size_changed(self, size: int):
        self.config["size"] = size
    
    def _on_opacity_changed(self, opacity: int):
        self.config["opacity"] = opacity

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "style" in config:
            self.config["style"] = config["style"]
            if self.config_panel and hasattr(self, 'style_combo'):
                self.style_combo.setCurrentText(self.config["style"])
        if "size" in config:
            self.config["size"] = config["size"]
            if self.config_panel and hasattr(self, 'size_spin'):
                self.size_spin.setValue(self.config["size"])
        if "opacity" in config:
            self.config["opacity"] = config["opacity"]
            if self.config_panel and hasattr(self, 'opacity_spin'):
                self.opacity_spin.setValue(self.config["opacity"])