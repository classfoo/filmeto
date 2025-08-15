"""
OpacitySetting - Opacity adjustment setting for drawing tools
"""
from typing import Optional
from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel, QSlider, QSpinBox, QHBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt
from app.ui.drawing_tools.drawing_setting import DrawingSetting


class OpacitySetting(DrawingSetting):
    """
    Opacity adjustment setting (0-100%).
    Button shows current opacity percentage.
    """
    
    def __init__(self, name: str = "opacity", default_opacity: int = 100):
        super().__init__(name, icon="\uE6D1")  # Opacity icon
        self._value = default_opacity  # 0-100
    
    def create_button(self) -> QWidget:
        """Create opacity indicator button with text label"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Create the opacity button
        btn = QPushButton()
        btn.setFixedHeight(28)
        btn.setObjectName("setting_opacity_btn")
        
        # Add widgets to layout (text on the left, button on the right)
        layout.addWidget(btn)
        layout.addStretch()
        
        # Update button text
        self._update_button_text(btn)
        
        btn.setStyleSheet("""
            QPushButton#setting_opacity_btn {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 2px solid #4080ff;  /* 始终显示高亮边框 */
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton#setting_opacity_btn:hover {
                background-color: #4a4c5e;
                border: 2px solid #4080ff;
            }
        """)
        
        # Store references for later use
        container.opacity_button = btn
        return container
    
    def _update_button_text(self, btn: QPushButton):
        """Update button to show current opacity"""
        btn.setText(f"{self.name}: {self._value}%")
        btn.setToolTip(f"{self.name}: {self._value}%")
        btn.adjustSize()

    
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
    
    def get_value(self) -> str:
        return str(self._value)
    
    def set_value(self, value: str):
        opacity = int(value)
        self._value = opacity
        if self._button:
            self._update_button_text(self._button.opacity_button)
        self.value_changed.emit(opacity)
