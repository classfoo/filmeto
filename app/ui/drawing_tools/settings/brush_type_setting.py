"""
BrushTypeSetting - Brush line style setting for drawing tools
"""
from typing import Optional
from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel, QButtonGroup, QRadioButton, QWidget, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from app.ui.drawing_tools.drawing_setting import DrawingSetting


class BrushTypeSetting(DrawingSetting):
    """
    Brush line style setting.
    Button shows current line pattern icon.
    """
    
    def __init__(self, name: str = "line_style"):
        super().__init__(name, icon="\uE6E5")  # Line icon
        self._value = "solid"  # solid, dash, dot, dash-dot
        self._type_names = {
            "solid": "Solid",
            "dash": "Dash",
            "dot": "Dot",
            "dash-dot": "Dash-Dot"
        }
        self._type_icons = {
            "solid": "━",
            "dash": "╌",
            "dot": "┄",
            "dash-dot": "╍"
        }
    
    def create_button(self) -> QWidget:
        """Create line type indicator button with text label"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Create the brush type button
        btn = QPushButton()
        btn.setFixedHeight(28)
        btn.setObjectName("setting_brush_type_btn")
        
        # Add widgets to layout (text on the left, button on the right)
        layout.addWidget(btn)
        layout.addStretch()
        
        # Update button display
        self._update_button_display_internal(btn)
        
        btn.setStyleSheet("""
            QPushButton#setting_brush_type_btn {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 2px solid #4080ff;  /* 始终显示高亮边框 */
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton#setting_brush_type_btn:hover {
                background-color: #4a4c5e;
                border: 2px solid #4080ff;
            }
        """)
        
        # Store references for later use
        container.brush_type_button = btn

        return container
    
    def _update_button_display_internal(self, btn: QPushButton):
        """Update button visual"""
        btn.setText(f"{self.name}: {self._type_icons[self._value]}")
        btn.setToolTip(f"{self.name}: {self._type_names[self._value]}")
    
    def create_panel(self) -> QFrame:
        """Create line type selection panel"""
        panel = QFrame()
        panel.setObjectName("setting_panel")
        panel.setFixedWidth(180)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Title
        title = QLabel(self.name)
        title.setStyleSheet("font-weight: bold; color: #E1E1E1; font-size: 12px;")
        layout.addWidget(title)
        
        # Radio button group
        button_group = QButtonGroup(panel)
        
        for type_key, type_name in self._type_names.items():
            radio = QRadioButton(f"{self._type_icons[type_key]}  {type_name}")
            radio.setStyleSheet("""
                QRadioButton {
                    color: #E1E1E1;
                    spacing: 6px;
                    font-size: 11px;
                }
                QRadioButton::indicator {
                    width: 13px;
                    height: 13px;
                }
                QRadioButton::indicator:unchecked {
                    background-color: #1e1f22;
                    border: 1px solid #505254;
                    border-radius: 7px;
                }
                QRadioButton::indicator:checked {
                    background-color: #4080ff;
                    border: 1px solid #4080ff;
                    border-radius: 7px;
                }
            """)
            radio.setChecked(type_key == self._value)
            radio.toggled.connect(lambda checked=False, tk=type_key: self._on_type_selected(checked, tk))
            button_group.addButton(radio)
            layout.addWidget(radio)
        
        panel.setStyleSheet("""
            QFrame#setting_panel {
                background-color: #2b2d30;
                border: 1px solid #505254;
                border-radius: 6px;
            }
        """)
        
        return panel
    
    def _on_type_selected(self, checked: bool, type_key: str):
        """Handle line type selection"""
        if checked:
            self.set_value(type_key)
    
    def get_value(self) -> str:
        return self._value
    
    def set_value(self, value: str):
        self._value = value
        if self._button:
            self._update_button_display_internal(self._button.brush_type_button)
        # Recreate panel to update selected state
        if self._panel:
            self._panel.deleteLater()
            self._panel = None
        self.value_changed.emit(value)
