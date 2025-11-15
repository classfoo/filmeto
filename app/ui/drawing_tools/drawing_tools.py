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
from .settings import DrawingSetting
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
        
        # Get the tool instance
        tool = self.tools.get(tool_id)
        if not tool:
            return
            
        # Get settings for this tool from the tool itself
        settings = tool.get_settings()
        
        # Create setting buttons
        for setting in settings:
            btn_container = setting.get_button()
            # 使用partial函数修复闭包问题
            # 对于新的容器组件，我们需要连接到正确的按钮
            if hasattr(btn_container, 'color_button'):
                btn_to_connect = btn_container.color_button
            elif hasattr(btn_container, 'size_button'):
                btn_to_connect = btn_container.size_button
            elif hasattr(btn_container, 'opacity_button'):
                btn_to_connect = btn_container.opacity_button
            elif hasattr(btn_container, 'brush_type_button'):
                btn_to_connect = btn_container.brush_type_button
            elif hasattr(btn_container, 'shape_type_button'):
                btn_to_connect = btn_container.shape_type_button
            else:
                # Default to the container itself if no specific button found
                btn_to_connect = btn_container
                
            btn_to_connect.clicked.connect(partial(self._on_setting_clicked, setting, btn_to_connect))
            self.settings_layout.addWidget(btn_container)
        
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
        tool = self.tools.get(tool_id)
        if not tool:
            return None
            
        settings = tool.get_settings()
        for setting in settings:
            if setting.name == setting_name:
                return setting.get_value()
        return None
    
    def set_setting_value(self, tool_id: str, setting_name: str, value):
        """Set value of a specific setting for a tool."""
        tool = self.tools.get(tool_id)
        if not tool:
            return
            
        settings = tool.get_settings()
        for setting in settings:
            if setting.name == setting_name:
                setting.set_value(value)
                break