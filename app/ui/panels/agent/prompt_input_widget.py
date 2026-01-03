"""Prompt input component for agent panel."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QFrame, QSizePolicy, \
    QGridLayout, QWidget
from PySide6.QtCore import Qt, Signal, QEvent, QEasingCurve, QTimer, Property
from PySide6.QtGui import QKeyEvent, QFont, QCursor
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class AgentPromptInputWidget(BaseWidget):
    """Prompt input component for agent interactions."""
    
    # Signals
    message_submitted = Signal(str)  # Emitted when message is submitted
    
    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the prompt input widget."""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        self._setup_ui()
    
    def _setup_ui(self):
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
        layout.setContentsMargins(5, 5, 5, 5)  # Left/right/bottom: 5px, top: 12px
        layout.setSpacing(6)  # Compact spacing

        # Input container
        self.input_container = QFrame(self)
        self.input_container.setObjectName("agent_input_container")
        self.input_container.setStyleSheet("""
            QFrame#agent_input_container {
                background-color: #1e1f22;
                border: none;
                border-radius: 10px;
            }
        """)
        # Use a grid layout for better control over spacing
        input_container_layout = QGridLayout(self.input_container)
        input_container_layout.setContentsMargins(2, 6, 2, 6)  # Left/right: 2px margin, top: 12px, bottom: 6px
        input_container_layout.setSpacing(6)  # Fixed spacing between input and button

        # Text input field - dynamic height (2-10 lines)
        # Font size 13px, line height 1.4, single line ~18px
        self.input_text = QTextEdit(self.input_container)
        self.input_text.setObjectName("agent_input_text")
        self.input_text.setStyleSheet("""
            QTextEdit#agent_input_text {
                background-color: transparent;
                color: #e1e1e1;
                border: none;
                border-radius: 8px;
                padding: 0px;
                font-size: 13px;
                line-height: 1.4;
                selection-background-color: #4080ff;
            }
            QTextEdit#agent_input_text:focus {
                border: none;
            }
        """)
        self.input_text.setPlaceholderText(tr("输入消息..."))
        self.input_text.installEventFilter(self)

        # Set scrollbar policy: hide scrollbar when less than 10 lines
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

        # Debounce timer to prevent rapid height adjustments
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._adjust_height)

        # No animation for height transitions to ensure proper functionality
        # Animation will be handled differently if needed

        # Track if we're currently adjusting to prevent loops
        self._is_adjusting = False
        self._last_line_count = 1  # Start with 1 line for empty text
        self._first_change = True  # Flag to ignore the first text change (initialization)

        # Connect text changed signal
        self.input_text.textChanged.connect(self._on_text_changed)

        # Add input text to grid at row 0, column 0, spanning 1 row and 2 columns (to make space for button)
        input_container_layout.addWidget(self.input_text, 0, 0, 1, 2)

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
        self.send_button.setToolTip(tr("发送"))
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

        # Add button container to grid at row 1, column 1 (right side)
        input_container_layout.addWidget(button_widget, 1, 1)

        # Set stretch factors: row 0 (text area) expands, row 1 (button row) stays fixed
        input_container_layout.setRowStretch(0, 1)  # Text area gets all extra vertical space
        input_container_layout.setRowStretch(1, 0)  # Button row gets no extra space
        input_container_layout.setColumnStretch(0, 1)  # Column 0 (text area) expands horizontally
        input_container_layout.setColumnStretch(1, 0)  # Column 1 (button area) stays fixed

        layout.addWidget(self.input_container)
    
    def _calculate_line_height(self) -> int:
        """Calculate the height of a single line of text."""
        # Get font metrics
        font = self.input_text.font()
        font_metrics = self.input_text.fontMetrics()
        # Line height = font height * line-height factor (1.4)
        line_height = int(font_metrics.height() * 1.4)
        return max(line_height, 18)  # Minimum 18px
    
    def _get_text_line_count(self) -> int:
        """Get the number of lines in the text using document layout."""
        # Get the document
        doc = self.input_text.document()

        # Get the current viewport width to determine how text is wrapped
        viewport_width = self.input_text.viewport().width()
        if viewport_width <= 0:
            # If viewport isn't ready yet, use a reasonable default
            text = self.input_text.toPlainText()
            if not text.strip():
                return 1
            else:
                # Fallback: count actual newlines + 1
                return max(1, text.count('\n') + 1)

        # Temporarily set the text width to match the viewport width
        # This ensures the document layout is up-to-date
        original_text_width = doc.textWidth()
        doc.setTextWidth(viewport_width)

        # Force document layout update
        doc.adjustSize()

        # Get the document size after layout update
        doc_size = doc.size()
        doc_height = doc_size.height()

        # Calculate line count based on document height
        if doc_height > 0:
            import math
            line_count = math.ceil(doc_height / self._line_height)
            # Ensure minimum 1 line
            result = max(1, line_count)
        else:
            # If document height is 0, return 1 for empty text
            text = self.input_text.toPlainText()
            if not text.strip():
                result = 1
            else:
                # Fallback: count actual newlines + 1
                result = max(1, text.count('\n') + 1)

        # Restore original text width if it was set
        if original_text_width >= 0:
            doc.setTextWidth(original_text_width)
        else:
            # If original was not set, clear the width we set so it auto-adjusts
            doc.setTextWidth(-1)

        return result
    
    def _on_text_changed(self):
        """Handle text change with debouncing to prevent flickering."""
        # Handle the first change specially (initialization)
        if self._first_change:
            self._first_change = False
            # Update the initial line count to match the current state
            self._last_line_count = self._get_text_line_count()
            return

        # Use a short debounce timer to prevent rapid adjustments during typing
        self._debounce_timer.stop()
        self._debounce_timer.start(100)  # 100ms debounce
    
    def _adjust_height(self):
        """Adjust input height based on text line count."""
        # Prevent recursive calls
        if self._is_adjusting:
            return

        # Set adjusting flag to prevent recursive calls
        self._is_adjusting = True

        try:
            # Get the current line count
            line_count = self._get_text_line_count()

            # Clamp line count between 1 and 10
            clamped_lines = max(1, min(10, line_count))

            # Calculate target height
            target_height = self._line_height * clamped_lines

            # Only adjust if the line count actually changed
            if clamped_lines != self._last_line_count:
                # Update the last line count
                self._last_line_count = clamped_lines

                # Set the new height directly
                self.input_text.setMinimumHeight(target_height)
                self.input_text.setMaximumHeight(target_height)
                self.input_text.setFixedHeight(target_height)

        finally:
            # Always reset the adjusting flag
            self._is_adjusting = False
    
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
        # Store the current line count before changing text
        old_line_count = self._get_text_line_count()

        self.input_text.setPlainText(text)

        # Adjust height after text is set
        self._adjust_height()
    
    def clear(self):
        """Clear the input field."""
        self.input_text.clear()
        # Reset to minimum height
        self.input_text.setMinimumHeight(self._min_height)
        self.input_text.setMaximumHeight(self._min_height)
        self.input_text.setFixedHeight(self._min_height)
        self._last_line_count = 1
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the input widget."""
        self.input_text.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

