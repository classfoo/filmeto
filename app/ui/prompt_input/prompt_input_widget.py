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
        
        # Left panel - Tool configuration container
        self.left_panel = QFrame()
        self.left_panel.setObjectName("prompt_left_panel")
        # Don't set fixed width - let it adapt to content
        self.left_panel_layout = QVBoxLayout(self.left_panel)
        self.left_panel_layout.setContentsMargins(8, 8, 8, 8)
        self.left_panel_layout.setSpacing(6)
        
        # Placeholder label for left panel
        self.config_placeholder = QLabel(tr("Configuration options will appear here"))
        self.config_placeholder.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        self.config_placeholder.setAlignment(Qt.AlignCenter)
        self.left_panel_layout.addWidget(self.config_placeholder)
        
        # Right panel - Prompt input container
        self.right_panel = QWidget()
        self.right_panel.setObjectName("prompt_right_panel")
        right_panel_layout = QVBoxLayout(self.right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(4)
        
        # Template dropdown container (positioned above input row)
        self.template_dropdown_container = QFrame()
        self.template_dropdown_container.setObjectName("prompt_template_dropdown")
        self.template_dropdown_container.setFrameShape(QFrame.StyledPanel)
        self.template_dropdown_container.hide()  # Hidden by default
        
        dropdown_layout = QVBoxLayout(self.template_dropdown_container)
        dropdown_layout.setContentsMargins(4, 4, 4, 4)
        dropdown_layout.setSpacing(2)
        
        # Template list scroll area
        self.template_scroll = QScrollArea()
        self.template_scroll.setWidgetResizable(True)
        self.template_scroll.setMaximumHeight(200)
        self.template_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.template_list_widget = QWidget()
        self.template_list_layout = QVBoxLayout(self.template_list_widget)
        self.template_list_layout.setContentsMargins(0, 0, 0, 0)
        self.template_list_layout.setSpacing(2)
        self.template_list_layout.addStretch()
        
        self.template_scroll.setWidget(self.template_list_widget)
        dropdown_layout.addWidget(self.template_scroll)
        
        # Input row container (TextEdit + Send Button)
        self.input_container = QWidget()
        self.input_container.setObjectName("prompt_input_container")
        self.input_container.setFixedHeight(44)
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        # Text edit field
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("prompt_text_edit")
        self.text_edit.setPlaceholderText(tr("Enter your prompt here..."))
        self.text_edit.setMinimumWidth(200)
        self.text_edit.setFixedHeight(44)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.installEventFilter(self)
        
        # Send button (square, 44x44)
        self.send_button = QPushButton("\ue83e")  # Play icon for send button
        self.send_button.setObjectName("prompt_send_button")
        self.send_button.setFixedSize(44, 44)
        self.send_button.setToolTip(tr("Submit prompt"))
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Token count badge (child of send button)
        self.token_badge = QLabel("", self.send_button)
        self.token_badge.setObjectName("token_badge")
        self.token_badge.hide()  # Hidden by default
        self.token_badge.setAlignment(Qt.AlignCenter)
        
        # Add widgets to input layout
        input_layout.addWidget(self.text_edit, 1)
        input_layout.addWidget(self.send_button, 0)
        
        # Add to right panel layout
        right_panel_layout.addWidget(self.template_dropdown_container)
        right_panel_layout.addStretch()
        right_panel_layout.addWidget(self.input_container)
        
        # Add panels to main layout
        main_layout.addWidget(self.left_panel, 0)
        main_layout.addWidget(self.right_panel, 1)
        
        self.setLayout(main_layout)
    
    def _update_token_badge(self):
        """Update token badge position and content"""
        if not self._current_text:
            self.token_badge.hide()
            return
        
        # Calculate token count (characters / 4 heuristic)
        char_count = len(self._current_text)
        token_count = max(1, char_count // 4)
        
        # Determine display text and style
        if token_count >= 10000:
            display_text = "9999+"
            bg_color = "#ff6b6b"  # Warning style
        else:
            display_text = str(token_count)
            bg_color = "rgba(45, 45, 45, 0.8)"  # Normal style
        
        self.token_badge.setText(display_text)
        self.token_badge.setStyleSheet(f"""
            QLabel#token_badge {{
                background-color: {bg_color};
                color: #FFFFFF;
                font-size: 10px;
                padding: 2px 4px;
                border-radius: 4px;
            }}
        """)
        
        # Position badge at top-right corner
        self.token_badge.adjustSize()
        badge_width = self.token_badge.width()
        badge_height = self.token_badge.height()
        self.token_badge.move(
            self.send_button.width() - badge_width - 2,
            2
        )
        self.token_badge.show()
    
    def _connect_signals(self):
        """Connect signals and slots"""
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.send_button.clicked.connect(self._on_send_clicked)
        self._filter_timer.timeout.connect(self._filter_templates)
    
    def _apply_initial_style(self):
        """Apply initial styling"""
        # Apply overall border to the widget itself
        self.setStyleSheet("""
            PromptInputWidget {
                background-color: #2d2d2d;
                border: 1px solid #505254;
                border-radius: 8px;
            }
        """)
        
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
        
        self.left_panel.setStyleSheet("""
            QFrame#prompt_left_panel {
                background-color: #2d2d2d;
                border: none;  /* Remove border */
                border-radius: 0px;  /* Remove rounded corners */
            }
        """)
        
        self.template_dropdown_container.setStyleSheet("""
            QFrame#prompt_template_dropdown {
                background-color: #2c2c2c;
                border: none;  /* Remove border */
                border-radius: 8px;
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
        
        # Update token badge
        self._update_token_badge()
        
        # Emit signal
        self.prompt_changed.emit(text)
        
        # Trigger template filtering with debounce
        self._filter_timer.start()
    
    def _filter_templates(self):
        """Filter templates based on current text"""
        query = self._current_text.strip()
        
        if not query:
            self.template_dropdown_container.hide()
            return
        
        # Search templates
        templates = self.prompt_manager.search_templates(query)
        
        if not templates:
            self.template_dropdown_container.hide()
            return
        
        # Clear existing items
        while self.template_list_layout.count() > 1:  # Keep the stretch
            item = self.template_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add filtered templates
        for template in templates[:10]:  # Show max 10 results
            item_widget = TemplateItemWidget(template)
            item_widget.clicked.connect(self._on_template_selected)
            self.template_list_layout.insertWidget(
                self.template_list_layout.count() - 1, 
                item_widget
            )
        
        self.template_dropdown_container.show()
    
    def _on_template_selected(self, template: PromptTemplate):
        """Handle template selection"""
        self._selected_template = template
        
        # Populate input field
        self.text_edit.setPlainText(template.text)
        
        # Move cursor to end
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        
        # Close dropdown
        self.template_dropdown_container.hide()
        
        # Focus input field
        self.text_edit.setFocus()
        
        # Increment usage count
        self.prompt_manager.increment_usage(template.id)
    
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
            self.left_panel_layout.addWidget(widget)
            self.left_panel_layout.addStretch()
            
            # Adjust left panel width based on widget's size hint or minimum width
            # Allow the widget to determine the width naturally
            widget_width = widget.sizeHint().width()
            if widget_width > 0:
                # Add margins to the width (8px left + 8px right = 16px)
                self.left_panel.setFixedWidth(widget_width + 16)
            else:
                # Fallback to minimum size if size hint is not available
                widget.adjustSize()
                min_width = widget.minimumSizeHint().width()
                if min_width > 0:
                    self.left_panel.setFixedWidth(min_width + 16)
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
        
        # Update token badge
        self._update_token_badge()