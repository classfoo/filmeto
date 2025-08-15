"""
ColorSetting - Color picker setting for drawing tools
"""
from typing import Optional
from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel, QColorDialog, QGridLayout, QWidget, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from app.ui.drawing_tools.drawing_setting import DrawingSetting


class ColorSetting(DrawingSetting):
    """
    Color picker setting with visual preview.
    Button shows current color as background.
    """
    
    def __init__(self, name: str = "color", default_color: Optional[QColor] = None):
        super().__init__(name, icon="\uE6CF")  # Palette icon
        self._value = default_color if default_color else QColor(Qt.GlobalColor.black)
    
    def create_button(self) -> QWidget:
        """Create color preview button with text label"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Create the color button
        btn = QPushButton("color")
        btn.setFixedHeight(28)
        btn.setToolTip(self.name)
        btn.setObjectName("setting_color_btn")
        
        # Add widgets to layout (text on the left, button on the right)
        layout.addWidget(btn)
        layout.addStretch()
        
        # Apply initial color
        self._apply_color_to_button(btn, self._value)
        
        # Store references for later use
        container.color_button = btn
        return container
    
    def _apply_color_to_button(self, btn: QPushButton, color: QColor):
        """Apply color as button background with adaptive text color"""
        # Calculate luminance for text color
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255.0
        text_color = "#000000" if luminance > 0.5 else "#FFFFFF"
        
        btn.setStyleSheet(f"""
            QPushButton#setting_color_btn {{
                background-color: {color.name()};
                color: {text_color};
                border: 2px solid #4080ff;  /* 始终显示高亮边框 */
                border-radius: 4px;
                font-size: 10px;
            }}
            QPushButton#setting_color_btn:hover {{
                border: 2px solid #4080ff;
                background-color: {color.lighter(120).name()};  /* 悬停时稍微亮一点 */
            }}
        """)
    
    def create_panel(self) -> QFrame:
        """Create color picker panel"""
        panel = QFrame()
        panel.setObjectName("setting_panel")
        panel.setFixedWidth(220)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel(self.name)
        title.setStyleSheet("font-weight: bold; color: #E1E1E1; font-size: 12px;")
        layout.addWidget(title)
        
        # Quick color palette (2 rows x 8 cols)
        palette_grid = QGridLayout()
        palette_grid.setSpacing(4)
        
        quick_colors = [
            # Row 1
            QColor(Qt.GlobalColor.black), QColor(Qt.GlobalColor.darkGray),
            QColor(Qt.GlobalColor.red), QColor(Qt.GlobalColor.darkRed),
            QColor(Qt.GlobalColor.green), QColor(Qt.GlobalColor.darkGreen),
            QColor(Qt.GlobalColor.blue), QColor(Qt.GlobalColor.darkBlue),
            # Row 2
            QColor(Qt.GlobalColor.white), QColor(Qt.GlobalColor.lightGray),
            QColor(Qt.GlobalColor.yellow), QColor(Qt.GlobalColor.darkYellow),
            QColor(Qt.GlobalColor.cyan), QColor(Qt.GlobalColor.darkCyan),
            QColor(Qt.GlobalColor.magenta), QColor(Qt.GlobalColor.darkMagenta)
        ]
        
        for idx, color in enumerate(quick_colors):
            row = idx // 8
            col = idx % 8
            color_btn = QPushButton()
            color_btn.setFixedSize(22, 22)
            color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    border: 1px solid #555555;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    border: 2px solid #4080ff;
                }}
            """)
            color_btn.clicked.connect(lambda checked=False, c=color: self.set_value(c))
            palette_grid.addWidget(color_btn, row, col)
        
        layout.addLayout(palette_grid)
        
        # Custom color button
        custom_btn = QPushButton("Custom Color...")
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 1px solid #505254;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4a4c5e;
            }
        """)
        custom_btn.clicked.connect(self._show_color_dialog)
        layout.addWidget(custom_btn)
        
        panel.setStyleSheet("""
            QFrame#setting_panel {
                background-color: #2b2d30;
                border: 1px solid #505254;
                border-radius: 6px;
            }
        """)
        
        return panel
    
    def _show_color_dialog(self):
        """Show full color picker dialog"""
        color = QColorDialog.getColor(self._value, None, self.name)
        if color.isValid():
            self.set_value(color)
    
    def get_value(self) -> str:
        return self._value.name()
    
    def set_value(self, value: str):
        color = QColor(value)
        self._value = color
        if self._button:
            self._apply_color_to_button(self._button.color_button, color)
        self.value_changed.emit(value)
