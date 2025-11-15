"""
DrawingToolsWidget - A component for drawing tools with selection and configuration panels
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QFrame, QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import os
import importlib.util
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
    tool_selected = Signal(str)  # Signal emitted when a tool is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # Load tools dynamically
        self.tools = self._load_tools()
        
        # Initialize selected tool
        self.current_tool = "pen"
        
        # Create UI
        self.init_ui()
        self.setup_connections()
        
    def _load_tools(self):
        """Load all available drawing tools."""
        # In a more advanced implementation, this could dynamically discover and load tools
        # For now, we'll manually instantiate our tool classes
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
        
        # Convert to dictionary for easier access
        tools_dict = {tool.get_id(): tool for tool in tool_instances}
        return tools_dict
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Create tool buttons
        self.tool_buttons = {}
        
        # Create buttons for all loaded tools
        for tool_id, tool in self.tools.items():
            btn = QPushButton(self)
            btn.setObjectName(f"tool_{tool_id}")
            btn.setCheckable(True)
            btn.setFixedSize(32, 32)
            btn.setToolTip(tool.get_name())
            
            # Set icon using iconfont character directly
            btn.setText(tool.get_icon())
            
            # Set font for icon display
            font = QFont("iconfont", 12)
            btn.setFont(font)
            
            # If this is the current tool, check it
            if tool_id == self.current_tool:
                btn.setChecked(True)
                
            self.tool_buttons[tool_id] = btn
            layout.addWidget(btn)
        
        # Create floating panel for tool options
        self.floating_panel = QFrame(self.parent_widget)
        self.floating_panel.setFrameStyle(QFrame.StyledPanel)
        self.floating_panel.setWindowFlags(Qt.Popup)
        self.floating_panel.setVisible(False)
        
        # Apply dark theme style to the floating panel from styles module
        from ..styles import DRAWING_TOOLS_WIDGET_STYLE
        self.setStyleSheet(DRAWING_TOOLS_WIDGET_STYLE)
        self.floating_panel.setStyleSheet(DRAWING_TOOLS_WIDGET_STYLE)
        
        # Ensure tool buttons remain square
        for btn in self.tool_buttons.values():
            btn.setFixedSize(32, 32)
        
        # Create stacked widget for different tool configurations
        self.config_stack = QStackedWidget()
        
        # Create configurations for different tools
        self.create_tool_configs()
        
        # Create main layout for floating panel
        panel_layout = QVBoxLayout(self.floating_panel)
        panel_layout.addWidget(self.config_stack)
        
    def create_tool_configs(self):
        """Create configuration panels for different tools."""
        self.tool_config_widgets = {}
        
        # Create configuration panels for all tools
        for tool_id, tool in self.tools.items():
            config_widget = tool.create_config_panel()
            self.config_stack.addWidget(config_widget)
            self.tool_config_widgets[tool_id] = config_widget
        
    def setup_connections(self):
        """Setup signal connections."""
        # Connect button signals
        for btn in self.tool_buttons.values():
            btn.clicked.connect(self.on_tool_button_clicked)
            
    def on_tool_button_clicked(self):
        """Handle tool button click."""
        # Get the clicked button
        button = self.sender()
        
        # Get the tool ID from the button
        tool_id = None
        for tid, btn in self.tool_buttons.items():
            if btn == button:
                tool_id = tid
                break
        
        if tool_id:
            # Deselect all other buttons first
            for tid, btn in self.tool_buttons.items():
                if tid != tool_id:
                    btn.setChecked(False)
            
            # Select the current button
            button.setChecked(True)
            
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
    
    def load_iconfont_map(self):
        """Load iconfont mapping with direct unicode values."""
        # This method is no longer needed as we're using direct iconfont characters
        # Keeping it for backward compatibility
        return {}
        
    def get_tool_config(self, tool_id):
        """Get configuration data for a specific tool."""
        if tool_id in self.tools:
            return self.tools[tool_id].get_config()
        return None
        
    def set_tool_config(self, tool_id, config):
        """Set configuration data for a specific tool."""
        if tool_id in self.tools:
            self.tools[tool_id].set_config(config)
