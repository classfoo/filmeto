"""Prompt input component for agent panel."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QLabel, QFrame, QSizePolicy, \
    QGridLayout, QWidget
from PySide6.QtCore import Qt, Signal, QEvent, QEasingCurve, QTimer, Property
from PySide6.QtGui import QKeyEvent, QFont, QCursor
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace
from app.ui.layout.flow_layout import FlowLayout
from utils.i18n_utils import tr
from .context_item_widget import ContextItemWidget


class AgentPromptInputWidget(BaseWidget):
    """Prompt input component for agent interactions."""
    
    # Signals
    message_submitted = Signal(str)  # Emitted when message is submitted
    add_context_requested = Signal()  # Emitted when add context button is clicked
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the prompt input widget."""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Set up the UI components."""
        # Set widget style - dark rounded theme
        self.setStyleSheet("""
            QWidget#agent_prompt_input_widget {
                background-color: #2b2d30;
                border-radius: 6px;
            }
        """)
        self.setObjectName("agent_prompt_input_widget")
        
        # Main layout - 5px margins on left, right, and bottom
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # Input container
        self.input_container = QFrame(self)
        self.input_container.setObjectName("agent_input_container")
        self.input_container.setStyleSheet("""
            QFrame#agent_input_container {
                background-color: #1e1f22;
                border: none;
                border-radius: 8px;
            }
        """)
        # Use a grid layout for better control over spacing
        input_container_layout = QGridLayout(self.input_container)
        input_container_layout.setContentsMargins(2, 2, 2, 2)
        input_container_layout.setSpacing(2)  # Fixed spacing between input and button

        # Initialize context UI components (above input)
        self._init_context_ui(input_container_layout)
        
        # Initialize input UI components
        self._init_input_ui(input_container_layout)
        
        # Initialize tool UI components
        self._init_tool_ui(input_container_layout)

        layout.addWidget(self.input_container)
    
    def _init_context_ui(self, input_container_layout):
        """Initialize the context UI components using context_item_widget."""
        # Create a container for context items with horizontal layout
        self.context_widget = QWidget(self.input_container)
        context_main_layout = QHBoxLayout(self.context_widget)
        context_main_layout.setContentsMargins(0, 0, 0, 0)
        context_main_layout.setSpacing(6)
        
        # Add button (16x16) on the left
        icon_font = QFont("iconfont", 14)  # Font size for 16x16 button
        self.add_context_button = QPushButton("\ue835", self.context_widget)  # Add icon
        self.add_context_button.setObjectName("add_context_button")
        self.add_context_button.setFont(icon_font)
        self.add_context_button.setFixedSize(24, 24)
        self.add_context_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_context_button.setToolTip(tr("Add context"))
        self.add_context_button.setStyleSheet("""
            QPushButton#add_context_button {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                color: #888888;
                font-size: 14px;
            }
            QPushButton#add_context_button:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #e1e1e1;
            }
            QPushButton#add_context_button:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.add_context_button.clicked.connect(self.add_context_requested.emit)
        context_main_layout.addWidget(self.add_context_button, 0)
        
        # Add placeholder text "add context" that appears when no context items exist
        self.context_placeholder = QLabel(tr("add context"), self.context_widget)
        self.context_placeholder.setObjectName("context_placeholder")
        self.context_placeholder.setStyleSheet("""
            QLabel#context_placeholder {
                color: #888888;
                font-size: 12px;
                background-color: transparent;
            }
        """)
        context_main_layout.addWidget(self.context_placeholder, 0)
        
        # Create a container widget for flow layout (context items)
        self.context_items_container = QWidget(self.context_widget)
        # Set size policy to allow vertical expansion
        self.context_items_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.context_layout = FlowLayout(self.context_items_container)
        self.context_layout.setContentsMargins(0, 0, 0, 0)
        self.context_layout.setSpacing(6)
        
        context_main_layout.addWidget(self.context_items_container, 1)
        
        # Initialize context items list
        self.context_items = []
        
        # Initially show the context widget and placeholder since there are no items
        self.context_widget.show()
        
        # Add context widget to the grid at row 0, spanning both columns
        # This places it above the input text
        input_container_layout.addWidget(self.context_widget, 0, 0, 1, 2)

    def _init_input_ui(self, input_container_layout):
        """Initialize the input UI components."""
        # Text input field - dynamic height (1-10 lines)
        # Font size 13px, line height 1.4, single line ~18px
        self.input_text = QPlainTextEdit(self.input_container)
        self.input_text.setObjectName("agent_input_text")
        self.input_text.setStyleSheet("""
            QPlainTextEdit#agent_input_text {
                background-color: transparent;
                color: #e1e1e1;
                border: none;
                border-radius: 4px;
                padding: 0px;
                font-size: 13px;
                line-height: 1.4;
                selection-background-color: #4080ff;
            }
            QPlainTextEdit#agent_input_text:focus {
                border: none;
            }
        """)
        self.input_text.setPlaceholderText(tr("输入消息..."))
        self.input_text.installEventFilter(self)

        # Set scrollbar policy: show scrollbar only when content exceeds 10 lines
        self.input_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Calculate single line height
        self._line_height = self._calculate_line_height()
        self._min_height = self._line_height * 1  # 1 line default
        self._max_height = self._line_height * 10  # 10 lines max

        # Set size policy to allow height changes
        self.input_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.input_text.setMinimumHeight(self._min_height)
        self.input_text.setMaximumHeight(self._max_height)
        self.input_text.setFixedHeight(self._min_height)

        # Connect document contents changed signal to adjust height automatically
        self.input_text.document().contentsChanged.connect(self._adjust_height_auto)

        # Add input text to grid at row 1, column 0, spanning 1 row and 2 columns (to make space for button)
        input_container_layout.addWidget(self.input_text, 1, 0, 1, 2)

    def _init_tool_ui(self, input_container_layout):
        """Initialize the tool UI components."""
        # Create a container for the button to position it properly
        button_widget = QWidget(self.input_container)
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)  # No margins for the button container
        button_layout.addStretch()  # Push button to the right

        # Send button - icon button (24x24) below input
        icon_font = QFont("iconfont", 14)  # Font size for 24x24 button
        self.send_button = QPushButton("\ue83e", button_widget)  # Play/send icon
        self.send_button.setObjectName("agent_send_button")
        self.send_button.setFont(icon_font)
        self.send_button.setFixedSize(24, 24)
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_button.setToolTip(tr("Send"))
        self.send_button.setStyleSheet("""
            QPushButton#agent_send_button {
                background-color: #3d3f4e;
                border: none;
                border-radius: 12px;
                color: #e1e1e1;
                font-size: 14px;
            }
            QPushButton#agent_send_button:hover {
                background-color: #4080ff;
            }
            QPushButton#agent_send_button:pressed {
                background-color: #3060cc;
            }
            QPushButton#agent_send_button:disabled {
                background-color: #3d3f42;
                color: #6d6f72;
            }
        """)
        self.send_button.clicked.connect(self._on_send_message)
        button_layout.addWidget(self.send_button)

        # Add button container to grid at row 2, column 1 (right side)
        input_container_layout.addWidget(button_widget, 2, 1)

        # Set stretch factors: row 0 (context), row 1 (text area) expands, row 2 (button row) stays fixed
        input_container_layout.setRowStretch(0, 0)  # Context row gets no extra space
        input_container_layout.setRowStretch(1, 1)  # Text area gets all extra vertical space
        input_container_layout.setRowStretch(2, 0)  # Button row gets no extra space
        input_container_layout.setColumnStretch(0, 1)  # Column 0 (text area) expands horizontally
        input_container_layout.setColumnStretch(1, 0)  # Column 1 (button area) stays fixed
    
    def _calculate_line_height(self) -> int:
        """Calculate the height of a single line of text."""
        # Get font metrics
        font_metrics = self.input_text.fontMetrics()
        # Calculate line height based on font height and line spacing
        # fontMetrics.lineSpacing() gives us the full line height including line spacing
        line_height = font_metrics.lineSpacing()
        return max(line_height, 18)  # Minimum 18px
    
    def _adjust_height_auto(self):
        """Automatically adjust input height based on content using QPlainTextEdit's built-in capabilities."""
        # Get the document
        doc = self.input_text.document()
        
        # Get the block count (number of lines)
        # QPlainTextEdit always has at least 1 block (even when empty)
        block_count = doc.blockCount()
        
        # Ensure at least 1 line for empty content
        if block_count == 0:
            block_count = 1
        
        # Clamp line count between 1 and 10
        clamped_lines = max(1, min(10, block_count))
        
        # Calculate target height based on clamped lines
        target_height = self._line_height * clamped_lines
        
        # Set the height
        self.input_text.setMinimumHeight(target_height)
        self.input_text.setMaximumHeight(target_height)
        self.input_text.setFixedHeight(target_height)
        
        # If content exceeds 10 lines, enable vertical scrollbar
        if block_count > 10:
            self.input_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.input_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def resizeEvent(self, event):
        """Handle widget resize to recalculate height."""
        super().resizeEvent(event)
        # Don't recalculate on resize - let text change events handle it
        # Resize events can cause infinite loops if we adjust height here
        pass
    
    def eventFilter(self, obj, event):
        """Handle keyboard events."""
        if obj == self.input_text and event.type() == QEvent.KeyPress:
            # Ctrl+Enter or Cmd+Enter to send message
            if isinstance(event, QKeyEvent):
                if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
                    modifiers = event.modifiers()
                    if modifiers & Qt.ControlModifier or modifiers & Qt.MetaModifier:
                        self._on_send_message()
                        return True
        
        return super().eventFilter(obj, event)
    
    def _on_send_message(self):
        """Handle send message button click."""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
        
        # Emit signal with message
        self.message_submitted.emit(message)
        
        # Clear input
        self.input_text.clear()
    
    def get_text(self) -> str:
        """Get the current input text."""
        return self.input_text.toPlainText()
    
    def set_text(self, text: str):
        """Set the input text."""
        self.input_text.setPlainText(text)
        # Height adjustment is handled automatically by _adjust_height_auto via contentsChanged signal
    
    def clear(self):
        """Clear the input field."""
        self.input_text.clear()
        # Height adjustment is handled automatically by _adjust_height_auto via contentsChanged signal
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the input widget."""
        self.input_text.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
    
    def add_context_item(self, context_id: str, context_name: str):
        """Add a context item to the context UI."""
        # Create a new context item widget
        context_item = ContextItemWidget(context_id, context_name, self.context_items_container)
        
        # Connect the removed signal to handle removal
        context_item.removed.connect(self._on_context_item_removed)
        
        # Add to the flow layout and internal list
        self.context_layout.addWidget(context_item)
        self.context_items.append(context_item)
        
        # Show the context widget if it was hidden
        self.context_widget.show()
        
        # Hide the placeholder when we have context items
        self.context_placeholder.hide()
        
        # Update the container size to ensure proper layout
        self.context_items_container.updateGeometry()
        self.context_items_container.update()
        # Force layout update
        self.context_layout.invalidate()
        self.context_layout.update()
    
    def remove_context_item(self, context_id: str):
        """Remove a context item by its ID."""
        for i, context_item in enumerate(self.context_items):
            if context_item.get_context_id() == context_id:
                # Remove from flow layout
                self.context_layout.removeWidget(context_item)
                
                # Remove from internal list
                self.context_items.pop(i)
                
                # Show the placeholder if no context items remain
                if len(self.context_items) == 0:
                    self.context_placeholder.show()
                
                # Always keep the context widget visible to show either context items or placeholder
                self.context_widget.show()
                
                # Delete the widget
                context_item.deleteLater()
                
                # Update the container size to ensure proper layout
                self.context_items_container.updateGeometry()
                self.context_items_container.update()
                # Force layout update
                self.context_layout.invalidate()
                self.context_layout.update()
                return True
        
        return False
    
    def clear_context_items(self):
        """Clear all context items."""
        for context_item in self.context_items:
            self.context_layout.removeWidget(context_item)
            context_item.deleteLater()
        
        self.context_items.clear()
        
        # Show the placeholder since no context items remain
        self.context_placeholder.show()
        
        # Still show the context widget to display the placeholder
        self.context_widget.show()
        
        # Update the container size to ensure proper layout
        self.context_items_container.updateGeometry()
        self.context_items_container.update()
        # Force layout update
        self.context_layout.invalidate()
        self.context_layout.update()
    
    def get_context_items(self):
        """Get all context item IDs."""
        return [item.get_context_id() for item in self.context_items]
    
    def _on_context_item_removed(self, context_id: str):
        """Handle when a context item is removed by the user."""
        self.remove_context_item(context_id)
