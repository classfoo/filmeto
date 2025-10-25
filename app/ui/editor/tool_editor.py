"""
AI Image/Video Editor Component with Dynamic Tool Loading
A comprehensive editor widget that dynamically loads tools from plugins/tools directory.
"""

from typing import Dict, Optional
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
from app.plugins.plugins import ToolInfo
from utils.i18n_utils import tr


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
        self._is_processing = False
        self._tool_instances: Dict[str, BaseTool] = {}  # tool_id -> tool instance
        self._tool_buttons: Dict[str, QPushButton] = {}  # tool_id -> button
        
        # Load available tools from plugins
        from app.plugins.plugins import Plugins
        self.plugins = Plugins(None)
        self._tools = self.plugins.get_tool_registry()
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
        self.current_tool = None
        self.update_current_tool(self.workspace.get_project().get_timeline().get_current_item())

    def update_current_tool(self,current_timeline_item):
        if self.current_tool is None:
            self.current_tool = current_timeline_item.get_config_value("current_tool")
        else:
            old_tool = self.current_tool
            self.current_tool = current_timeline_item.get_config_value("current_tool")
            if old_tool == self.current_tool:
                return

        # Set initial tool if any available
        if self._tools:
            if self.current_tool is None:
                first_tool = list(self._tools.keys())[0]
                self.current_tool = first_tool
                self._select_tool(first_tool)
            else:
                self._select_tool(self.current_tool)
    
    def _get_tool_instance(self, tool_id: str) -> Optional[BaseTool]:
        
        if tool_id not in self._tool_instances:
            # Create new instance
            tool_info = self._tools[tool_id]
            try:
                instance = tool_info.tool_class(self.workspace, self)
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
        # Override the get_current_tool_name method to return the current tool
        original_get_current_tool_name = self.prompt_input.get_current_tool_name
        def get_current_tool_name_override():
            return self.current_tool
        self.prompt_input.get_current_tool_name = get_current_tool_name_override
        # Set fixed height to match tool buttons (40px)
        self.prompt_input.text_edit.setFixedHeight(40)
        self.prompt_input.text_edit.setMaximumHeight(40)
        self.prompt_input.send_button.setFixedSize(40, 40)
        self.prompt_input._is_expanded = False
        control_h_layout.addWidget(self.prompt_input, 1)  # Stretch to fill
        
        control_main_layout.addLayout(control_h_layout)
        
        # Set fixed height for control container (40px + padding)
        self.control_container.setFixedHeight(72)  # 40px content + 12px top + 12px bottom
        
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
            btn.setToolTip(tool_info.name)  # Tooltip shows text on hover, but not visible text on button
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            btn.setProperty("tool_id", tool_id)
            btn.clicked.connect(self._handle_tool_button_click)
            self._tool_buttons[tool_id] = btn
            buttons_layout.addWidget(btn)
        
        # Layout
        tool_layout.addWidget(buttons_container)
        tool_layout.addStretch()
        
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
        old_tool=self.current_tool
        self.current_tool = tool_id
        # Uncheck all buttons
        for btn in self._tool_buttons.values():
            btn.setChecked(False)
        
        # Check the selected button
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].setChecked(True)
        self._update_preview(tool_id)
        # Update placeholder
        tool_info = self._tools[tool_id]
        placeholder = tr("Enter prompt for {tool}...").replace("{tool}", tool_info.name)
        self.prompt_input.set_placeholder(placeholder)
        
        # Update the prompt input with the current tool's prompt from the current timeline item
        self._update_prompt(tool_id)
        
        # Emit signal if changed
        if old_tool != tool_id:
            self.tool_changed.emit(tool_id)

    def _update_preview(self, tool_id):
        timeline_item = self.workspace.get_project().get_timeline().get_current_item()
        timeline_item.set_config_value("current_tool",self.current_tool)
        tool_instance = (self._get_tool_instance(tool_id))
        if tool_instance:
            tool_instance.on_timeline_switch(timeline_item)

    def _update_prompt(self,tool_id):
        # Get the current timeline item
        timeline_index = self.workspace.get_project().get_timeline_index()
        current_item = self.workspace.get_project().get_timeline().get_item(timeline_index)
        
        # Get the prompt for the current tool from the timeline item
        tool_prompt = current_item.get_prompt(tool_id)
        
        # Update the prompt input text
        if tool_prompt:
            self.prompt_input.text_edit.setPlainText(str(tool_prompt))
        else:
            # If no tool-specific prompt exists, clear the input
            self.prompt_input.text_edit.clear()
    
    # def _refresh_preview_for_tool(self, tool_id: str):
    #     """Refresh preview widget based on selected tool"""
    #     # Get the current timeline item
    #     timeline_index = self.workspace.get_project().get_timeline_index()
    #     current_item = self.workspace.get_project().get_timeline().get_item(timeline_index)
    #
    #     # Get tool instance
    #     tool = self._get_tool_instance(tool_id)
    #     if not tool:
    #         return
    #
    #     # Let the tool handle its own UI refresh
    #     tool.handle_timeline_switch(self.preview_widget, current_item)
    
    @Slot(str)
    def _on_prompt_submitted(self, prompt: str):
        """Handle prompt submission - call tool's params() and submit task"""
        if not prompt.strip():
            return
        
        if not self.current_tool:
            print(tr("No tool selected"))
            return
        
        # Get tool instance
        tool = self._get_tool_instance(self.current_tool)
        if not tool:
            print(tr("Tool not available"))
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
                print(tr("Task submitted..."))
            else:
                print(tr("Tool does not support params()"))
        
        except Exception as e:
            print(f"Error submitting task: {e}")
            print(tr("Error submitting task"))
    
    # ========== Task Event Handlers ==========
    
    def on_task_create(self, params):
        """Handle task creation (must be sync - called via blinker signal)"""
        self._set_processing(True)
        print(tr("Task created"))
    
    def on_task_finished(self, result: TaskResult):
        """Handle task completion (must be sync - called via blinker signal)"""
        self._set_processing(False)
        
        if result.get_image_path() or result.get_video_path():
            print(tr("Completed"))
        else:
            print(tr("Task finished"))

    def on_timeline_switch(self, item: TimelineItem):
        """Handle timeline item switch"""
        # Auto-select tool based on media type
        # If video exists, select img2video tool, otherwise select text2img tool
        # if os.path.exists(item.get_video_path()):
        #     # Video exists, select img2video tool if available
        #     if "img2video" in self._tools:
        #         self._select_tool("img2video")
        # else:
        #     # No video, select text2img tool if available
        #     if "text2img" in self._tools:
        #         self._select_tool("text2img")
        self.update_current_tool(item)
        pass
    
    # ========== Public API ==========
    
    def get_current_tool(self) -> Optional[str]:
        """Get current tool ID"""
        return self.current_tool
    
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
    
    def _set_processing(self, is_processing: bool):
        """Update processing state"""
        self._is_processing = is_processing
        # 不再禁用工具按钮，允许在任务执行期间切换工具和提交新任务
        # for btn in self._tool_buttons.values():
        #     btn.setEnabled(not is_processing)

    def get_review_widget(self):
        return self.preview_widget