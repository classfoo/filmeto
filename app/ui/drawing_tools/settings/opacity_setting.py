"""
OpacitySetting - Opacity/transparency setting for drawing tools
"""
from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox
from PySide6.QtCore import Qt
from app.ui.drawing_tools.drawing_setting import DrawingSetting


class OpacitySetting(DrawingSetting):
    """
    Opacity adjustment setting (0-100%).
    Button shows current opacity percentage.
    """
    
    def __init__(self, name: str = "Opacity", default_opacity: int = 100):
        super().__init__(name, icon="\uE6D1")  # Opacity icon
        self._value = default_opacity  # 0-100
    
    def create_button(self) -> QPushButton:
        """Create opacity indicator button (28x28px)"""
        btn = QPushButton()
        btn.setFixedSize(28, 28)
        btn.setObjectName("setting_opacity_btn")
        
        self._update_button_text(btn)
        
        btn.setStyleSheet("""
            QPushButton#setting_opacity_btn {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 1px solid #505254;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton#setting_opacity_btn:hover {
                background-color: #4a4c5e;
                border: 1px solid #5a5c6e;
            }
        """)
        
        return btn
    
    def _update_button_text(self, btn: QPushButton):
        """Update button to show current opacity"""
        btn.setText(f"{self._value}%")
        btn.setToolTip(f"{self.name}: {self._value}%")
    
    def create_panel(self) -> QFrame:
        """Create opacity adjustment panel"""
        panel = QFrame()
        panel.setObjectName("setting_panel")
        panel.setFixedWidth(220)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel(f"{self.name}")
        title.setStyleSheet("font-weight: bold; color: #E1E1E1; font-size: 12px;")
        layout.addWidget(title)
        
        # Slider and spinbox
        control_layout = QHBoxLayout()
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(self._value)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #1e1f22;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4080ff;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)
        
        spinbox = QSpinBox()
        spinbox.setRange(0, 100)
        spinbox.setValue(self._value)
        spinbox.setSuffix("%")
        spinbox.setFixedWidth(60)
        spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #1e1f22;
                color: #E1E1E1;
                border: 1px solid #505254;
                border-radius: 3px;
                padding: 2px;
                font-size: 11px;
            }
        """)
        
        # Connect controls
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(self.set_value)
        
        control_layout.addWidget(slider, 1)
        control_layout.addWidget(spinbox)
        layout.addLayout(control_layout)
        
        panel.setStyleSheet("""
            QFrame#setting_panel {
                background-color: #2b2d30;
                border: 1px solid #505254;
                border-radius: 6px;
            }
        """)
        
        return panel
    
    def get_value(self) -> int:
        return self._value
    
    def set_value(self, value: int):
        self._value = value
        if self._button:
            self._update_button_text(self._button)
        self.value_changed.emit(value)
