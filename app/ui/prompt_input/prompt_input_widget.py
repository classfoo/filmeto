from PySide6.QtCore import Qt, Signal, QTimer, QEvent, Slot, QRect, QPoint
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, 
                               QPushButton, QLabel, QListWidget, QDialog, 
                               QFileDialog, QLineEdit, QMessageBox, QScrollArea,
                               QFrame, QStackedWidget, QSizePolicy)
from PySide6.QtGui import QCursor, QTextCursor, QKeyEvent

from app.ui.base_widget import BaseWidget, BaseTaskWidget
from app.ui.prompt_input.template_item_widget import TemplateItemWidget
from app.data.workspace import Workspace, PromptTemplate, PromptManager
from utils.i18n_utils import tr, translation_manager


class PromptInputWidget(BaseTaskWidget):
    """
    Reusable prompt input component with template management
    """
    
    # Signals
    prompt_submitted = Signal(str)  # Emitted when send button clicked
    prompt_changed = Signal(str)    # Emitted when text changes
    
    def __init__(self, workspace: Workspace, parent=None):
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        self.prompt_manager: PromptManager = workspace.get_prompt_manager()
        
        # State variables
        self._has_focus = False
        self._mouse_over = False
        self._current_text = ""
        self._selected_template = None
        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(300)  # 300ms debounce
        self._in_input_mode = False  # Track if user is actually inputting text
        
        self._setup_ui()
        self._connect_signals()
        self._apply_initial_style()
        self._update_ui_text()
        
        # Set size policy to expand and fill parent
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Connect to language change signal (use lambda to handle optional parameter)
        translation_manager.language_changed.connect(lambda lang: self._update_ui_text())
    
    def _setup_ui(self):
        """Initialize UI components with horizontal split layout"""
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Remove spacing between panels
        
        # Left panel - Tool configuration container with scroll support
        self.left_panel = QWidget()
        self.left_panel.setObjectName("prompt_left_panel")
        # Don't set fixed width - let it adapt to content

        self.left_panel_layout = QVBoxLayout(self.left_panel)
        self.left_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.left_panel_layout.setSpacing(4)

        # Right panel - Prompt input container
        self.right_panel = QWidget()
        self.right_panel.setObjectName("prompt_right_panel")
        right_panel_layout = QHBoxLayout(self.right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(4)
        
        # Text edit field
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("prompt_text_edit")
        self.text_edit.setPlaceholderText(tr("Enter your prompt here..."))
        self.text_edit.setMinimumWidth(200)
        self.text_edit.setFixedHeight(64)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.installEventFilter(self)
        
        # Send button (square, 44x44)
        self.send_button = QPushButton("\ue83e")  # Play icon for send button
        self.send_button.setObjectName("prompt_send_button")
        self.send_button.setFixedSize(44, 44)
        self.send_button.setToolTip(tr("Submit prompt"))
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Add widgets to input layout
        right_panel_layout.addWidget(self.text_edit, 1)
        right_panel_layout.addWidget(self.send_button, 0)
        
        # Add to right panel layout
        #right_panel_layout.addWidget(self.input_layout)
        
        # Add panels to main layout
        main_layout.addWidget(self.left_panel, 1)
        main_layout.addWidget(self.right_panel, 1)
        
        self.setLayout(main_layout)
    
    def _connect_signals(self):
        """Connect signals and slots"""
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.send_button.clicked.connect(self._on_send_clicked)

    def _apply_initial_style(self):
        """Apply initial styling"""
        # Apply overall border to the widget itself
        self.setStyleSheet("""
            PromptInputWidget {
                background-color: #2d2d2d;
                border: 0px solid #505254;
                border-radius: 4px;
            }
        """)
        
        self.text_edit.setStyleSheet("""
            QTextEdit#prompt_text_edit {
                background-color: #2b2d30;
                border: none;  /* Remove border */
                border-radius: 4px;
                padding: 0px;
                margin: 4px;
                color: #E1E1E1;
                font-size: 14px;
                selection-background-color: #4080ff;
                height:76px;
            }
            QTextEdit#prompt_text_edit:focus {
                border: none;  /* Remove border */
            }
        """)
        
        self.send_button.setStyleSheet("""
            QPushButton#prompt_send_button {
                background-color: #3d3f4e;
                border: none;
                border-radius: 22px;
                color: #E1E1E1;
                font-size: 16px;
            }
            QPushButton#prompt_send_button:hover {
                background-color: #4080ff;
            }
            QPushButton#prompt_send_button:pressed {
                background-color: #3060cc;
            }
        """)

        self.right_panel.setStyleSheet("""
            QWidget#prompt_right_panel {
                background-color: #2d2d2d;
                border: 2px solid #505254;
                border-radius: 4px;
            }
        """)
        
        self.left_panel.setStyleSheet("""
            QWidget#prompt_left_panel {
                background-color: #2d2d2d;
                border: none;
                border-radius: 0px;
            }
            QFrame#prompt_left_panel_content {
                background-color: #2d2d2d;
                border: none;
                border-radius: 0px;
            }
        """)
    
    def eventFilter(self, obj, event):
        """Filter events for text edit widget"""
        if obj == self.text_edit:
            if event.type() == QEvent.FocusIn:
                self._on_input_focus_in()
            elif event.type() == QEvent.FocusOut:
                self._on_input_focus_out()
            elif event.type() == QEvent.Enter:
                self._on_mouse_enter()
            elif event.type() == QEvent.Leave:
                self._on_mouse_leave()
            elif event.type() == QEvent.KeyPress:
                return self._handle_key_press(event)
        
        return super().eventFilter(obj, event)
    
    def _on_input_focus_in(self):
        """Handle input field focus in"""
        self._has_focus = True
        self._update_text_edit_style()
    
    def _on_input_focus_out(self):
        """Handle input field focus out"""
        self._has_focus = False
        self._update_text_edit_style()
    
    def _on_mouse_enter(self):
        """Handle mouse enter event"""
        self._mouse_over = True
    
    def _on_mouse_leave(self):
        """Handle mouse leave event"""
        self._mouse_over = False
    
    def _update_text_edit_style(self):
        """Update text edit style based on focus state only"""
        if self._has_focus:
            self.text_edit.setStyleSheet("""
                QTextEdit#prompt_text_edit {
                    background-color: #2b2d30;
                    border: none;  /* Remove border */
                    border-radius: 8px;
                    padding: 8px;
                    color: #E1E1E1;
                    font-size: 14px;
                    selection-background-color: #4080ff;
                }
            """)
        else:
            self.text_edit.setStyleSheet("""
                QTextEdit#prompt_text_edit {
                    background-color: #2b2d30;
                    border: none;  /* Remove border */
                    border-radius: 8px;
                    padding: 8px;
                    color: #E1E1E1;
                    font-size: 14px;
                    selection-background-color: #4080ff;
                }
            """)
    
    def _on_text_changed(self):
        """Handle text change event"""
        text = self.text_edit.toPlainText()
        self._current_text = text
        
        # Track if user is actually inputting text
        if text.strip() and not self._in_input_mode:
            self._in_input_mode = True
        elif not text.strip() and self._in_input_mode:
            self._in_input_mode = False
        
        # Emit signal
        self.prompt_changed.emit(text)
        
        # Trigger template filtering with debounce
        self._filter_timer.start()
    
    def _on_send_clicked(self):
        """Handle send button click"""
        text = self._current_text.strip()
        
        if not text:
            QMessageBox.warning(self, tr("Empty Input"), tr("Please enter a prompt"))
            return
        
        # Emit signal
        self.prompt_submitted.emit(text)
    
    def _handle_key_press(self, event: QKeyEvent) -> bool:
        """Handle key press events"""
        # Enter key submits (without Ctrl)
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ControlModifier:
                # Ctrl+Enter inserts line break (default behavior)
                return False
            else:
                # Enter submits
                self._on_send_clicked()
                return True
        
        # Escape closes dropdown
        elif event.key() == Qt.Key_Escape:
            if self.template_dropdown_container.isVisible():
                self.template_dropdown_container.hide()
                return True
        
        return False
    
    # Public API
    
    def set_placeholder(self, text: str):
        """Set input field placeholder text"""
        self.text_edit.setPlaceholderText(text)
    
    def get_prompt_text(self) -> str:
        """Retrieve current prompt text"""
        return self._current_text
    
    def clear_prompt(self):
        """Clear input field content"""
        self.text_edit.clear()
        self._current_text = ""
        self.template_dropdown_container.hide()
        self._in_input_mode = False  # Reset input mode when clearing
        self.token_badge.hide()  # Hide token badge
    
    def on_timeline_switch(self, item):
        """Load and display the prompt content from the timeline item"""
        from app.data.timeline import TimelineItem
        if isinstance(item, TimelineItem):
            # Get the current tool name if available - this method can be overridden
            # by parent widgets to provide the selected tool
            tool_name = self.get_current_tool_name()
            
            if tool_name:
                # Load tool-specific prompt
                prompt_content = item.get_prompt(tool_name)
            else:
                # Fallback to general prompt
                prompt_content = item.get_prompt()
                
            if prompt_content is not None:
                self.text_edit.setPlainText(str(prompt_content))
            else:
                # If no prompt in timeline item, clear the input
                self.text_edit.clear()
            self._in_input_mode = False  # Reset input mode when switching timeline
    
    def get_current_tool_name(self) -> str:
        """
        Get the currently selected tool name.
        This method can be overridden by parent widgets to provide the actual selected tool.
        Default implementation returns None.
        """
        return None
    
    def on_project_switched(self, project_name):
        """处理项目切换"""
        # 重新初始化提示管理器
        self.prompt_manager = self.workspace.get_prompt_manager()
        
        # 清除当前内容
        self.clear_prompt()
        
        # 隐藏模板下拉框
        self.template_dropdown_container.hide()
        self._in_input_mode = False  # Reset input mode when switching projects
    
    def set_config_panel_widget(self, widget):
        """
        Set a custom widget for the left configuration panel.
        
        Args:
            widget: QWidget to display in the left panel
        """
        if not hasattr(self, 'left_panel_layout'):
            return
            
        # Clear existing widgets from left panel layout
        while self.left_panel_layout.count():
            item = self.left_panel_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        
        # Add new widget if provided
        if widget:
            # Set maximum height to prevent overflow
            # Ensure widget doesn't exceed the available height
            widget.setMaximumHeight(60)  # Limit height to prevent covering input area
            
            self.left_panel_layout.addWidget(widget)
            self.left_panel_layout.addStretch()
            
            # Adjust left panel width based on widget's size hint or minimum width
            # Allow the widget to determine the width naturally
            widget_width = widget.sizeHint().width()
            if widget_width > 0:
                # Add margins and scrollbar space to the width (8px left + 8px right + scrollbar)
                self.left_panel.setFixedWidth(widget_width + 25)
            else:
                # Fallback to minimum size if size hint is not available
                widget.adjustSize()
                min_width = widget.minimumSizeHint().width()
                if min_width > 0:
                    self.left_panel.setFixedWidth(min_width + 25)
                else:
                    # Final fallback to default width
                    self.left_panel.setFixedWidth(250)
        else:
            # Show placeholder if no widget provided and reset to default width
            self.left_panel.setFixedWidth(250)
            self.config_placeholder = QLabel(tr("Configuration options will appear here"))
            self.config_placeholder.setStyleSheet("color: #CCCCCC; font-size: 12px;")
            self.config_placeholder.setAlignment(Qt.AlignCenter)
            self.left_panel_layout.addWidget(self.config_placeholder)
    
    @Slot()
    def _update_ui_text(self):
        """Update all translatable UI text"""
        # Update placeholder
        current_placeholder = self.text_edit.placeholderText()
        new_placeholder = tr("Enter your prompt here...")
        if current_placeholder != new_placeholder:
            self.text_edit.setPlaceholderText(new_placeholder)
        
        # Update tooltip
        current_tooltip = self.send_button.toolTip()
        new_tooltip = tr("Submit prompt")
        if current_tooltip != new_tooltip:
            self.send_button.setToolTip(new_tooltip)