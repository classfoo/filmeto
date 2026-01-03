"""Prompt input component for agent panel."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt, Signal, QEvent
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
                border-radius: 12px;
            }
        """)
        self.setObjectName("agent_prompt_input_widget")
        
        # Main layout - compact, no margins on left, right, and bottom
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 0, 0)  # Top margin only, no left/right/bottom
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
        input_container_layout.setContentsMargins(12, 12, 12, 6)  # Compact padding
        input_container_layout.setSpacing(6)  # Compact spacing between input and button
        
        # Text input field
        self.input_text = QTextEdit(self.input_container)
        self.input_text.setObjectName("agent_input_text")
        self.input_text.setMinimumHeight(60)
        self.input_text.setMaximumHeight(120)
        self.input_text.setStyleSheet("""
            QTextEdit#agent_input_text {
                background-color: transparent;
                color: #e1e1e1;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                selection-background-color: #4080ff;
            }
            QTextEdit#agent_input_text:focus {
                border: none;
            }
        """)
        self.input_text.setPlaceholderText(tr("输入消息..."))
        self.input_text.installEventFilter(self)
        input_container_layout.addWidget(self.input_text)
        
        # Button container - horizontal layout to align button to right
        button_container = QHBoxLayout()
        button_container.setContentsMargins(0, 0, 0, 0)
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

