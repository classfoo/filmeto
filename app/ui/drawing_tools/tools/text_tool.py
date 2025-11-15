"""
Text tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtWidgets import QGridLayout, QLabel, QSpinBox, QComboBox
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting
from app.ui.drawing_tools.settings import ColorSetting, SizeSetting


class TextTool(DrawingTool):
    """Implementation of the text tool."""

    def __init__(self):
        self.config = {
            "font_size": 14,
            "text_color": "#000000",
            "font_family": "Arial"
        }
        self.config_panel = None
        # Define settings for this tool
        self._settings = [
            ColorSetting("Text Color"),
            SizeSetting("Font Size", min_size=8, max_size=72, default_size=14)
        ]

    def get_id(self) -> str:
        return "text"

    def get_name(self) -> str:
        return "文字工具"

    def get_icon(self) -> str:
        return "\uE6A4"  # 字体

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
        self.size_spin.setValue(self.config["font_size"])
        layout.addWidget(self.size_spin, 0, 1)

        # Text color label and button
        color_label = QLabel("文字颜色:")
        layout.addWidget(color_label, 1, 0)

        self.color_btn = QPushButton()
        self.color_btn.setText("选择颜色")
        layout.addWidget(self.color_btn, 1, 1)

        # Font family label and combo
        font_label = QLabel("字体:")
        layout.addWidget(font_label, 2, 0)

        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "Courier New", "微软雅黑", "宋体"])
        self.font_combo.setCurrentText(self.config["font_family"])
        layout.addWidget(self.font_combo, 2, 1)

        # Add some spacing
        layout.setRowStretch(3, 1)
        
        # Connect signals
        self.size_spin.valueChanged.connect(self._on_size_changed)
        self.color_btn.clicked.connect(self._on_color_clicked)
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        
        return widget
    
    def _on_size_changed(self, size: int):
        self.config["font_size"] = size
    
    def _on_color_clicked(self):
        # In a full implementation, this would open a color picker dialog
        pass
    
    def _on_font_changed(self, font: str):
        self.config["font_family"] = font

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "font_size" in config:
            self.config["font_size"] = config["font_size"]
            if self.config_panel and hasattr(self, 'size_spin'):
                self.size_spin.setValue(self.config["font_size"])
        if "text_color" in config:
            self.config["text_color"] = config["text_color"]
        if "font_family" in config:
            self.config["font_family"] = config["font_family"]
            if self.config_panel and hasattr(self, 'font_combo'):
                self.font_combo.setCurrentText(self.config["font_family"])

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the text tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings