"""
DrawingToolsWidget - A component for drawing tools with selection and configuration panels
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QFrame, QLabel, QSpinBox,
    QComboBox, QButtonGroup, QVBoxLayout, QGridLayout, QStackedWidget
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QPalette, QIcon, QPixmap, QPainter, QColor
import json
import os


class DrawingToolsWidget(QWidget):
    tool_selected = Signal(str)  # Signal emitted when a tool is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # Load iconfont mappings
        self.iconfont_map = self.load_iconfont_map()
        
        # Define tools with their properties
        self.tools = [
            {"id": "move", "name": "移动工具", "icon": "move"},
            {"id": "select", "name": "框选工具", "icon": "mti-quanxuan"},
            {"id": "pen", "name": "铅笔工具", "icon": "shougong"},
            {"id": "brush", "name": "画笔工具", "icon": "huabi"},
            {"id": "shape", "name": "图形工具", "icon": "shape"},
            {"id": "text", "name": "文字工具", "icon": "wenzi"},
            {"id": "zoom", "name": "缩放工具", "icon": "zoom"},
            {"id": "adjust", "name": "色彩调整工具", "icon": "diaoseban"}
        ]
        
        # Initialize selected tool
        self.current_tool = "select"
        
        # Create UI
        self.init_ui()
        self.setup_connections()
        
    def load_iconfont_map(self):
        """Load iconfont mapping from JSON file."""
        try:
            # Try to load iconfont.json from textures directory
            iconfont_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "textures", "iconfont.json")
            iconfont_path = os.path.abspath(iconfont_path)
            
            with open(iconfont_path, 'r', encoding='utf-8') as f:
                iconfont_data = json.load(f)
            
            # Map font_class to unicode
            icon_map = {}
            for glyph in iconfont_data.get("glyphs", []):
                icon_map[glyph["font_class"]] = chr(glyph["unicode_decimal"])
                
            return icon_map
        except Exception as e:
            print(f"Error loading iconfont: {e}")
            # Return basic mapping in case of error
            return {
                "move": "↖",  # Using a fallback character
                "mti-quanxuan": "□",  # Using a fallback character
                "shougong": "✏",  # Using a fallback character
                "huabi": "🖌",  # Using a fallback character
                "shape": "⋄",  # Using a fallback character
                "wenzi": "T",  # Using a fallback character
                "zoom": "+",  # Using a fallback character
                "diaoseban": "🎨"  # Using a fallback character
            }
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Create tool buttons
        self.button_group = QButtonGroup(self)
        self.tool_buttons = {}
        
        for tool in self.tools:
            btn = QToolButton(self)
            btn.setObjectName(f"tool_{tool['id']}")
            btn.setCheckable(True)
            btn.setFixedSize(32, 32)
            btn.setToolTip(tool["name"])
            
            # Set icon using iconfont character
            icon_char = self.iconfont_map.get(tool["icon"], tool["icon"][0].upper())
            btn.setText(icon_char)
            btn.setProperty("icon_class", tool["icon"])
            
            # Set font for icon display
            font = btn.font()
            font.setPointSize(12)
            btn.setFont(font)
            
            # If this is the current tool, check it
            if tool["id"] == self.current_tool:
                btn.setChecked(True)
                
            self.tool_buttons[tool["id"]] = btn
            self.button_group.addButton(btn)
            layout.addWidget(btn)
        
        # Create floating panel for tool options
        self.floating_panel = QFrame(self.parent_widget)
        self.floating_panel.setFrameStyle(QFrame.StyledPanel)
        self.floating_panel.setWindowFlags(Qt.Popup)
        self.floating_panel.setVisible(False)
        
        # Create stacked widget for different tool configurations
        self.config_stack = QStackedWidget()
        
        # Create configurations for different tools
        self.create_tool_configs()
        
        # Create main layout for floating panel
        panel_layout = QVBoxLayout(self.floating_panel)
        panel_layout.addWidget(self.config_stack)
        
    def create_tool_configs(self):
        """Create configuration panels for different tools."""
        # Select tool configuration
        select_config = self.create_select_config()
        self.config_stack.addWidget(select_config)
        self.tool_config_widgets = {"select": select_config}
        
        # Pen tool configuration
        pen_config = self.create_pen_config()
        self.config_stack.addWidget(pen_config)
        self.tool_config_widgets["pen"] = pen_config
        
        # Brush tool configuration
        brush_config = self.create_brush_config()
        self.config_stack.addWidget(brush_config)
        self.tool_config_widgets["brush"] = brush_config
        
        # Shape tool configuration
        shape_config = self.create_shape_config()
        self.config_stack.addWidget(shape_config)
        self.tool_config_widgets["shape"] = shape_config
        
        # Text tool configuration
        text_config = self.create_text_config()
        self.config_stack.addWidget(text_config)
        self.tool_config_widgets["text"] = text_config
        
        # Zoom tool configuration
        zoom_config = self.create_zoom_config()
        self.config_stack.addWidget(zoom_config)
        self.tool_config_widgets["zoom"] = zoom_config
        
        # Adjust tool configuration
        adjust_config = self.create_adjust_config()
        self.config_stack.addWidget(adjust_config)
        self.tool_config_widgets["adjust"] = adjust_config
        
        # For tools without specific config, create empty panels
        for tool_id in ["move"]:
            empty_config = QWidget()
            self.config_stack.addWidget(empty_config)
            self.tool_config_widgets[tool_id] = empty_config
        
    def create_select_config(self):
        """Create configuration for selection tool."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Selection mode label
        label = QLabel("选择模式:")
        layout.addWidget(label, 0, 0)
        
        # Selection mode combo box
        self.select_mode_combo = QComboBox()
        self.select_mode_combo.addItems(["矩形选择", "椭圆选择", "套索选择", "智能选择"])
        layout.addWidget(self.select_mode_combo, 0, 1)
        
        # Add some spacing
        layout.setRowStretch(1, 1)
        
        return widget
    
    def create_pen_config(self):
        """Create configuration for pen tool."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Brush size label and spinner
        size_label = QLabel("笔尖粗细:")
        layout.addWidget(size_label, 0, 0)
        
        self.pen_size_spin = QSpinBox()
        self.pen_size_spin.setRange(1, 50)
        self.pen_size_spin.setValue(2)
        layout.addWidget(self.pen_size_spin, 0, 1)
        
        # Color label and button
        color_label = QLabel("颜色:")
        layout.addWidget(color_label, 1, 0)
        
        self.pen_color_btn = QToolButton()
        self.pen_color_btn.setText("选择颜色")
        layout.addWidget(self.pen_color_btn, 1, 1)
        
        # Add some spacing
        layout.setRowStretch(2, 1)
        
        return widget
    
    def create_brush_config(self):
        """Create configuration for brush tool."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Brush style label and combo
        style_label = QLabel("笔刷样式:")
        layout.addWidget(style_label, 0, 0)
        
        self.brush_style_combo = QComboBox()
        self.brush_style_combo.addItems(["圆形", "方块", "纹理1", "纹理2"])
        layout.addWidget(self.brush_style_combo, 0, 1)
        
        # Brush size label and spinner
        size_label = QLabel("笔尖粗细:")
        layout.addWidget(size_label, 1, 0)
        
        self.brush_size_spin = QSpinBox()
        self.brush_size_spin.setRange(1, 50)
        self.brush_size_spin.setValue(5)
        layout.addWidget(self.brush_size_spin, 1, 1)
        
        # Opacity label and spinner
        opacity_label = QLabel("不透明度:")
        layout.addWidget(opacity_label, 2, 0)
        
        self.brush_opacity_spin = QSpinBox()
        self.brush_opacity_spin.setRange(1, 100)
        self.brush_opacity_spin.setValue(100)
        self.brush_opacity_spin.setSuffix("%")
        layout.addWidget(self.brush_opacity_spin, 2, 1)
        
        # Add some spacing
        layout.setRowStretch(3, 1)
        
        return widget
    
    def create_shape_config(self):
        """Create configuration for shape tool."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Shape type label and combo
        type_label = QLabel("形状类型:")
        layout.addWidget(type_label, 0, 0)
        
        self.shape_type_combo = QComboBox()
        self.shape_type_combo.addItems(["矩形", "椭圆", "直线", "多边形"])
        layout.addWidget(self.shape_type_combo, 0, 1)
        
        # Fill style label and combo
        fill_label = QLabel("填充样式:")
        layout.addWidget(fill_label, 1, 0)
        
        self.shape_fill_combo = QComboBox()
        self.shape_fill_combo.addItems(["实心", "空心", "渐变"])
        layout.addWidget(self.shape_fill_combo, 1, 1)
        
        # Line width label and spinner
        width_label = QLabel("线条宽度:")
        layout.addWidget(width_label, 2, 0)
        
        self.shape_width_spin = QSpinBox()
        self.shape_width_spin.setRange(1, 20)
        self.shape_width_spin.setValue(2)
        layout.addWidget(self.shape_width_spin, 2, 1)
        
        # Add some spacing
        layout.setRowStretch(3, 1)
        
        return widget
    
    def create_text_config(self):
        """Create configuration for text tool."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Font size label and spinner
        size_label = QLabel("字体大小:")
        layout.addWidget(size_label, 0, 0)
        
        self.text_size_spin = QSpinBox()
        self.text_size_spin.setRange(8, 72)
        self.text_size_spin.setValue(16)
        layout.addWidget(self.text_size_spin, 0, 1)
        
        # Font family label and combo
        font_label = QLabel("字体:")
        layout.addWidget(font_label, 1, 0)
        
        self.text_font_combo = QComboBox()
        self.text_font_combo.addItems(["Arial", "Times", "Courier", "Helvetica"])
        layout.addWidget(self.text_font_combo, 1, 1)
        
        # Text alignment label and combo
        align_label = QLabel("对齐方式:")
        layout.addWidget(align_label, 2, 0)
        
        self.text_align_combo = QComboBox()
        self.text_align_combo.addItems(["左对齐", "居中", "右对齐", "两端对齐"])
        layout.addWidget(self.text_align_combo, 2, 1)
        
        # Add some spacing
        layout.setRowStretch(3, 1)
        
        return widget
    
    def create_zoom_config(self):
        """Create configuration for zoom tool."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Zoom level label and combo
        zoom_label = QLabel("缩放级别:")
        layout.addWidget(zoom_label, 0, 0)
        
        self.zoom_level_combo = QComboBox()
        self.zoom_level_combo.addItems(["25%", "50%", "75%", "100%", "150%", "200%", "400%"])
        self.zoom_level_combo.setCurrentText("100%")
        layout.addWidget(self.zoom_level_combo, 0, 1)
        
        # Fit to screen button
        self.fit_screen_btn = QToolButton()
        self.fit_screen_btn.setText("适应屏幕")
        layout.addWidget(self.fit_screen_btn, 1, 0, 1, 2)
        
        # Add some spacing
        layout.setRowStretch(2, 1)
        
        return widget
    
    def create_adjust_config(self):
        """Create configuration for color adjustment tool."""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Brightness label and spinner
        bright_label = QLabel("亮度:")
        layout.addWidget(bright_label, 0, 0)
        
        self.adjust_brightness_spin = QSpinBox()
        self.adjust_brightness_spin.setRange(-100, 100)
        self.adjust_brightness_spin.setValue(0)
        layout.addWidget(self.adjust_brightness_spin, 0, 1)
        
        # Contrast label and spinner
        contrast_label = QLabel("对比度:")
        layout.addWidget(contrast_label, 1, 0)
        
        self.adjust_contrast_spin = QSpinBox()
        self.adjust_contrast_spin.setRange(-100, 100)
        self.adjust_contrast_spin.setValue(0)
        layout.addWidget(self.adjust_contrast_spin, 1, 1)
        
        # Saturation label and spinner
        sat_label = QLabel("饱和度:")
        layout.addWidget(sat_label, 2, 0)
        
        self.adjust_saturation_spin = QSpinBox()
        self.adjust_saturation_spin.setRange(-100, 100)
        self.adjust_saturation_spin.setValue(0)
        layout.addWidget(self.adjust_saturation_spin, 2, 1)
        
        # Add some spacing
        layout.setRowStretch(3, 1)
        
        return widget
    
    def setup_connections(self):
        """Setup signal connections."""
        self.button_group.buttonClicked.connect(self.on_tool_selected)
        
    def on_tool_selected(self, button):
        """Handle tool selection."""
        # Get the tool ID from the button
        tool_id = None
        for tid, btn in self.tool_buttons.items():
            if btn == button:
                tool_id = tid
                break
        
        if tool_id:
            self.current_tool = tool_id
            self.tool_selected.emit(tool_id)
            self.show_floating_panel(button)
    
    def show_floating_panel(self, button):
        """Show the floating configuration panel below the selected tool button."""
        # Get the position of the button relative to the main window
        pos = button.mapToGlobal(button.rect().bottomLeft())
        
        # Show the floating panel at the calculated position
        self.floating_panel.move(pos)
        
        # Show the appropriate configuration based on the selected tool
        if self.current_tool in self.tool_config_widgets:
            index = self.config_stack.indexOf(self.tool_config_widgets[self.current_tool])
            self.config_stack.setCurrentIndex(index)
        
        self.floating_panel.setVisible(True)
    
    def hide_floating_panel(self):
        """Hide the floating configuration panel."""
        self.floating_panel.setVisible(False)
        
    def get_current_tool(self):
        """Get the currently selected tool."""
        return self.current_tool
        
    def set_current_tool(self, tool_id):
        """Set the current tool programmatically."""
        if tool_id in self.tool_buttons:
            self.tool_buttons[tool_id].click()
    
    def mousePressEvent(self, event):
        """Handle mouse press events to hide the floating panel when clicking outside."""
        super().mousePressEvent(event)
        # Check if the click is outside the tool buttons and floating panel
        # Hide the floating panel if needed
        self.check_and_hide_panel(event.pos())
    
    def check_and_hide_panel(self, pos):
        """Check if panel should be hidden based on click position."""
        # Get the global position
        global_pos = self.mapToGlobal(pos)
        
        # Check if click is outside the floating panel
        if self.floating_panel.isVisible():
            panel_rect = self.floating_panel.frameGeometry()
            if not panel_rect.contains(global_pos):
                # Also check if not clicking on one of the tool buttons
                widget_at_pos = self.parent_widget.childAt(self.parent_widget.mapFromGlobal(global_pos))
                if widget_at_pos not in self.tool_buttons.values():
                    self.hide_floating_panel()