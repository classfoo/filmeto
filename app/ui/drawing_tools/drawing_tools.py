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
from ..base_widget import BaseWidget
from ...data.workspace import Workspace
from ...data.drawing import Drawing


class DrawingToolsWidget(BaseWidget):
    """
    Refactored drawing tools widget.
    
    Layout: [Tool Buttons] | [Setting Buttons]
    - Left: Tool selection buttons (28x28px)
    - Separator: Vertical divider line
    - Right: Setting buttons that update based on selected tool
    
    Height: 30px (fixed)
    """
    tool_selected = Signal(str)  # Signal emitted when a tool is selected
    
    # Class variable to hold the instance
    _instance = None
    
    def __init__(self, parent, workspace: Workspace):
        super(DrawingToolsWidget, self).__init__(workspace)
        self.parent_widget = parent
        self.workspace = workspace
        # Fixed height for toolbar
        self.setFixedHeight(30)
        
        # Store the instance
        DrawingToolsWidget._instance = self
        
        # Load tools
        self.tools = self._load_tools()
        # Initialize current tool to default value first
        self.current_tool = "pen"
        
        # Active setting panel reference
        self._active_panel: Optional[QFrame] = None
        self._active_panel_button: Optional[QPushButton] = None
        
        # Create UI - this will use the default current_tool value
        self.init_ui()
        
        # Connect to workspace project switching to load drawing config
        self.workspace.project_manager.project_switched.connect(self._on_project_switched)
        
        # Load initial tool settings from project's drawing config or default
        self._load_initial_drawing_config()
    
    @staticmethod
    def get_instance() -> 'DrawingToolsWidget':
        """
        Get the singleton instance of DrawingToolsWidget.
        
        Returns:
            DrawingToolsWidget: The instance of DrawingToolsWidget, or None if not initialized
        """
        return DrawingToolsWidget._instance
    
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
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)
        
        # Tool buttons section
        self.tool_buttons = {}
        font = QFont("iconfont", 12)
        
        for tool_id, tool in self.tools.items():
            btn = QPushButton(tool.get_icon())
            btn.setObjectName(f"tool_{tool_id}")
            btn.setFont(font)
            btn.setCheckable(True)
            btn.setFixedSize(32, 32)
            btn.setToolTip(tool.get_name())
            btn.setChecked(tool_id == self.current_tool)
            btn.clicked.connect(lambda checked=False, tid=tool_id: self._on_tool_clicked(tid))
            
            self.tool_buttons[tool_id] = btn
            layout.addWidget(btn)
        
        # Vertical separator
        # Add padding widgets before and after separator
        left_padding = QWidget()
        left_padding.setFixedWidth(15)
        layout.addWidget(left_padding)
        
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setFixedHeight(24)
        separator.setStyleSheet("background-color: #FFFFFF;")
        layout.addWidget(separator)
        
        right_padding = QWidget()
        right_padding.setFixedWidth(15)
        layout.addWidget(right_padding)
        
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
        
        # Save the new drawing configuration to the project
        self._save_drawing_config_to_project()
    
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
        if self._active_panel and self._active_panel_button != button:
            self._hide_active_panel()
            return

        # Hide previous panel
        self._hide_active_panel()

        # Show new panel
        panel = setting.get_panel()
        panel.setParent(self.parent_widget if self.parent_widget else self)
        panel.setWindowFlags(Qt.WindowType.Popup)

        # Make sure the panel is valid before showing
        if panel is None or not panel.isVisible():
            # Position panel below button
            global_pos = button.mapToGlobal(button.rect().bottomLeft())
            panel.move(global_pos.x(), global_pos.y() + 4)
            panel.show()

            # Track active panel
            self._active_panel = panel
            self._active_panel_button = button

            # Install event filter to detect clicks outside
            panel.installEventFilter(self)
        
        # Connect the setting's value change signal to save the configuration
        setting.value_changed.connect(self._on_setting_value_changed)
    
    def _on_setting_value_changed(self):
        """Handle setting value changes by saving to project."""
        # Small delay to ensure the UI components have updated their values
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, self._save_drawing_config_to_project)
    
    def _hide_active_panel(self):
        """Hide the currently active setting panel."""
        if self._active_panel:
            # Check if panel still exists and is visible before trying to hide it
            try:
                if self._active_panel.isVisible():
                    self._active_panel.hide()
            except RuntimeError:
                # Handle case where panel has been deleted
                pass
            finally:
                self._active_panel = None
                self._active_panel_button = None
    
    def eventFilter(self, watched, event):
        """Event filter to close panel when clicking outside."""
        if event.type() == QEvent.Type.FocusOut:
            # Add additional check to ensure we're dealing with the active panel
            if watched == self._active_panel and self._active_panel is not None:
                # Use a single shot timer to avoid immediate closing issues
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self._hide_active_panel)
                return True
        return super().eventFilter(watched, event)
    
    def get_current_tool(self):
        """Get the currently selected tool."""
        return self.current_tool
    
    def set_current_tool(self, tool_id):
        """Set the current tool programmatically."""
        if tool_id in self.tool_buttons:
            self._on_tool_clicked(tool_id)
    
    def get_tool(self, tool_id: str) -> Optional[DrawingTool]:
        """
        Get a tool instance by its ID.
        
        Args:
            tool_id (str): The ID of the tool to retrieve
            
        Returns:
            Optional[DrawingTool]: The tool instance if found, None otherwise
        """
        return self.tools.get(tool_id)
    
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
    
    def _apply_drawing_config_to_ui(self, drawing_config: Drawing):
        """Apply drawing configuration settings to the UI."""
        # Apply settings for each tool without triggering save to project
        for tool_id, settings in drawing_config.tool_settings.items():
            for setting_name, value in settings.items():
                self.set_setting_value(tool_id, setting_name, value)
    
    def _load_initial_drawing_config(self):
        """Load the initial drawing configuration from the current project."""
        if self.workspace.get_project():
            drawing_config = self.workspace.get_project().get_drawing()
            self.current_tool = drawing_config.current_tool
            
            # Update tool buttons to reflect the current tool
            for tool_id, btn in self.tool_buttons.items():
                btn.setChecked(tool_id == self.current_tool)
            
            # Load settings for the current tool from the drawing config
            self._load_settings_for_tool(self.current_tool)
            
            # Apply stored settings from the drawing config to the UI components
            self._apply_drawing_config_to_ui(drawing_config)
        else:
            # Set default tool if no project is loaded
            self.current_tool = "pen"
            self._load_settings_for_tool(self.current_tool)
    
    def _on_project_switched(self, project_name):
        """Handle project switching by loading the drawing config for the new project."""
        # Get the new project
        project = self.workspace.get_project(project_name)
        if project:
            drawing_config = project.get_drawing()
            self.current_tool = drawing_config.current_tool
            
            # Update tool buttons to reflect the current tool
            for tool_id, btn in self.tool_buttons.items():
                btn.setChecked(tool_id == self.current_tool)
            
            # Load settings for the current tool
            self._load_settings_for_tool(self.current_tool)
            
            # Apply stored settings from the drawing config to the UI components
            self._apply_drawing_config_to_ui(drawing_config)
    
    def _save_drawing_config_to_project(self):
        """Save the current drawing configuration to the project."""
        if not self.workspace.get_project():
            return
            
        # Create a new drawing config with current state
        drawing_config = self.workspace.get_project().get_drawing()
        
        # Update current tool
        drawing_config.current_tool = self.current_tool
        
        # Update settings for each tool by querying the UI components
        for tool_id, tool in self.tools.items():
            settings = tool.get_settings()
            if tool_id not in drawing_config.tool_settings:
                drawing_config.tool_settings[tool_id] = {}
            
            for setting in settings:
                current_value = self.get_setting_value(tool_id, setting.name)
                if current_value is not None:
                    drawing_config.tool_settings[tool_id][setting.name] = current_value
        
        # Save to project
        self.workspace.get_project().get_drawing().update(drawing_config)