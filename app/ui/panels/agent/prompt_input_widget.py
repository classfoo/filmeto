"""Prompt input component for agent panel."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal, QEvent, QPropertyAnimation, QEasingCurve, QTimer, Property
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
        input_container_layout = QVBoxLayout(self.input_container)
        input_container_layout.setContentsMargins(2, 6, 2, 6)  # Left/right: 2px margin, top: 12px, bottom: 6px
        input_container_layout.setSpacing(6)  # Compact spacing between input and button
        
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
        self._min_height = self._line_height * 2  # 2 lines default
        self._max_height = self._line_height * 10  # 10 lines max
        self._current_height = self._min_height
        
        # Set size policy to allow height changes
        self.input_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_text.setMinimumHeight(self._min_height)
        self.input_text.setMaximumHeight(self._max_height)
        self.input_text.setFixedHeight(self._min_height)
        
        # Create a wrapper widget for height animation
        # We'll animate the input_text's height by animating minimumHeight
        # and synchronizing fixedHeight
        self._height_animation = QPropertyAnimation(self.input_text, b"minimumHeight")
        self._height_animation.setDuration(200)  # 200ms animation
        self._height_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Track animation state
        self._animating_to_height = None
        self._is_measuring = False  # Flag to prevent recursive calls
        
        # Debounce timer for height adjustment
        self._height_adjust_timer = QTimer()
        self._height_adjust_timer.setSingleShot(True)
        self._height_adjust_timer.timeout.connect(self._adjust_height)
        
        # Track if we're currently adjusting to prevent loops
        self._is_adjusting = False
        
        # Connect text changed signal - but don't adjust on initial setup
        self._initialized = False
        self.input_text.textChanged.connect(self._on_text_changed)
        
        # Mark as initialized after widget is fully laid out
        # Use a longer delay to ensure widget is ready
        QTimer.singleShot(300, lambda: setattr(self, '_initialized', True))
        
        input_container_layout.addWidget(self.input_text)
        
        # Button container - horizontal layout to align button to right
        button_container = QHBoxLayout()
        button_container.setContentsMargins(6, 0, 6, 0)
        button_container.addStretch()  # Push button to the right
        
        # Send button - icon button (24x24) below input
        icon_font = QFont("iconfont", 14)  # Font size for 24x24 button
        self.send_button = QPushButton("\ue83e", self.input_container)  # Play/send icon
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
        button_container.addWidget(self.send_button)
        
        input_container_layout.addLayout(button_container)
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
        """Get the number of lines in the text without modifying document state."""
        if self._is_measuring:
            return 2  # Return default to prevent recursion
        
        self._is_measuring = True
        
        try:
            text = self.input_text.toPlainText()
            
            # If empty, return 2 lines (default)
            if not text.strip():
                return 2
            
            # Get viewport width for wrapping calculation
            viewport_width = self.input_text.viewport().width()
            if viewport_width <= 0:
                # Widget not yet laid out, use a reasonable default
                return 2
            
            # Use document's current state to get accurate line count
            # Read-only access doesn't trigger layout updates
            doc = self.input_text.document()
            
            # Get current text width (may be -1 if not set, which is fine)
            current_text_width = doc.textWidth()
            
            # If text width is already set and matches viewport, use document height
            # This is the most accurate method when document is already laid out
            if current_text_width > 0 and abs(current_text_width - viewport_width) < 5:
                doc_height = doc.size().height()
                if doc_height > 0:
                    import math
                    line_count = math.ceil(doc_height / self._line_height)
                    return max(2, line_count)
            
            # Fallback: Use font metrics to estimate line count
            # This doesn't modify document state
            font_metrics = self.input_text.fontMetrics()
            lines = text.split('\n')
            
            total_lines = 0
            for line in lines:
                if not line.strip():
                    # Empty line counts as 1 line
                    total_lines += 1
                else:
                    # Calculate how many wrapped lines this line needs
                    line_width = font_metrics.horizontalAdvance(line)
                    if line_width <= 0:
                        total_lines += 1
                    else:
                        # Calculate wrapped lines: ceil(line_width / viewport_width)
                        # Add small margin for word wrapping
                        import math
                        wrapped_lines = math.ceil(line_width / max(viewport_width, 1))
                        total_lines += max(1, wrapped_lines)
            
            # Ensure minimum 2 lines
            return max(2, total_lines)
            
        except Exception as e:
            # Fallback to default on any error
            print(f"Error calculating line count: {e}")
            return 2
        finally:
            self._is_measuring = False
    
    def _on_text_changed(self):
        """Handle text change to adjust height."""
        # Don't adjust during initialization, measuring, or while already adjusting
        if not self._initialized or self._is_measuring or self._is_adjusting:
            return
        
        # Don't adjust if widget is not yet visible or laid out
        if not self.input_text.isVisible() or self.input_text.width() <= 0:
            return
        
        # Use debounce timer to avoid too frequent updates
        self._height_adjust_timer.stop()
        self._height_adjust_timer.start(100)  # 100ms debounce for stability
    
    def _adjust_height(self):
        """Adjust input height based on text line count."""
        # Prevent recursive calls and ensure widget is ready
        if self._is_measuring or not self._initialized or self._is_adjusting:
            return
        
        # Don't adjust if widget is not yet visible or laid out
        if not self.input_text.isVisible() or self.input_text.width() <= 0:
            return
        
        # Don't adjust if animation is running - let it finish first
        if self._height_animation.state() == QPropertyAnimation.State.Running:
            return
        
        # Set adjusting flag to prevent recursive calls
        self._is_adjusting = True
        
        try:
            line_count = self._get_text_line_count()
            
            # Clamp line count between 2 and 10
            clamped_lines = max(2, min(10, line_count))
            target_height = self._line_height * clamped_lines
            
            # Get current height
            current_height = self.input_text.height()
            if current_height <= 0:
                current_height = self._min_height
            
            # Only adjust if height actually changed significantly (threshold: 2px to avoid micro-adjustments)
            height_diff = abs(current_height - target_height)
            if height_diff < 2:
                self._is_adjusting = False
                return
            
            # If already animating to this height, skip
            if self._animating_to_height == target_height:
                self._is_adjusting = False
                return
            
            self._animating_to_height = target_height
            
            # Set up and start animation
            self._height_animation.setStartValue(int(current_height))
            self._height_animation.setEndValue(int(target_height))
            
            # Store callback reference for cleanup
            def on_animation_value_changed(value):
                height_value = max(1, int(value))  # Ensure positive value
                self.input_text.setFixedHeight(height_value)
            
            # Disconnect any previous handlers to avoid duplicates
            try:
                self._height_animation.valueChanged.disconnect()
            except:
                pass
            
            self._height_animation.valueChanged.connect(on_animation_value_changed)
            
            # Clean up after animation
            def on_animation_finished():
                final_height = int(target_height)
                self.input_text.setFixedHeight(final_height)
                self.input_text.setMinimumHeight(self._min_height)
                self.input_text.setMaximumHeight(self._max_height)
                self._current_height = final_height
                self._animating_to_height = None
                self._is_adjusting = False
                try:
                    self._height_animation.valueChanged.disconnect()
                except:
                    pass
            
            # Disconnect any previous finished handlers
            try:
                self._height_animation.finished.disconnect()
            except:
                pass
            
            self._height_animation.finished.connect(on_animation_finished, Qt.ConnectionType.SingleShotConnection)
            self._height_animation.start()
            
        except Exception as e:
            # Log error but don't crash
            print(f"Error in _adjust_height: {e}")
            import traceback
            traceback.print_exc()
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
        self.input_text.setPlainText(text)
    
    def clear(self):
        """Clear the input field."""
        self.input_text.clear()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the input widget."""
        self.input_text.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

