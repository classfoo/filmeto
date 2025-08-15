from PySide6.QtCore import Qt, Signal, QTimer, QEvent, Slot
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, 
                               QPushButton, QLabel, QListWidget, QDialog, 
                               QFileDialog, QLineEdit, QMessageBox, QScrollArea,
                               QFrame)
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
        
        self._setup_ui()
        self._connect_signals()
        self._apply_initial_style()
        self._update_ui_text()
        
        # Connect to language change signal (use lambda to handle optional parameter)
        translation_manager.language_changed.connect(lambda lang: self._update_ui_text())
    
    def _setup_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        # Input container (TextEdit + Send Button)
        self.input_container = QWidget()
        self.input_container.setObjectName("prompt_input_container")
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        # Text edit field
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("prompt_text_edit")
        self.text_edit.setPlaceholderText(tr("Enter your prompt here..."))
        self.text_edit.setMinimumWidth(200)
        self.text_edit.setMinimumHeight(40)  # Increased to accommodate border and padding
        self.text_edit.setMaximumHeight(40)  # Increased to accommodate border and padding
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.installEventFilter(self)
        
        # Send button
        self.send_button = QPushButton("\ue83e")  # Play icon for send button
        self.send_button.setObjectName("prompt_send_button")
        self.send_button.setFixedSize(36, 44)  # Match the text edit height for alignment
        self.send_button.setToolTip(tr("Submit prompt"))
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Character counter - only the number
        self.char_counter = QLabel("0")
        self.char_counter.setObjectName("prompt_char_counter")
        self.char_counter.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Align vertically with input
        self.char_counter.hide()  # Hidden by default
        
        # Add all elements to the horizontal input layout - char counter at the end (rightmost)
        input_layout.addWidget(self.text_edit, 1)
        input_layout.addWidget(self.send_button, 0)
        input_layout.addWidget(self.char_counter, 0)
        
        # Template dropdown container
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
        
        # Add to main layout
        main_layout.addWidget(self.input_container)
        main_layout.addWidget(self.template_dropdown_container)
        
        self.setLayout(main_layout)
    
    def _connect_signals(self):
        """Connect signals and slots"""
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.send_button.clicked.connect(self._on_send_clicked)
        self._filter_timer.timeout.connect(self._filter_templates)
    
    def _apply_initial_style(self):
        """Apply initial styling"""
        self.text_edit.setStyleSheet("""
            QTextEdit#prompt_text_edit {
                background-color: #2b2d30;
                border: 1px solid #505254;
                border-radius: 8px;
                padding: 8px;
                color: #E1E1E1;
                font-size: 14px;
            }
            QTextEdit#prompt_text_edit:focus {
                border: 1px solid #4080ff;
            }
        """)
        
        self.send_button.setStyleSheet("""
            QPushButton#prompt_send_button {
                background-color: #3d3f4e;
                border: none;
                border-radius: 18px;
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
        
        self.char_counter.setStyleSheet("""
            QLabel#prompt_char_counter {
                color: #888888;
                font-size: 11px;
                padding: 0px 4px;
            }
        """)
        
        self.template_dropdown_container.setStyleSheet("""
            QFrame#prompt_template_dropdown {
                background-color: #2c2c2c;
                border: 1px solid #505254;
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
        # Always show character counter when focused
        self.char_counter.show()
        self._update_text_edit_style()
    
    def _on_input_focus_out(self):
        """Handle input field focus out"""
        self._has_focus = False
        # Hide character counter when losing focus
        self.char_counter.hide()
        self._update_text_edit_style()
    
    def _on_mouse_enter(self):
        """Handle mouse enter event - no expansion on hover"""
        self._mouse_over = True
        # Show character counter on hover
        self.char_counter.show()
    
    def _on_mouse_leave(self):
        """Handle mouse leave event - no expansion on hover"""
        self._mouse_over = False
        # Hide character counter if not focused
        if not self._has_focus:
            self.char_counter.hide()
    
    def _update_text_edit_style(self):
        """Update text edit style based on focus state only"""
        if self._has_focus:
            self.text_edit.setStyleSheet("""
                QTextEdit#prompt_text_edit {
                    background-color: #2b2d30;
                    border: 1px solid #4080ff;
                    border-radius: 8px;
                    padding: 8px;
                    color: #E1E1E1;
                    font-size: 14px;
                }
            """)
        else:
            self.text_edit.setStyleSheet("""
                QTextEdit#prompt_text_edit {
                    background-color: #2b2d30;
                    border: 1px solid #505254;
                    border-radius: 8px;
                    padding: 8px;
                    color: #E1E1E1;
                    font-size: 14px;
                }
            """)
    
    def _on_text_changed(self):
        """Handle text change event"""
        text = self.text_edit.toPlainText()
        self._current_text = text
        
        # Update character counter
        char_count = len(text)
        self.char_counter.setText(str(char_count))
        
        # Emit signal
        self.prompt_changed.emit(text)
        
        # Trigger template filtering with debounce
        self._filter_timer.start()
        
        # Show warning if text is too long
        if char_count > 10000:
            self.char_counter.setStyleSheet("""
                QLabel#prompt_char_counter {
                    color: #ff6b6b;
                    font-size: 11px;
                    padding: 2px 4px;
                }
            """)
        else:
            self.char_counter.setStyleSheet("""
                QLabel#prompt_char_counter {
                    color: #888888;
                    font-size: 11px;
                    padding: 2px 4px;
                }
            """)
    
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
        
        # Update character counter
        char_count = len(self._current_text)
        self.char_counter.setText(str(char_count))
