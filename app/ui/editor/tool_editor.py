"""
AI Image/Video Editor Component with Dynamic Tool Loading
A comprehensive editor widget that dynamically loads tools from plugins/tools directory.
"""

import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, Optional, Type
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor
from qasync import asyncSlot

from app.ui.base_widget import BaseTaskWidget
from app.ui.preview import MediaPreviewWidget
from app.ui.prompt_input.prompt_input_widget import PromptInputWidget
from app.data.workspace import Workspace
from app.data.task import TaskResult, Task
from app.data.timeline import TimelineItem
from app.spi.tool import BaseTool
from utils.i18n_utils import tr


@dataclass
class ToolInfo:
    """Information about a registered tool"""
    tool_id: str  # e.g. "text2img"
    name: str  # Display name
    icon: str  # Unicode icon character
    tool_class: Type[BaseTool]  # Tool class
    module_path: str  # Module path for lazy loading


class ToolEditorWidget(BaseTaskWidget):
    """
    AI Image/Video Editor Component with Dynamic Tool Loading
    
    Layout Structure:
    ┌─────────────────────────────────┐
    │     Preview Area (Top)          │
    │   MediaPreviewWidget            │
    │                                 │
    ├─────────────────────────────────┤
    │  Control Area (Bottom - 64px)   │
    │  ┌───────────┬─────────────┐   │
    │  │Tool Btns  │Prompt Input │   │
    │  │(40px)     │(40px)       │   │
    │  └───────────┴─────────────┘   │
    └─────────────────────────────────┘
    
    Tools are dynamically loaded from app/plugins/tools/
    """
    
    # Signals
    tool_changed = Signal(str)  # Emitted when tool changes
    task_submitted = Signal(dict)  # Emitted when task is submitted
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the editor widget"""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.workspace = workspace
        self._current_tool: Optional[str] = None
        self._is_processing = False
        self._tools: Dict[str, ToolInfo] = {}  # tool_id -> ToolInfo
        self._tool_instances: Dict[str, BaseTool] = {}  # tool_id -> tool instance
        self._tool_buttons: Dict[str, QPushButton] = {}  # tool_id -> button
        
        # Load available tools
        self._discover_tools()
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
        
        # Set initial tool if any available
        if self._tools:
            first_tool = list(self._tools.keys())[0]
            self._select_tool(first_tool)
    
    def _discover_tools(self):
        """Discover and register tools from plugins/tools directory"""
        # Get tools directory
        current_dir = Path(__file__).parent.parent.parent  # app/
        tools_dir = current_dir / "plugins" / "tools"
        
        if not tools_dir.exists():
            print(f"Tools directory not found: {tools_dir}")
            return
        
        # Scan each subdirectory in tools/
        for tool_dir in tools_dir.iterdir():
            if not tool_dir.is_dir() or tool_dir.name.startswith('_'):
                continue
            
            # Try to import the tool module
            tool_module_path = f"app.plugins.tools.{tool_dir.name}.{tool_dir.name}"
            
            try:
                module = importlib.import_module(tool_module_path)
                
                # Find BaseTool subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj != BaseTool:
                        # Register the tool
                        tool_id = tool_dir.name
                        tool_info = self._create_tool_info(tool_id, obj, tool_module_path)
                        if tool_info:
                            self._tools[tool_id] = tool_info
                            print(f"Registered tool: {tool_id} ({tool_info.name})")
                        break
            
            except Exception as e:
                print(f"Failed to load tool from {tool_module_path}: {e}")
    
    def _create_tool_info(self, tool_id: str, tool_class: Type[BaseTool], module_path: str) -> Optional[ToolInfo]:
        """Create ToolInfo from tool class"""
        # Define tool configurations (icon and display name)
        tool_configs = {
            "text2img": ("\ue82c", tr("Text to Image")),
            "img2video": ("\ue874", tr("Image to Video")),
            "text2video": ("\ue84b", tr("Text to Video")),
            "imgedit": ("\ue837", tr("Image Edit")),
            "videoedit": ("\ue834", tr("Video Edit")),
        }
        
        icon, name = tool_configs.get(tool_id, ("\ue846", tool_id.title()))
        
        return ToolInfo(
            tool_id=tool_id,
            name=name,
            icon=icon,
            tool_class=tool_class,
            module_path=module_path
        )
    
    def _get_tool_instance(self, tool_id: str) -> Optional[BaseTool]:
        """Get or create tool instance"""
        if tool_id not in self._tools:
            return None
        
        if tool_id not in self._tool_instances:
            # Create new instance
            tool_info = self._tools[tool_id]
            try:
                instance = tool_info.tool_class(self.workspace)
                self._tool_instances[tool_id] = instance
            except Exception as e:
                print(f"Failed to create tool instance for {tool_id}: {e}")
                return None
        
        return self._tool_instances.get(tool_id)
    
    def _setup_ui(self):
        """Initialize UI components"""
        # Main layout - vertical split
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable areas
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setHandleWidth(2)
        
        # ========== Top: Preview Area ==========
        self.preview_container = QFrame()
        self.preview_container.setObjectName("editor_preview_container")
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(0)
        
        # Preview widget
        self.preview_widget = MediaPreviewWidget(self.workspace)
        preview_layout.addWidget(self.preview_widget)
        
        # ========== Bottom: Control Area ==========
        self.control_container = QFrame()
        self.control_container.setObjectName("editor_control_container")
        control_main_layout = QVBoxLayout(self.control_container)
        control_main_layout.setContentsMargins(12, 12, 12, 12)
        control_main_layout.setSpacing(0)
        
        # Create horizontal layout for tool buttons and prompt input
        control_h_layout = QHBoxLayout()
        control_h_layout.setSpacing(12)
        control_h_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tool buttons section (left)
        tool_section = self._create_tool_section()
        control_h_layout.addWidget(tool_section, 0)  # Don't stretch
        
        # Prompt input section (right)
        self.prompt_input = PromptInputWidget(self.workspace)
        # Set fixed height to match tool buttons (40px)
        self.prompt_input.text_edit.setFixedHeight(40)
        self.prompt_input.text_edit.setMaximumHeight(40)
        self.prompt_input.send_button.setFixedSize(40, 40)
        self.prompt_input._is_expanded = False
        control_h_layout.addWidget(self.prompt_input, 1)  # Stretch to fill
        
        control_main_layout.addLayout(control_h_layout)
        
        # Set fixed height for control container (40px + padding)
        self.control_container.setFixedHeight(64)  # 40px content + 12px top + 12px bottom
        
        # Add containers to splitter
        self.splitter.addWidget(self.preview_container)
        self.splitter.addWidget(self.control_container)
        
        # Set initial splitter sizes (70% preview, 30% control)
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 3)
        
        # Set minimum sizes
        self.preview_container.setMinimumHeight(300)
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)
    
    def _create_tool_section(self) -> QWidget:
        """Create tool switching section with icon buttons"""
        tool_widget = QFrame()
        tool_widget.setObjectName("editor_tool_section")
        tool_layout = QHBoxLayout(tool_widget)
        tool_layout.setContentsMargins(0, 0, 0, 0)
        tool_layout.setSpacing(8)
        
        # Tool buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        
        # Create tool buttons dynamically
        for tool_id, tool_info in self._tools.items():
            btn = QPushButton(tool_info.icon)
            btn.setObjectName("editor_tool_button")
            btn.setToolTip(tool_info.name)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            btn.setProperty("tool_id", tool_id)
            btn.clicked.connect(self._handle_tool_button_click)
            self._tool_buttons[tool_id] = btn
            buttons_layout.addWidget(btn)
        
        # Status indicator
        self.status_label = QLabel(tr("Ready"))
        self.status_label.setObjectName("editor_status_label")
        
        # Layout
        tool_layout.addWidget(buttons_container)
        tool_layout.addStretch()
        tool_layout.addWidget(self.status_label)
        
        return tool_widget
    
    def _connect_signals(self):
        """Connect signals and slots"""
        # Prompt submission
        self.prompt_input.prompt_submitted.connect(self._on_prompt_submitted)
    
    def _apply_styles(self):
        """Apply component styling"""
        # Preview container
        self.preview_container.setStyleSheet("""
            QFrame#editor_preview_container {
                background-color: #1e1f22;
                border: none;
            }
        """)
        
        # Control container
        self.control_container.setStyleSheet("""
            QFrame#editor_control_container {
                background-color: #2b2d30;
                border-top: 1px solid #505254;
            }
        """)
        
        # Tool buttons
        tool_button_style = """
            QPushButton#editor_tool_button {
                font-family: iconfont;
                font-size: 18px;
                background-color: #3d3f4e;
                border: 2px solid #505254;
                border-radius: 6px;
                color: #888888;
            }
            QPushButton#editor_tool_button:hover {
                background-color: #4a4c5e;
                border: 2px solid #5a5c6e;
                color: #E1E1E1;
            }
            QPushButton#editor_tool_button:checked {
                background-color: #4080ff;
                border: 2px solid #4080ff;
                color: #ffffff;
            }
            QPushButton#editor_tool_button:checked:hover {
                background-color: #5090ff;
                border: 2px solid #5090ff;
            }
        """
        
        for btn in self._tool_buttons.values():
            btn.setStyleSheet(tool_button_style)
        
        # Status label
        self.status_label.setStyleSheet("""
            QLabel#editor_status_label {
                color: #888888;
                font-size: 12px;
                padding: 4px 8px;
            }
        """)
        
        # Splitter
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #505254;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
    
    # ========== Signal Handlers ==========
    
    def _handle_tool_button_click(self):
        """Handle tool button click"""
        button = self.sender()
        if button:
            tool_id = button.property("tool_id")
            self._select_tool(tool_id)
    
    def _select_tool(self, tool_id: str):
        """Select a tool"""
        if tool_id not in self._tools:
            return
        
        # Uncheck all buttons
        for btn in self._tool_buttons.values():
            btn.setChecked(False)
        
        # Check the selected button
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].setChecked(True)
        
        # Update current tool
        old_tool = self._current_tool
        self._current_tool = tool_id
        
        # Update placeholder
        tool_info = self._tools[tool_id]
        placeholder = tr("Enter prompt for {tool}...").replace("{tool}", tool_info.name)
        self.prompt_input.set_placeholder(placeholder)
        
        # Emit signal if changed
        if old_tool != tool_id:
            self.tool_changed.emit(tool_id)
            self._update_status(tr("Tool: {tool}").replace("{tool}", tool_info.name))
    
    @Slot(str)
    async def _on_prompt_submitted(self, prompt: str):
        """Handle prompt submission - call tool's params() and submit task"""
        if not prompt.strip():
            return
        
        if not self._current_tool:
            await self._update_status(tr("No tool selected"))
            return
        
        # Get tool instance
        tool = self._get_tool_instance(self._current_tool)
        if not tool:
            await self._update_status(tr("Tool not available"))
            return
        
        try:
            # Get task parameters from tool
            if hasattr(tool, 'params'):
                # Override prompt in tool if it has a prompt attribute
                if hasattr(tool, 'prompt') and hasattr(tool.prompt, 'setText'):  # type: ignore
                    tool.prompt.setText(prompt)  # type: ignore
                
                # Get parameters
                params = tool.params()  # type: ignore
                
                # Submit task via workspace
                self.workspace.submit_task(params)
                
                # Emit signal
                self.task_submitted.emit(params)
                
                # Update status
                await self._set_processing(True)
                await self._update_status(tr("Task submitted..."))
            else:
                await self._update_status(tr("Tool does not support params()"))
        
        except Exception as e:
            print(f"Error submitting task: {e}")
            await self._update_status(tr("Error submitting task"))
    
    # ========== Task Event Handlers ==========
    
    async def on_task_create(self, params):
        """Handle task creation (must be sync - called via blinker signal)"""
        await self._set_processing(True)
        await  self._update_status(tr("Task created"))
    
    async def on_task_execute(self, task: Task):
        """Handle task execution (can be async - called via AsyncQueue)"""
        await  self._set_processing(True)
        await self._update_status(tr("Executing..."))
    
    async def on_task_finished(self, result: TaskResult):
        """Handle task completion (must be sync - called via blinker signal)"""
        await self._set_processing(False)
        
        if result.get_image_path() or result.get_video_path():
            await  self._update_status(tr("Completed"))
        else:
            await self._update_status(tr("Task finished"))

    def on_timeline_switch(self, item: TimelineItem):
        """Handle timeline item switch"""
        # Let tool handle it if it wants
        if self._current_tool:
            tool = self._get_tool_instance(self._current_tool)
            if tool and hasattr(tool, 'on_timeline_switch'):
                tool.on_timeline_switch(item)  # type: ignore
    
    # ========== Public API ==========
    
    def get_current_tool(self) -> Optional[str]:
        """Get current tool ID"""
        return self._current_tool
    
    def set_tool(self, tool_id: str):
        """Set tool programmatically"""
        self._select_tool(tool_id)
    
    def get_tools(self) -> Dict[str, ToolInfo]:
        """Get all registered tools"""
        return self._tools.copy()
    
    def get_preview_widget(self) -> MediaPreviewWidget:
        """Get reference to preview widget"""
        return self.preview_widget
    
    # ========== Helper Methods ==========
    
    async def _set_processing(self, is_processing: bool):
        """Update processing state"""
        self._is_processing = is_processing
        for btn in self._tool_buttons.values():
            btn.setEnabled(not is_processing)
    
    async def _update_status(self, message: str):
        """Update status label"""
        self.status_label.setText(message)
        if not self._is_processing:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.status_label.setText(tr("Ready")))
