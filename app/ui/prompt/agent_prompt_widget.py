"""Common agent prompt input widget with context management."""

from typing import TYPE_CHECKING
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QFrame, QSizePolicy, \
    QGridLayout, QWidget, QLabel
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QKeyEvent, QFont, QCursor
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace
from utils.i18n_utils import tr

# Lazy imports - defer until first use
if TYPE_CHECKING:
    from app.ui.layout.flow_layout import FlowLayout
    from app.ui.prompt.context_item_widget import ContextItemWidget


class AgentPromptWidget(BaseWidget):
    """
    Common agent prompt input widget with context management.

    This widget provides the full prompt input functionality used in agent panel,
    including context management. It can be used in both startup window and agent panel.
    """

    # Constants
    DEFAULT_INPUT_ROWS = 3  # Number of rows to show by default in the input area

    # Signals
    prompt_submitted = Signal(str)  # Emitted when prompt is submitted
    message_submitted = Signal(str)  # Alias for prompt_submitted
    add_context_requested = Signal()  # Emitted when add context button is clicked
    cancel_requested = Signal()  # Emitted when cancel button is clicked during conversation
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the prompt widget."""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)

        # Connect prompt_submitted to message_submitted for backward compatibility
        self.prompt_submitted.connect(self.message_submitted.emit)

        self._init_ui()
    
    def _init_ui(self):
        """Set up the UI components."""
        # Set widget style - dark rounded theme
        self.setStyleSheet("""
            QWidget#agent_prompt_widget {
                background-color: #2b2d30;
                border-radius: 6px;
                border: 1px solid transparent;
            }
        """)
        self.setObjectName("agent_prompt_widget")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # Input container
        self.input_container = QFrame(self)
        self.input_container.setObjectName("agent_input_container")
        self.input_container.setStyleSheet("""
            QFrame#agent_input_container {
                background-color: #1e1f22;
                border: 1px solid transparent;
                border-radius: 8px;
            }
            QFrame#agent_input_container[focused="true"] {
                border: 2px solid #4080ff;
            }
        """)
        # Use a grid layout for better control over spacing
        input_container_layout = QGridLayout(self.input_container)
        input_container_layout.setContentsMargins(4, 4, 4, 4)
        input_container_layout.setSpacing(5)

        # Initialize context UI components (above input)
        self._init_context_ui(input_container_layout)
        
        # Initialize input UI components
        self._init_input_ui(input_container_layout)

        # Initialize the send UI separately
        self._init_send_ui(input_container_layout)

        layout.addWidget(self.input_container)
    
    def _init_context_ui(self, input_container_layout):
        """Initialize the context UI components."""
        # Lazy import when first needed
        try:
            from app.ui.prompt.context_item_widget import ContextItemWidget
        except ImportError:
            ContextItemWidget = None
        
        if ContextItemWidget is None:
            # If context widget is not available, skip context UI
            return
        
        from app.ui.layout.flow_layout import FlowLayout
        
        # Create a container for context items with horizontal layout
        self.context_widget = QWidget(self.input_container)
        self.context_widget.setObjectName("agent_prompt_context_widget")
        self.context_widget.setStyleSheet("""
            QWidget#agent_prompt_context_widget {
                padding: 5px 5px 5px 5px;
            }
        """)
        context_main_layout = QHBoxLayout(self.context_widget)
        context_main_layout.setContentsMargins(0, 0, 0, 0)
        context_main_layout.setSpacing(6)
        
        # Add button (24x24) on the left
        icon_font = QFont("iconfont", 15)
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
                font-size: 15px;
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
                font-size: 15px;
                background-color: transparent;
            }
        """)
        context_main_layout.addWidget(self.context_placeholder, 0)
        
        # Create a container widget for flow layout (context items)
        self.context_items_container = QWidget(self.context_widget)
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
        input_container_layout.addWidget(self.context_widget, 0, 0, 1, 2)
    
    def _init_input_ui(self, input_container_layout):
        """Initialize the input UI components."""
        # Text input field - dynamic height (1-10 lines)
        self.input_text = QPlainTextEdit(self.input_container)
        self.input_text.setObjectName("agent_input_text")
        self.input_text.setStyleSheet("""
            QPlainTextEdit#agent_input_text {
                background-color: transparent;
                color: #e1e1e1;
                border: none;
                border-radius: 4px;
                margin: 0px 5px 0px 5px;
                font-size: 15px;
                selection-background-color: #4080ff;
            }
            QPlainTextEdit#agent_input_text:focus {
                border: none;
            }
        """)
        self.input_text.setPlaceholderText(tr("Input Prompts..."))
        # Install event filter to handle keyboard events in the input_text
        self.input_text.installEventFilter(self)

        # Set scrollbar policy
        self.input_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Calculate single line height
        self._line_height = self._calculate_line_height()
        self._min_height = self._line_height * self.DEFAULT_INPUT_ROWS  # Default rows defined as constant
        self._max_height = self._line_height * 10  # 10 lines max

        # Set size policy to allow height changes
        self.input_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.input_text.setMinimumHeight(self._min_height)
        self.input_text.setMaximumHeight(self._max_height)
        self.input_text.setFixedHeight(self._min_height)

        # Connect document contents changed signal to adjust height automatically
        self.input_text.document().contentsChanged.connect(self._adjust_height_auto)

        # Also override the focus events directly
        self.original_focusInEvent = self.input_text.focusInEvent
        self.original_focusOutEvent = self.input_text.focusOutEvent
        self.input_text.focusInEvent = self._input_focus_in_event
        self.input_text.focusOutEvent = self._input_focus_out_event

        # Initialize focused property
        self.setProperty('focused', False)

        # Determine row based on whether context UI exists
        input_row = 1 if hasattr(self, 'context_widget') and self.context_widget else 0

        # Add input text to grid
        input_container_layout.addWidget(self.input_text, input_row, 0, 1, 2)

        # Set stretch factors
        input_container_layout.setRowStretch(input_row, 1)  # Text area gets all extra vertical space
        input_container_layout.setColumnStretch(0, 1)  # Column 0 expands horizontally
        input_container_layout.setColumnStretch(1, 0)  # Column 1 stays fixed
    
    def _init_send_ui(self, input_container_layout):
        """Initialize the send UI components with agent dropdown and send button."""
        # Create a toolbar at the bottom of the input container
        self.send_toolbar = QFrame(self.input_container)
        self.send_toolbar.setObjectName("send_toolbar")
        self.send_toolbar.setStyleSheet("""
            QFrame#send_toolbar {
                border: none;
                background-color: transparent;
                padding: 5px 5px 5px 5px;
            }
        """)

        # Create horizontal layout for the toolbar
        toolbar_layout = QHBoxLayout(self.send_toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(6)

        # Agent dropdown on the left
        from PySide6.QtWidgets import QComboBox
        self.agent_dropdown = QComboBox(self.send_toolbar)
        self.agent_dropdown.setObjectName("agent_dropdown")
        self.agent_dropdown.setStyleSheet("""
            QComboBox#agent_dropdown {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 1px 6px;
                color: #e1e1e1;
                font-size: 12px;
                min-width: 10px;
                max-width: 150px;
            }
            QComboBox#agent_dropdown:hover {
                border: 1px solid #555555;
            }
            QComboBox#agent_dropdown:focus {
                border: 1px solid #4080ff;
            }
            QComboBox#agent_dropdown::drop-down {
                border: none;
                width: 15px;
            }
            QComboBox#agent_dropdown::down-arrow {
                image: url(noimg);
                width: 0px;
                border-left: 1px solid transparent;
                border-right: 1px solid transparent;
                border-top: 1px solid #888888;
            }
            QComboBox#agent_dropdown QAbstractItemView {
                background-color: #2b2d30;
                border: 1px solid #4a4a4a;
                color: #e1e1e1;
                selection-background-color: #4080ff;
                outline: none;
            }
        """)

        # Add some default options to the dropdown
        self.agent_dropdown.addItem(tr("Default Agent"), "default_agent")
        self.agent_dropdown.addItem(tr("Creative Agent"), "creative_agent")
        self.agent_dropdown.addItem(tr("Analytical Agent"), "analytical_agent")

        # Send button on the right
        icon_font = QFont("iconfont", 15)
        self.send_button = QPushButton("\ue83e", self.send_toolbar)  # Play/send icon
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
                font-size: 15px;
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
        self.send_button.clicked.connect(self._on_button_clicked)

        # Add widgets to the toolbar layout
        toolbar_layout.addWidget(self.agent_dropdown)
        toolbar_layout.addStretch()  # Add stretch to push send button to the right
        toolbar_layout.addWidget(self.send_button)

        # Add the toolbar to the input container's layout - at the bottom
        # Find the next available row in the grid layout
        next_row = input_container_layout.rowCount()
        input_container_layout.addWidget(self.send_toolbar, next_row, 0, 1, 2)  # Span both columns

    def _calculate_line_height(self) -> int:
        """Calculate the height of a single line of text."""
        font_metrics = self.input_text.fontMetrics()
        line_height = font_metrics.lineSpacing()
        return max(line_height, 21)  # Minimum 21px to accommodate 15pt font

    def _adjust_height_auto(self):
        """Automatically adjust input height based on content."""
        doc = self.input_text.document()
        block_count = doc.blockCount()

        if block_count == 0:
            block_count = 1

        # Clamp line count between 1 and 10
        clamped_lines = max(1, min(10, block_count))
        target_height = self._line_height * clamped_lines

        self.input_text.setMinimumHeight(target_height)
        self.input_text.setMaximumHeight(target_height)
        self.input_text.setFixedHeight(target_height)
    
    def _input_focus_in_event(self, event):
        """Handle focus in event for the input text."""
        self.set_focused_state(True)
        if self.original_focusInEvent:
            self.original_focusInEvent(event)

    def _input_focus_out_event(self, event):
        """Handle focus out event for the input text."""
        self.set_focused_state(False)
        if self.original_focusOutEvent:
            self.original_focusOutEvent(event)

    def set_focused_state(self, focused: bool):
        """Set the focused state and update the widget's style."""
        # Apply focused property to the input container instead of the main widget
        self.input_container.setProperty('focused', focused)
        self.input_container.style().unpolish(self.input_container)
        self.input_container.style().polish(self.input_container)
        self.input_container.update()

    def eventFilter(self, obj, event):
        """Handle keyboard events."""
        if obj == self.input_text and event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent):
                if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
                    modifiers = event.modifiers()
                    if not (modifiers & Qt.ShiftModifier):  # Enter sends message
                        self._on_button_clicked()
                        return True
                    else:  # Shift+Enter creates new line
                        cursor = self.input_text.textCursor()
                        cursor.insertText('\n')
                        return True
        
        return super().eventFilter(obj, event)
    
    def _on_button_clicked(self):
        """Handle button click - always send message."""
        # Send message regardless of any conversation state
        self._on_send_message()
    
    def _on_send_message(self):
        """Handle send message button click."""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
        
        # Emit signal with message
        self.prompt_submitted.emit(message)
        
        # Clear input
        self.input_text.clear()
    
    def get_text(self) -> str:
        """Get the current input text."""
        return self.input_text.toPlainText()
    
    def set_text(self, text: str):
        """Set the input text."""
        self.input_text.setPlainText(text)
        # Height adjustment is handled automatically by _adjust_height_auto
    
    def clear(self):
        """Clear the input field."""
        self.input_text.clear()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the input widget."""
        self.input_text.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
    
    def set_placeholder(self, text: str):
        """Set placeholder text."""
        self.input_text.setPlaceholderText(text)
    
    def set_conversation_active(self, active: bool):
        """Set the conversation active state and update button appearance."""
        # In group chat mode, we don't change the button state
        # The button always remains as a send button
        pass
    
    # Context management methods
    def add_context_item(self, context_id: str, context_name: str):
        """Add a context item to the context UI."""
        # Lazy import when first needed
        try:
            from app.ui.prompt.context_item_widget import ContextItemWidget
        except ImportError:
            ContextItemWidget = None
        
        if ContextItemWidget is None or not hasattr(self, 'context_items'):
            return
        
        # Create a new context item widget
        context_item = ContextItemWidget(context_id, context_name, self.context_items_container)
        
        # Connect the removed signal to handle removal
        context_item.removed.connect(self._on_context_item_removed)
        
        # Add to the flow layout and internal list
        self.context_layout.addWidget(context_item)
        self.context_items.append(context_item)
        
        # Show the context widget if it was hidden
        if hasattr(self, 'context_widget'):
            self.context_widget.show()
        
        # Hide the placeholder when we have context items
        if hasattr(self, 'context_placeholder'):
            self.context_placeholder.hide()
        
        # Update the container size to ensure proper layout
        self.context_items_container.updateGeometry()
        self.context_items_container.update()
        self.context_layout.invalidate()
        self.context_layout.update()
    
    def remove_context_item(self, context_id: str):
        """Remove a context item by its ID."""
        if not hasattr(self, 'context_items'):
            return False
        
        for i, context_item in enumerate(self.context_items):
            if context_item.get_context_id() == context_id:
                # Remove from flow layout
                self.context_layout.removeWidget(context_item)
                
                # Remove from internal list
                self.context_items.pop(i)
                
                # Show the placeholder if no context items remain
                if len(self.context_items) == 0 and hasattr(self, 'context_placeholder'):
                    self.context_placeholder.show()
                
                # Always keep the context widget visible
                if hasattr(self, 'context_widget'):
                    self.context_widget.show()
                
                # Delete the widget
                context_item.deleteLater()
                
                # Update the container size
                self.context_items_container.updateGeometry()
                self.context_items_container.update()
                self.context_layout.invalidate()
                self.context_layout.update()
                return True
        
        return False
    
    def clear_context_items(self):
        """Clear all context items."""
        if not hasattr(self, 'context_items'):
            return
        
        for context_item in self.context_items:
            self.context_layout.removeWidget(context_item)
            context_item.deleteLater()
        
        self.context_items.clear()
        
        # Show the placeholder since no context items remain
        if hasattr(self, 'context_placeholder'):
            self.context_placeholder.show()
        
        # Still show the context widget to display the placeholder
        if hasattr(self, 'context_widget'):
            self.context_widget.show()
        
        # Update the container size
        self.context_items_container.updateGeometry()
        self.context_items_container.update()
        self.context_layout.invalidate()
        self.context_layout.update()
    
    def get_context_items(self):
        """Get all context item IDs."""
        if not hasattr(self, 'context_items'):
            return []
        return [item.get_context_id() for item in self.context_items]
    
    def _on_context_item_removed(self, context_id: str):
        """Handle when a context item is removed by the user."""
        self.remove_context_item(context_id)
