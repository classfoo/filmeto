"""
Shape tool implementation
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtWidgets import QGridLayout, QLabel, QComboBox, QSpinBox
from app.ui.drawing_tools.drawing_tool import DrawingTool
from app.ui.drawing_tools.settings import DrawingSetting
from app.ui.drawing_tools.settings import ColorSetting, SizeSetting, BrushTypeSetting, ShapeTypeSetting


class ShapeTool(DrawingTool):
    """Implementation of the shape tool."""

    def __init__(self):
        self.config = {
            "shape": "rectangle",
            "stroke_color": "#000000",
            "stroke_size": 2,
            "line_style": "solid"
        }
        self.config_panel = None
        # Define settings for this tool
        self._settings = [
            ShapeTypeSetting("Shape"),
            ColorSetting("Stroke Color"),
            SizeSetting("Stroke Size", min_size=1, max_size=20, default_size=2),
            BrushTypeSetting("Line Style")
        ]

    def get_id(self) -> str:
        return "shape"

    def get_name(self) -> str:
        return "形状工具"

    def get_icon(self) -> str:
        return "\uE6BC"  # 形状

    def create_config_panel(self) -> QWidget:
        if self.config_panel is None:
            self.config_panel = self._create_config_ui()
        return self.config_panel

    def _create_config_ui(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        # Shape type label and combo
        shape_label = QLabel("形状:")
        layout.addWidget(shape_label, 0, 0)

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["矩形", "圆形", "线条", "箭头"])
        layout.addWidget(self.shape_combo, 0, 1)

        # Stroke color label and button
        color_label = QLabel("描边颜色:")
        layout.addWidget(color_label, 1, 0)

        self.color_btn = QPushButton()
        self.color_btn.setText("选择颜色")
        layout.addWidget(self.color_btn, 1, 1)

        # Stroke size label and spinner
        size_label = QLabel("描边粗细:")
        layout.addWidget(size_label, 2, 0)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 20)
        self.size_spin.setValue(self.config["stroke_size"])
        layout.addWidget(self.size_spin, 2, 1)

        # Line style label and combo
        style_label = QLabel("线条样式:")
        layout.addWidget(style_label, 3, 0)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["实线", "虚线", "点线", "点划线"])
        layout.addWidget(self.style_combo, 3, 1)

        # Add some spacing
        layout.setRowStretch(4, 1)
        
        # Connect signals
        self.shape_combo.currentTextChanged.connect(self._on_shape_changed)
        self.color_btn.clicked.connect(self._on_color_clicked)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        
        return widget
    
    def _on_shape_changed(self, shape: str):
        self.config["shape"] = shape
    
    def _on_color_clicked(self):
        # In a full implementation, this would open a color picker dialog
        pass
    
    def _on_size_changed(self, size: int):
        self.config["stroke_size"] = size
    
    def _on_style_changed(self, style: str):
        self.config["line_style"] = style

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if "shape" in config:
            self.config["shape"] = config["shape"]
            if self.config_panel and hasattr(self, 'shape_combo'):
                # Would need to map from internal value to display value
                pass
        if "stroke_color" in config:
            self.config["stroke_color"] = config["stroke_color"]
        if "stroke_size" in config:
            self.config["stroke_size"] = config["stroke_size"]
            if self.config_panel and hasattr(self, 'size_spin'):
                self.size_spin.setValue(self.config["stroke_size"])
        if "line_style" in config:
            self.config["line_style"] = config["line_style"]
            if self.config_panel and hasattr(self, 'style_combo'):
                # Would need to map from internal value to display value
                pass

    def get_settings(self) -> List[DrawingSetting]:
        """
        Get the list of settings for the shape tool.
        Returns:
            List[DrawingSetting]: The list of settings for this tool
        """
        return self._settings