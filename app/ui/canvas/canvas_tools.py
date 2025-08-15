"""
Canvas Tools Widget Component
This module implements a canvas tools widget with drawing tools, brush properties, and canvas operations.
"""
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
                               QGroupBox, QComboBox, QFrame, QSizePolicy)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Signal

from app.ui.canvas import BrushType
from app.ui.canvas.canvas import DrawingMode


class CanvasToolsWidget(QFrame):
    """
    Tools and properties panel for canvas editing.
    Contains drawing tools, brush properties, and canvas operations.
    """
    
    # Signals
    brush_size_changed = Signal(int)
    brush_color_changed = Signal(QColor)
    brush_type_changed = Signal(BrushType)
    mode_changed = Signal(object)
    
    def __init__(self, canvas_widget):
        super().__init__()
        self.canvas_widget = canvas_widget
        
        # Set fixed width to match LayersWidget
        self.setFixedWidth(160)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # Set up UI
        self.setFrameStyle(QFrame.StyledPanel)
        # 使用暗色主题样式
        self._apply_style()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tools section
        tools_group = self._create_tools_section()
        main_layout.addWidget(tools_group)
        
        # Create properties section
        properties_group = self._create_properties_section()
        main_layout.addWidget(properties_group)
        
        # Create canvas operations section
        operations_group = self._create_operations_section()
        main_layout.addWidget(operations_group)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        # Connect canvas widget signals to update UI
        self._connect_canvas_signals()
    
    def _apply_style(self):
        """Apply widget style from styles library"""
        from app.ui.styles import CANVAS_TOOLS_WIDGET_STYLE
        self.setStyleSheet(CANVAS_TOOLS_WIDGET_STYLE)
    
    def _create_tools_section(self):
        """Create the tools section with drawing mode buttons"""
        tools_group = QGroupBox("Drawing Tools")
        tools_layout = QVBoxLayout(tools_group)
        tools_layout.setSpacing(5)
        
        # Set up icon font
        icon_font = QFont("iconfont", 16)
        # Fallback to a standard font if iconfont is not available
        icon_font.setPointSize(16)
        
        # Mode buttons with icons - made square with fixed size
        button_size = 30
        
        # Create a flow layout for the buttons
        from app.ui.layout.flow_layout import FlowLayout
        buttons_layout = FlowLayout()
        buttons_layout.setSpacing(5)
        
        self.brush_btn = QPushButton("\uE648")  # 画笔图标 (37画笔)
        self.brush_btn.setFont(icon_font)
        self.brush_btn.setCheckable(True)
        self.brush_btn.setChecked(True)
        self.brush_btn.setFixedSize(button_size, button_size)
        self.brush_btn.setToolTip("Brush")
        self.brush_btn.clicked.connect(lambda: self._set_mode(DrawingMode.BRUSH))
        buttons_layout.addWidget(self.brush_btn)
        
        self.eraser_btn = QPushButton("\uE7F1")  # 橡皮擦图标 (橡皮擦)
        self.eraser_btn.setFont(icon_font)
        self.eraser_btn.setCheckable(True)
        self.eraser_btn.setFixedSize(button_size, button_size)
        self.eraser_btn.setToolTip("Eraser")
        self.eraser_btn.clicked.connect(lambda: self._set_mode(DrawingMode.ERASER))
        buttons_layout.addWidget(self.eraser_btn)
        
        self.select_btn = QPushButton("\uE61B")  # 平移图标 (平移)
        self.select_btn.setFont(icon_font)
        self.select_btn.setCheckable(True)
        self.select_btn.setFixedSize(button_size, button_size)
        self.select_btn.setToolTip("Select")
        self.select_btn.clicked.connect(lambda: self._set_mode(DrawingMode.SELECT))
        buttons_layout.addWidget(self.select_btn)
        
        self.shape_btn = QPushButton("\uE6BC")  # 图片生成图标 (图片生成)
        self.shape_btn.setFont(icon_font)
        self.shape_btn.setCheckable(True)
        self.shape_btn.setFixedSize(button_size, button_size)
        self.shape_btn.setToolTip("Shape Draw")
        self.shape_btn.clicked.connect(lambda: self._set_mode(DrawingMode.SHAPE))
        buttons_layout.addWidget(self.shape_btn)

        
        # Add the flow layout to the main layout
        tools_layout.addLayout(buttons_layout)
        
        return tools_group
    
    def _create_properties_section(self):
        """Create the properties section with brush settings"""
        properties_group = QGroupBox("Brush Properties")
        properties_layout = QVBoxLayout(properties_group)

        # Brush size control
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 50)
        self.size_slider.setValue(5)
        self.size_slider.valueChanged.connect(self._set_brush_size)
        size_layout.addWidget(self.size_slider)
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(1, 50)
        self.size_spinbox.setValue(5)
        self.size_spinbox.valueChanged.connect(self._set_brush_size)
        size_layout.addWidget(self.size_spinbox)
        
        # Connect slider and spinbox
        self.size_slider.valueChanged.connect(self.size_spinbox.setValue)
        self.size_spinbox.valueChanged.connect(self.size_slider.setValue)
        properties_layout.addLayout(size_layout)
        
        # Brush type control
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.brush_type_combo = QComboBox()
        self.brush_type_combo.addItems(["Solid", "Dash", "Dotted", "Dash Dot", "Dash Dot Dot"])
        self.brush_type_combo.currentIndexChanged.connect(self._set_brush_type)
        type_layout.addWidget(self.brush_type_combo)
        properties_layout.addLayout(type_layout)
        
        # Brush color control
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self._choose_brush_color)
        color_layout.addWidget(self.color_btn)
        properties_layout.addLayout(color_layout)
        
        # Color preview
        # self.color_preview = QLabel()
        # self.color_preview.setFixedSize(30, 30)
        # self.color_preview.setStyleSheet(f"background-color: {self.canvas_widget.brush_color.name()}; border: 1px solid #555555;")
        # color_layout.addWidget(self.color_preview)
        
        return properties_group
    
    def _create_operations_section(self):
        """Create the canvas operations section"""
        operations_group = QGroupBox("Canvas Operations")
        operations_layout = QVBoxLayout(operations_group)
        
        self.clear_btn = QPushButton("Clear Canvas")
        self.clear_btn.clicked.connect(self.canvas_widget.clear_canvas)
        operations_layout.addWidget(self.clear_btn)
        
        return operations_group
    
    def _connect_canvas_signals(self):
        """Connect canvas widget signals to update UI controls"""
        # Update UI when canvas properties change
        # For now, we'll update on mode change
        pass
    
    def _set_mode(self, mode: DrawingMode):
        """Set the drawing mode in the canvas widget"""
        self.canvas_widget.set_mode(mode)
        
        # Update button states with visual highlighting
        self._update_button_states(mode)
        
        # Emit signal
        self.mode_changed.emit(mode)
    
    def _update_button_states(self, mode: DrawingMode):
        """Update the visual state of tool buttons"""
        # Reset all buttons to default style
        buttons = [self.brush_btn, self.eraser_btn, self.select_btn, self.shape_btn]
        for btn in buttons:
            btn.setChecked(False)
            btn.setProperty("selected", False)
        
        # Highlight the selected button
        if mode == DrawingMode.BRUSH:
            self.brush_btn.setChecked(True)
            self.brush_btn.setProperty("selected", True)
        elif mode == DrawingMode.ERASER:
            self.eraser_btn.setChecked(True)
            self.eraser_btn.setProperty("selected", True)
        elif mode == DrawingMode.SELECT:
            self.select_btn.setChecked(True)
            self.select_btn.setProperty("selected", True)
        elif mode == DrawingMode.SHAPE:
            self.shape_btn.setChecked(True)
            self.shape_btn.setProperty("selected", True)
        
        # Force style update for all buttons
        for btn in buttons:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()
    
    def _set_brush_size(self, size: int):
        """Set the brush size in the canvas widget"""
        self.canvas_widget.set_brush_size(size)
        self.brush_size_changed.emit(size)
    
    def _set_brush_type(self, index: int):
        """Set the brush type in the canvas widget"""
        brush_types = [
            BrushType.SOLID,
            BrushType.DASH,
            BrushType.DOTTED,
            BrushType.DASHDOT,
            BrushType.DASHDOTDOT
        ]
        if 0 <= index < len(brush_types):
            brush_type = brush_types[index]
            self.canvas_widget.set_brush_type(brush_type)
            self.brush_type_changed.emit(brush_type)
    
    def _choose_brush_color(self):
        """Open a color dialog to choose brush color"""
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(self.canvas_widget.brush_color, self, "Choose Brush Color")
        if color.isValid():
            self.canvas_widget.set_brush_color(color)
            self.brush_color_changed.emit(color)
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #555555;")