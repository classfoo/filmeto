"""
Text tool implementation
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QSpinBox
from app.ui.drawing_tools.drawing_tool import DrawingTool


class TextTool(DrawingTool):
    """Implementation of the text tool."""

    def __init__(self):
        self.config = {
            "size": 16,
            "font": "Arial",
            "alignment": "左对齐"
        }
        self.config_panel = None

    def get_id(self) -> str:
        return "text"

    def get_name(self) -> str:
        return "文字工具"

    def get_icon(self) -> str:
        return "\uE647"  # 文字

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Font size label and spinner
        size_label = QLabel("字体大小:")
        layout.addWidget(size_label, 0, 0)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(self.config["size"])
        layout.addWidget(self.size_spin, 0, 1)

        # Font family label and combo
        font_label = QLabel("字体:")
        layout.addWidget(font_label, 1, 0)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times", "Courier", "Helvetica"])
        self.font_combo.setCurrentText(self.config["font"])
        layout.addWidget(self.font_combo, 1, 1)

        # Text alignment label and combo
        align_label = QLabel("对齐方式:")
        layout.addWidget(align_label, 2, 0)

        self.align_combo = QComboBox()
        self.align_combo.addItems(["左对齐", "居中", "右对齐", "两端对齐"])
        self.align_combo.setCurrentText(self.config["alignment"])
        layout.addWidget(self.align_combo, 2, 1)

        # Add some spacing
        layout.setRowStretch(3, 1)
        
        # Connect signals
        self.size_spin.valueChanged.connect(self._on_size_changed)
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        self.align_combo.currentTextChanged.connect(self._on_align_changed)
        
        return widget
    
    def _on_size_changed(self, size: int):
        self.config["size"] = size
    
    def _on_font_changed(self, font: str):
        self.config["font"] = font
    
    def _on_align_changed(self, alignment: str):
        self.config["alignment"] = alignment

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "size" in config:
            self.config["size"] = config["size"]
            if self.config_panel and hasattr(self, 'size_spin'):
                self.size_spin.setValue(self.config["size"])
        if "font" in config:
            self.config["font"] = config["font"]
            if self.config_panel and hasattr(self, 'font_combo'):
                self.font_combo.setCurrentText(self.config["font"])
        if "alignment" in config:
            self.config["alignment"] = config["alignment"]
            if self.config_panel and hasattr(self, 'align_combo'):
                self.align_combo.setCurrentText(self.config["alignment"])