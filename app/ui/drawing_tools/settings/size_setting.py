"""
SizeSetting - Size adjustment setting for drawing tools
"""
from typing import Optional
from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel, QSlider, QSpinBox, QHBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt
from app.ui.drawing_tools.drawing_setting import DrawingSetting


class SizeSetting(DrawingSetting):
    """
    Size adjustment setting with slider.
    Button shows current size value.
    """
    
    def __init__(self, name: str = "size", min_size: int = 1, max_size: int = 50, default_size: int = 5):
        super().__init__(name, icon="\uE648")  # Brush icon
        self._value = default_size
        self._min_size = min_size
        self._max_size = max_size
    
    def create_button(self) -> QWidget:
        """Create size indicator button with text label"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Create the text label
        label = QLabel(self.name)
        label.setStyleSheet("color: #E1E1E1; font-size: 11px; background: transparent; border: none;")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setWordWrap(False)
        label.setTextFormat(Qt.PlainText)
        label.setTextInteractionFlags(Qt.NoTextInteraction)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        label.adjustSize()  # Fit to text content
        
        # Create the size button
        btn = QPushButton("size:12px")
        btn.setFixedHeight(28)
        btn.setObjectName("setting_size_btn")
        
        # Add widgets to layout (text on the left, button on the right)
        #layout.addWidget(label)
        layout.addWidget(btn)
        layout.addStretch()
        
        # Update button text
        self._update_button_text(btn)
        
        btn.setStyleSheet("""
            QPushButton#setting_size_btn {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 2px solid #4080ff;  /* 始终显示高亮边框 */
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton#setting_size_btn:hover {
                background-color: #4a4c5e;
                border: 2px solid #4080ff;
            }
        """)
        
        # Store references for later use
        container.size_button = btn
        container.label = label
        
        return container
    
    def _update_button_text(self, btn: QPushButton):
        """Update button to show current size"""
        btn.setText(f"{self.name}: {self._value}px")
        btn.setToolTip(f"{self.name}: {self._value}px")
    
    def create_panel(self) -> QFrame:
        """Create size adjustment panel"""
        panel = QFrame()
        panel.setObjectName("setting_panel")
        panel.setFixedWidth(240)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel(f"{self.name} Adjustment")
        title.setStyleSheet("font-weight: bold; color: #E1E1E1; font-size: 12px;")
        layout.addWidget(title)
        
        # Slider and spinbox
        control_layout = QHBoxLayout()
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(self._min_size, self._max_size)
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
        spinbox.setRange(self._min_size, self._max_size)
        spinbox.setValue(self._value)
        spinbox.setFixedWidth(55)
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
        
        # Size preview
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setFixedHeight(35)
        
        def update_preview(size):
            dot_size = min(size, 20)  # Cap visual size at 20
            preview_label.setText(f"● {size}px")
            preview_label.setStyleSheet(f"font-size: {dot_size}px; color: #E1E1E1;")
        
        slider.valueChanged.connect(update_preview)
        update_preview(self._value)
        
        layout.addWidget(preview_label)
        
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
        size = int(value)
        self._value = size
        if self._button:
            self._update_button_text(self._button.size_button)
        self.value_changed.emit(size)
