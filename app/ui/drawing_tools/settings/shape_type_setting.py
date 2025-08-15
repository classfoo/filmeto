"""
ShapeTypeSetting - Shape type selection setting for drawing tools
"""
from typing import Optional
from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel, QGridLayout, QWidget, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from app.ui.drawing_tools.drawing_setting import DrawingSetting


class ShapeTypeSetting(DrawingSetting):
    """
    Shape type selection setting.
    Button shows current shape icon.
    """
    
    def __init__(self, name: str = "shape"):
        super().__init__(name, icon="\uE6BC")  # Shape icon
        self._value = "rectangle"  # rectangle, ellipse, line, arrow
        self._shape_icons = {
            "rectangle": "\u25AD",  # Rectangle
            "ellipse": "\u25EF",    # Ellipse
            "line": "\u2500",       # Line
            "arrow": "\u2192"       # Arrow
        }
        self._shape_names = {
            "rectangle": "Rectangle",
            "ellipse": "Ellipse",
            "line": "Line",
            "arrow": "Arrow"
        }
    
    def create_button(self) -> QWidget:
        """Create shape type indicator button with text label"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        # Create the shape type button
        btn = QPushButton()
        btn.setFixedHeight(28)
        btn.setObjectName("setting_shape_type_btn")
        
        # Add widgets to layout (text on the left, button on the right)
        layout.addWidget(btn)
        layout.addStretch()
        
        # Update button display
        self._update_button_display_internal(btn)
        
        btn.setStyleSheet("""
            QPushButton#setting_shape_type_btn {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 2px solid #4080ff;  /* 始终显示高亮边框 */
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton#setting_shape_type_btn:hover {
                background-color: #4a4c5e;
                border: 2px solid #4080ff;
            }
        """)
        
        # Store references for later use
        container.shape_type_button = btn

        return container
    
    def _update_button_display_internal(self, btn: QPushButton):
        """Update button visual"""
        btn.setText(f"{self.name}: {self._shape_icons[self._value]}")
        btn.setToolTip(f"{self.name}: {self._shape_names[self._value]}")
    
    def create_panel(self) -> QFrame:
        """Create shape selection panel"""
        panel = QFrame()
        panel.setObjectName("setting_panel")
        panel.setFixedWidth(180)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Select Shape")
        title.setStyleSheet("font-weight: bold; color: #E1E1E1; font-size: 12px;")
        layout.addWidget(title)
        
        # Shape selection buttons (2x2 grid)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)
        
        shapes = ["rectangle", "ellipse", "line", "arrow"]
        for idx, shape in enumerate(shapes):
            row = idx // 2
            col = idx % 2
            shape_btn = self._create_shape_button(shape)
            grid_layout.addWidget(shape_btn, row, col)
        
        layout.addLayout(grid_layout)
        
        panel.setStyleSheet("""
            QFrame#setting_panel {
                background-color: #2b2d30;
                border: 1px solid #505254;
                border-radius: 6px;
            }
        """)
        
        return panel
    
    def _create_shape_button(self, shape: str) -> QPushButton:
        """Create a shape selection button"""
        btn = QPushButton(f"{self._shape_icons[shape]}\n{self._shape_names[shape]}")
        btn.setFixedSize(80, 40)
        
        is_selected = shape == self._value
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#4080ff' if is_selected else '#3d3f4e'};
                color: #E1E1E1;
                border: 1px solid {'#4080ff' if is_selected else '#505254'};
                border-radius: 4px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {'#5090ff' if is_selected else '#4a4c5e'};
                border: 1px solid #5a5c6e;
            }}
        """)
        
        btn.clicked.connect(lambda: self.set_value(shape))
        return btn
    
    def get_value(self) -> str:
        return self._value
    
    def set_value(self, value: str):
        self._value = value
        if self._button:
            self._update_button_display_internal(self._button.shape_type_button)
        # Recreate panel to update selected state
        if self._panel:
            self._panel.deleteLater()
            self._panel = None
        self.value_changed.emit(value)
