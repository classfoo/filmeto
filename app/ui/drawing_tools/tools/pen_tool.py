"""
Pen tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtWidgets import QGridLayout, QLabel, QSpinBox
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting
from app.ui.drawing_tools.settings import ColorSetting, SizeSetting


class PenTool(DrawingTool):
    """Implementation of the pen tool."""

    def __init__(self):
        self.config = {
            "size": 2,
            "color": "#000000"
        }
        self.config_panel = None
        # Define settings for this tool
        self._settings = [
            ColorSetting("Color"),
            SizeSetting("Size", min_size=1, max_size=20, default_size=2)
        ]

    def get_id(self) -> str:
        return "pen"

    def get_name(self) -> str:
        return "铅笔工具"

    def get_icon(self) -> str:
        return "\uE754"  # 手工2

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Brush size label and spinner
        size_label = QLabel("笔尖粗细:")
        layout.addWidget(size_label, 0, 0)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 50)
        self.size_spin.setValue(self.config["size"])
        layout.addWidget(self.size_spin, 0, 1)

        # Color label and button
        color_label = QLabel("颜色:")
        layout.addWidget(color_label, 1, 0)

        self.color_btn = QPushButton()
        self.color_btn.setText("选择颜色")
        layout.addWidget(self.color_btn, 1, 1)

        # Add some spacing
        layout.setRowStretch(2, 1)
        
        # Connect signals
        self.size_spin.valueChanged.connect(self._on_size_changed)
        self.color_btn.clicked.connect(self._on_color_clicked)
        
        return widget
    
    def _on_size_changed(self, size: int):
        self.config["size"] = size
    
    def _on_color_clicked(self):
        # In a full implementation, this would open a color picker dialog
        pass

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "size" in config:
            self.config["size"] = config["size"]
            if self.config_panel and hasattr(self, 'size_spin'):
                self.size_spin.setValue(self.config["size"])
        if "color" in config:
            self.config["color"] = config["color"]

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the pen tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings