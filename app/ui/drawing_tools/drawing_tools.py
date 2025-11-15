"""
DrawingToolsWidget - Refactored component with tool buttons and setting buttons

Layout: [Tool Buttons] | [Setting Buttons]
- Left: Tool mode buttons  
- Separator: Vertical divider
- Right: Setting buttons that change based on selected tool
"""
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QFrame, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont
from functools import partial
from .drawing_tool import DrawingTool
from .settings import DrawingSetting, ColorSetting, SizeSetting, OpacitySetting, BrushTypeSetting, ShapeTypeSetting
from .tools.move_tool import MoveTool
from .tools.select_tool import SelectTool
from .tools.pen_tool import PenTool
from .tools.brush_tool import BrushTool
from .tools.eraser_tool import EraserTool
from .tools.shape_tool import ShapeTool
from .tools.text_tool import TextTool
from .tools.zoom_tool import ZoomTool
from .tools.adjust_tool import AdjustTool


class DrawingToolsWidget(QWidget):
    """
    Refactored drawing tools widget.
    
    Layout: [Tool Buttons] | [Setting Buttons]
    - Left: Tool selection buttons (28x28px)
    - Separator: Vertical divider line
    - Right: Setting buttons that update based on selected tool
    
    Height: 30px (fixed)
    """
    tool_selected = Signal(str)  # Signal emitted when a tool is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # Fixed height for toolbar
        self.setFixedHeight(30)
        
        # Load tools
        self.tools = self._load_tools()
        self.current_tool = "pen"
        
        # Tool-specific settings configuration
        self.tool_settings_map: Dict[str, List[DrawingSetting]] = {}
        self._init_tool_settings()
        
        # Active setting panel reference
        self._active_panel: Optional[QFrame] = None
        self._active_panel_button: Optional[QPushButton] = None
        
        # Create UI
        self.init_ui()
        
        # Load initial tool settings
        self._load_settings_for_tool(self.current_tool)
        
    def _load_tools(self):
        """Load all available drawing tools."""
        tool_instances = [
            MoveTool(),
            SelectTool(),
            PenTool(),
            BrushTool(),
            EraserTool(),
            ShapeTool(),
            TextTool(),
            ZoomTool(),
            AdjustTool()
        ]
        
        tools_dict = {tool.get_id(): tool for tool in tool_instances}
        return tools_dict
    
    def _init_tool_settings(self):
        """Initialize settings for each tool."""
        # Brush tool: color, size, opacity, line type
        self.tool_settings_map["brush"] = [
            ColorSetting("Color"),
            SizeSetting("Size", min_size=1, max_size=50, default_size=5),
            OpacitySetting("Opacity", default_opacity=100),
            BrushTypeSetting("Line Style")
        ]
        
        # Pen tool: color, size (shared settings with brush)
        self.tool_settings_map["pen"] = [
            ColorSetting("Color"),
            SizeSetting("Size", min_size=1, max_size=20, default_size=2)
        ]
        
        # Eraser tool: size only (larger range)
        self.tool_settings_map["eraser"] = [
            SizeSetting("Size", min_size=5, max_size=100, default_size=20)
        ]
        
        # Shape tool: shape type, color, size, line type
        self.tool_settings_map["shape"] = [
            ShapeTypeSetting("Shape"),
            ColorSetting("Stroke Color"),
            SizeSetting("Stroke Size", min_size=1, max_size=20, default_size=2),
            BrushTypeSetting("Line Style")
        ]
        
        # Text tool: color, size
        self.tool_settings_map["text"] = [
            ColorSetting("Text Color"),
            SizeSetting("Font Size", min_size=8, max_size=72, default_size=14)
        ]
        
        # Move, Select, Zoom, Adjust tools: no settings
        for tool_id in ["move", "select", "zoom", "adjust"]:
            self.tool_settings_map[tool_id] = []
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(4)
        
        # Tool buttons section
        self.tool_buttons = {}
        font = QFont("iconfont", 12)
        
        for tool_id, tool in self.tools.items():
            btn = QPushButton(tool.get_icon())
            btn.setObjectName(f"tool_{tool_id}")
            btn.setFont(font)
            btn.setCheckable(True)
            btn.setFixedSize(28, 28)
            btn.setToolTip(tool.get_name())
            btn.setChecked(tool_id == self.current_tool)
            btn.clicked.connect(lambda checked=False, tid=tool_id: self._on_tool_clicked(tid))
            
            self.tool_buttons[tool_id] = btn
            layout.addWidget(btn)
        
        # Vertical separator
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setFixedHeight(24)
        separator.setStyleSheet("background-color: #505254;")
        layout.addWidget(separator)
        
        # Settings buttons container (dynamic)
        self.settings_container = QWidget()
        self.settings_layout = QHBoxLayout(self.settings_container)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(4)
        layout.addWidget(self.settings_container, 1)
        
        # Apply dark theme style
        self._apply_styles()
    
    def _apply_styles(self):
        """Apply widget styling."""
        from ..styles import DRAWING_TOOLS_WIDGET_STYLE
        self.setStyleSheet(DRAWING_TOOLS_WIDGET_STYLE)
        
        # Additional button styles
        tool_button_style = """
            QPushButton {
                background-color: #3d3f4e;
                color: #888888;
                border: 1px solid #505254;
                border-radius: 4px;
                font-family: iconfont;
            }
            QPushButton:hover {
                background-color: #4a4c5e;
                color: #E1E1E1;
            }
            QPushButton:checked {
                background-color: #4080ff;
                color: #ffffff;
                border: 1px solid #4080ff;
            }
        """
        
        for btn in self.tool_buttons.values():
            btn.setStyleSheet(tool_button_style)
    
    def _on_tool_clicked(self, tool_id: str):
        """Handle tool button click - focus on tool switching only."""
        # Update button states
        for tid, btn in self.tool_buttons.items():
            btn.setChecked(tid == tool_id)
        
        # Update current tool
        self.current_tool = tool_id
        
        # Hide any active panel
        self._hide_active_panel()
        
        # Load settings for the new tool
        self._load_settings_for_tool(tool_id)
        
        # Emit signal
        self.tool_selected.emit(tool_id)
    
    def _load_settings_for_tool(self, tool_id: str):
        """Load and display settings buttons for the selected tool."""
        # Clear existing settings
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)  # 立即移除父级关系，避免信号连接时对象已删除的问题
        
        # Get settings for this tool
        settings = self.tool_settings_map.get(tool_id, [])
        
        # Create setting buttons
        for setting in settings:
            btn = setting.get_button()
            # 使用partial函数修复闭包问题
            btn.clicked.connect(partial(self._on_setting_clicked, setting, btn))
            self.settings_layout.addWidget(btn)
        
        # Add stretch to push settings to the left
        self.settings_layout.addStretch()
    
    def _on_setting_clicked(self, setting: DrawingSetting, button: QPushButton):
        """Handle setting button click - show configuration panel."""
        # If clicking the same button, toggle panel
        if self._active_panel and self._active_panel_button == button:
            self._hide_active_panel()
            return
        
        # Hide previous panel
        self._hide_active_panel()
        
        # Show new panel
        panel = setting.get_panel()
        panel.setParent(self.parent_widget if self.parent_widget else self)
        panel.setWindowFlags(Qt.WindowType.Popup)
        
        # Position panel below button
        global_pos = button.mapToGlobal(button.rect().bottomLeft())
        panel.move(global_pos.x(), global_pos.y() + 4)
        panel.show()
        
        # Track active panel
        self._active_panel = panel
        self._active_panel_button = button
        
        # Install event filter to detect clicks outside
        panel.installEventFilter(self)
    
    def _hide_active_panel(self):
        """Hide the currently active setting panel."""
        if self._active_panel:
            self._active_panel.hide()
            self._active_panel = None
            self._active_panel_button = None
    
    def eventFilter(self, watched, event):
        """Event filter to close panel when clicking outside."""
        if event.type() == QEvent.Type.FocusOut:
            if watched == self._active_panel:
                self._hide_active_panel()
        return super().eventFilter(watched, event)
    
    def get_current_tool(self):
        """Get the currently selected tool."""
        return self.current_tool
    
    def set_current_tool(self, tool_id):
        """Set the current tool programmatically."""
        if tool_id in self.tool_buttons:
            self._on_tool_clicked(tool_id)
    
    def get_setting_value(self, tool_id: str, setting_name: str):
        """Get value of a specific setting for a tool."""
        settings = self.tool_settings_map.get(tool_id, [])
        for setting in settings:
            if setting.name == setting_name:
                return setting.get_value()
        return None
    
    def set_setting_value(self, tool_id: str, setting_name: str, value):
        """Set value of a specific setting for a tool."""
        settings = self.tool_settings_map.get(tool_id, [])
        for setting in settings:
            if setting.name == setting_name:
                setting.set_value(value)
                break