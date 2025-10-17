"""
AI Image/Video Editor Component
A comprehensive editor widget with preview area and prompt input controls.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor, Qt as QtGui

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
        control_main_layout.setSpacing(12)
        
        # Mode switching section
        mode_section = self._create_mode_section()
        control_main_layout.addWidget(mode_section)
        
        # Prompt input section
        self.prompt_input = PromptInputWidget(self.workspace)
        control_main_layout.addWidget(self.prompt_input)
        
        # Add containers to splitter
        self.splitter.addWidget(self.preview_container)
        self.splitter.addWidget(self.control_container)
        
        # Set initial splitter sizes (70% preview, 30% control)
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 3)
        
        # Set minimum sizes
        self.preview_container.setMinimumHeight(300)
        self.control_container.setMinimumHeight(150)
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)
        
        self.setLayout(main_layout)
    
    def _create_mode_section(self) -> QWidget:
        """Create mode switching section"""
        mode_widget = QFrame()
        mode_widget.setObjectName("editor_mode_section")
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(8)
        
        # Mode label
        self.mode_label = QLabel(tr("Mode:"))
        self.mode_label.setObjectName("editor_mode_label")
        
        # Mode selector (combo box)
        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("editor_mode_combo")
        self.mode_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mode_combo.setMinimumWidth(200)
        
        # Add modes
        self.mode_combo.addItem(tr("Text to Image"), self.MODE_TEXT_TO_IMAGE)
        self.mode_combo.addItem(tr("Image to Video"), self.MODE_IMAGE_TO_VIDEO)
        self.mode_combo.addItem(tr("Text to Video"), self.MODE_TEXT_TO_VIDEO)
        self.mode_combo.addItem(tr("Image Edit"), self.MODE_IMAGE_EDIT)
        self.mode_combo.addItem(tr("Video Edit"), self.MODE_VIDEO_EDIT)
        
        # Status indicator
        self.status_label = QLabel(tr("Ready"))
        self.status_label.setObjectName("editor_status_label")
        
        # Layout
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        mode_layout.addWidget(self.status_label)
        
        return mode_widget
    
    def _connect_signals(self):
        """Connect signals and slots"""
        # Mode change
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        
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
        
        # Mode section
        self.mode_label.setStyleSheet("""
            QLabel#editor_mode_label {
                color: #E1E1E1;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # Mode combo box
        self.mode_combo.setStyleSheet("""
            QComboBox#editor_mode_combo {
                background-color: #3d3f4e;
                border: 1px solid #505254;
                border-radius: 6px;
                padding: 6px 12px;
                color: #E1E1E1;
                font-size: 13px;
            }
            QComboBox#editor_mode_combo:hover {
                border: 1px solid #4080ff;
            }
            QComboBox#editor_mode_combo::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox#editor_mode_combo::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #E1E1E1;
                margin-right: 4px;
            }
            QComboBox#editor_mode_combo QAbstractItemView {
                background-color: #3d3f4e;
                border: 1px solid #505254;
                selection-background-color: #4080ff;
                selection-color: #ffffff;
                color: #E1E1E1;
            }
        """)
        
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
        # Update mode combo items
        for i in range(self.mode_combo.count()):
            mode_data = self.mode_combo.itemData(i)
            if mode_data == self.MODE_TEXT_TO_IMAGE:
                self.mode_combo.setItemText(i, tr("Text to Image"))
            elif mode_data == self.MODE_IMAGE_TO_VIDEO:
                self.mode_combo.setItemText(i, tr("Image to Video"))
            elif mode_data == self.MODE_TEXT_TO_VIDEO:
                self.mode_combo.setItemText(i, tr("Text to Video"))
            elif mode_data == self.MODE_IMAGE_EDIT:
                self.mode_combo.setItemText(i, tr("Image Edit"))
            elif mode_data == self.MODE_VIDEO_EDIT:
                self.mode_combo.setItemText(i, tr("Video Edit"))
        
        # Update labels
        self.mode_label.setText(tr("Mode:"))
        if not self._is_processing:
            self.status_label.setText(tr("Ready"))
    
    # ========== Signal Handlers ==========
    
    @Slot(int)
    def _on_mode_changed(self, index: int):
        """Handle mode change"""
        if index < 0:
            return
        
        new_mode = self.mode_combo.itemData(index)
        if new_mode == self._current_mode:
            return
        
        self._current_mode = new_mode
        
        # Update placeholder based on mode
        placeholder = self._get_mode_placeholder(new_mode)
        self.prompt_input.set_placeholder(placeholder)
        
        # Emit signal
        self.mode_changed.emit(new_mode)
        
        # Update status
        self._update_status(tr("Mode changed to: {mode}").replace(
            "{mode}", self.mode_combo.currentText()
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
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == mode:
                self.mode_combo.setCurrentIndex(i)
                break
    
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
        
        # Disable/enable controls during processing
        self.mode_combo.setEnabled(not is_processing)
        # prompt_input handles its own state
    
    def _update_status(self, message: str):
        """Update status label"""
        self.status_label.setText(message)
        
        # Auto-reset status after delay for non-processing messages
        if not self._is_processing:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.status_label.setText(tr("Ready")))
