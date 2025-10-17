"""
AI Image/Video Editor Component
A comprehensive editor widget with preview area and prompt input controls.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor

from app.ui.base_widget import BaseTaskWidget
from app.ui.preview import MediaPreviewWidget
from app.ui.prompt_input.prompt_input_widget import PromptInputWidget
from app.data.workspace import Workspace
from app.data.task import TaskResult, Task
from app.data.timeline import TimelineItem
from utils.i18n_utils import tr


class EditorWidget(BaseTaskWidget):
    """
    AI Image/Video Editor Component
    
    Layout Structure:
    ┌─────────────────────────────────┐
    │     Preview Area (Top)          │
    │   MediaPreviewWidget            │
    │                                 │
    ├─────────────────────────────────┤
    │  Control Area (Bottom)          │
    │  ┌───────────┬─────────────┐   │
    │  │Mode Switch│Prompt Input │   │
    │  └───────────┴─────────────┘   │
    └─────────────────────────────────┘
    """
    
    # Editing modes
    MODE_TEXT_TO_IMAGE = "text_to_image"
    MODE_IMAGE_TO_VIDEO = "image_to_video"
    MODE_TEXT_TO_VIDEO = "text_to_video"
    MODE_IMAGE_EDIT = "image_edit"
    MODE_VIDEO_EDIT = "video_edit"
    
    # Signals
    mode_changed = Signal(str)  # Emitted when editing mode changes
    prompt_submitted = Signal(str, str)  # Emitted with (mode, prompt)
    
    def __init__(self, workspace: Workspace, parent=None):
        """
        Initialize the editor widget
        
        Args:
            workspace: Workspace data model
            parent: Optional parent widget
        """
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.workspace = workspace
        self._current_mode = self.MODE_TEXT_TO_IMAGE
        self._is_processing = False
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
        self._update_ui_text()
    
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
        control_main_layout.setSpacing(0)  # No spacing, content determines height
        
        # Create horizontal layout for mode buttons and prompt input
        control_h_layout = QHBoxLayout()
        control_h_layout.setSpacing(12)
        control_h_layout.setContentsMargins(0, 0, 0, 0)
        
        # Mode switching section (left)
        mode_section = self._create_mode_section()
        control_h_layout.addWidget(mode_section, 0)  # Don't stretch
        
        # Prompt input section (right)
        self.prompt_input = PromptInputWidget(self.workspace)
        # Set fixed height to match mode buttons (40px)
        self.prompt_input.text_edit.setFixedHeight(40)
        self.prompt_input.text_edit.setMaximumHeight(40)
        self.prompt_input.send_button.setFixedSize(40, 40)  # Match button height
        # Disable expand/collapse behavior
        self.prompt_input._is_expanded = False
        control_h_layout.addWidget(self.prompt_input, 1)  # Stretch to fill
        
        control_main_layout.addLayout(control_h_layout)
        
        # Set fixed height for control container to match content (40px + padding)
        self.control_container.setFixedHeight(40 + 24)  # 40px content + 12px top + 12px bottom
        
        # Add containers to splitter
        self.splitter.addWidget(self.preview_container)
        self.splitter.addWidget(self.control_container)
        
        # Set initial splitter sizes (70% preview, 30% control)
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 3)
        
        # Set minimum sizes
        self.preview_container.setMinimumHeight(300)
        # Control container has fixed height, no minimum needed
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)
        
        self.setLayout(main_layout)
    
    def _create_mode_section(self) -> QWidget:
        """Create mode switching section with icon buttons"""
        mode_widget = QFrame()
        mode_widget.setObjectName("editor_mode_section")
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(8)
        
        # Mode buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        
        # Create mode buttons with icons
        self.mode_buttons = {}
        mode_configs = [
            (self.MODE_TEXT_TO_IMAGE, "\ue82c", tr("Text to Image")),
            (self.MODE_IMAGE_TO_VIDEO, "\ue874", tr("Image to Video")),
            (self.MODE_TEXT_TO_VIDEO, "\ue84b", tr("Text to Video")),
            (self.MODE_IMAGE_EDIT, "\ue837", tr("Image Edit")),
            (self.MODE_VIDEO_EDIT, "\ue834", tr("Video Edit")),
        ]
        
        for mode, icon, tooltip in mode_configs:
            btn = QPushButton(icon)
            btn.setObjectName("editor_mode_button")
            btn.setToolTip(tooltip)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            # Store mode as button property to avoid lambda closure issue
            btn.setProperty("mode", mode)
            btn.clicked.connect(self._handle_mode_button_click)
            self.mode_buttons[mode] = btn
            buttons_layout.addWidget(btn)
        
        # Set initial mode
        self.mode_buttons[self.MODE_TEXT_TO_IMAGE].setChecked(True)
        
        # Status indicator
        self.status_label = QLabel(tr("Ready"))
        self.status_label.setObjectName("editor_status_label")
        
        # Layout
        mode_layout.addWidget(buttons_container)
        mode_layout.addStretch()
        mode_layout.addWidget(self.status_label)
        
        return mode_widget
    
    def _connect_signals(self):
        """Connect signals and slots"""
        # Prompt submission
        self.prompt_input.prompt_submitted.connect(self._on_prompt_submitted)
        
        # Prompt text change
        self.prompt_input.prompt_changed.connect(self._on_prompt_changed)
    
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
        
        # Mode buttons
        mode_button_style = """
            QPushButton#editor_mode_button {
                font-family: iconfont;
                font-size: 18px;
                background-color: #3d3f4e;
                border: 2px solid #505254;
                border-radius: 6px;
                color: #888888;
            }
            QPushButton#editor_mode_button:hover {
                background-color: #4a4c5e;
                border: 2px solid #5a5c6e;
                color: #E1E1E1;
            }
            QPushButton#editor_mode_button:checked {
                background-color: #4080ff;
                border: 2px solid #4080ff;
                color: #ffffff;
            }
            QPushButton#editor_mode_button:checked:hover {
                background-color: #5090ff;
                border: 2px solid #5090ff;
            }
        """
        
        for btn in self.mode_buttons.values():
            btn.setStyleSheet(mode_button_style)
        
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
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
    
    def _update_ui_text(self):
        """Update all translatable UI text"""
        # Update mode button tooltips
        tooltips = {
            self.MODE_TEXT_TO_IMAGE: tr("Text to Image"),
            self.MODE_IMAGE_TO_VIDEO: tr("Image to Video"),
            self.MODE_TEXT_TO_VIDEO: tr("Text to Video"),
            self.MODE_IMAGE_EDIT: tr("Image Edit"),
            self.MODE_VIDEO_EDIT: tr("Video Edit"),
        }
        
        for mode, btn in self.mode_buttons.items():
            btn.setToolTip(tooltips[mode])
        
        # Update status
        if not self._is_processing:
            self.status_label.setText(tr("Ready"))
    
    # ========== Signal Handlers ==========
    
    def _handle_mode_button_click(self):
        """Handle mode button click - wrapper to get mode from sender"""
        button = self.sender()
        if button:
            mode = button.property("mode")
            self._on_mode_button_clicked(mode)
    
    def _on_mode_button_clicked(self, mode: str):
        """Handle mode button click"""
        # Always update selection, even if clicking the same mode
        # This ensures only one button is checked
        
        # Uncheck all buttons first
        for btn in self.mode_buttons.values():
            btn.setChecked(False)
        
        # Check the clicked button
        self.mode_buttons[mode].setChecked(True)
        
        # Only update mode if different
        if mode == self._current_mode:
            return
        
        self._current_mode = mode
        
        # Update placeholder based on mode
        placeholder = self._get_mode_placeholder(mode)
        self.prompt_input.set_placeholder(placeholder)
        
        # Emit signal
        self.mode_changed.emit(mode)
        
        # Update status
        mode_name = self.mode_buttons[mode].toolTip()
        self._update_status(tr("Mode changed to: {mode}").replace(
            "{mode}", mode_name
        ))
    
    @Slot(str)
    def _on_prompt_submitted(self, prompt: str):
        """Handle prompt submission"""
        if not prompt.strip():
            return
        
        # Emit signal with current mode and prompt
        self.prompt_submitted.emit(self._current_mode, prompt)
        
        # Update status
        self._set_processing(True)
        self._update_status(tr("Processing..."))
    
    @Slot(str)
    def _on_prompt_changed(self, text: str):
        """Handle prompt text change"""
        # Can be used for real-time validation or suggestions
        pass
    
    # ========== Task Event Handlers (from BaseTaskWidget) ==========
    
    @Slot()
    async def on_task_create(self, params):
        """Handle task creation"""
        self._set_processing(True)
        self._update_status(tr("Task created"))
    
    @Slot()
    async def on_task_execute(self, task: Task):
        """Handle task execution"""
        self._set_processing(True)
        self._update_status(tr("Executing task..."))
    
    @Slot()
    async def on_task_finished(self, result: TaskResult):
        """Handle task completion"""
        self._set_processing(False)
        
        if result.get_image_path() or result.get_video_path():
            self._update_status(tr("Task completed successfully"))
        else:
            self._update_status(tr("Task completed"))
    
    @Slot()
    def on_timeline_switch(self, item: TimelineItem):
        """Handle timeline item switch"""
        # Preview widget will handle this automatically
        pass
    
    # ========== Public API ==========
    
    def get_current_mode(self) -> str:
        """Get current editing mode"""
        return self._current_mode
    
    def set_mode(self, mode: str):
        """Set editing mode programmatically"""
        if mode in self.mode_buttons:
            self._on_mode_button_clicked(mode)
    
    def get_prompt_text(self) -> str:
        """Get current prompt text"""
        return self.prompt_input.get_prompt_text()
    
    def clear_prompt(self):
        """Clear prompt input"""
        self.prompt_input.clear_prompt()
    
    def get_preview_widget(self) -> MediaPreviewWidget:
        """Get reference to preview widget"""
        return self.preview_widget
    
    def get_prompt_widget(self) -> PromptInputWidget:
        """Get reference to prompt input widget"""
        return self.prompt_input
    
    def set_processing(self, is_processing: bool):
        """Set processing state externally"""
        self._set_processing(is_processing)
    
    # ========== Helper Methods ==========
    
    def _get_mode_placeholder(self, mode: str) -> str:
        """Get placeholder text for specific mode"""
        placeholders = {
            self.MODE_TEXT_TO_IMAGE: tr("Describe the image you want to generate..."),
            self.MODE_IMAGE_TO_VIDEO: tr("Describe the video motion or animation..."),
            self.MODE_TEXT_TO_VIDEO: tr("Describe the video you want to create..."),
            self.MODE_IMAGE_EDIT: tr("Describe the edits you want to apply..."),
            self.MODE_VIDEO_EDIT: tr("Describe the video edits you want to make..."),
        }
        return placeholders.get(mode, tr("Enter your prompt here..."))
    
    def _set_processing(self, is_processing: bool):
        """Update processing state"""
        self._is_processing = is_processing
        
        # Disable/enable mode buttons during processing
        for btn in self.mode_buttons.values():
            btn.setEnabled(not is_processing)
        # prompt_input handles its own state
    
    def _update_status(self, message: str):
        """Update status label"""
        self.status_label.setText(message)
        
        # Auto-reset status after delay for non-processing messages
        if not self._is_processing:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.status_label.setText(tr("Ready")))
