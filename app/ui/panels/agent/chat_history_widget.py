"""Chat history component for agent panel."""

from PySide6.QtWidgets import QVBoxLayout, QScrollArea, QWidget, QLabel
from PySide6.QtCore import Qt
from app.ui.base_widget import BaseWidget
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class ChatHistoryWidget(BaseWidget):
    """Chat history component for displaying agent conversation messages."""

    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the chat history widget."""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        self.messages = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for chat messages
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #252525;
                border: 1px solid #505254;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                background-color: #2b2d30;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #505254;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #606264;
            }
        """)

        # Container widget for messages
        self.messages_container = QWidget()
        self.messages_container.setStyleSheet("""
            QWidget {
                background-color: #252525;
            }
        """)
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()  # Push messages to top

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

    def append_message(self, sender: str, message: str, message_id: str = None):
        """
        Append a message to the chat history.
        
        Args:
            sender: Sender name
            message: Message content
            message_id: Optional message ID for updating streaming messages
        """
        if not message:
            return

        # Create message widget
        message_widget = QWidget(self.messages_container)
        message_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        # Store message_id as property if provided
        if message_id:
            message_widget.setProperty("message_id", message_id)

        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(5)

        # Sender label
        sender_label = QLabel(sender, message_widget)
        sender_label.setObjectName("chat_sender_label")
        sender_label.setStyleSheet("""
            QLabel#chat_sender_label {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 0px;
            }
        """)
        message_layout.addWidget(sender_label)

        # Message content label
        content_label = QLabel(message, message_widget)
        content_label.setObjectName("chat_content_label")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        content_label.setStyleSheet("""
            QLabel#chat_content_label {
                color: #e1e1e1;
                font-size: 13px;
                padding: 8px;
                background-color: #2b2d30;
                border: 1px solid #505254;
                border-radius: 5px;
            }
        """)
        message_layout.addWidget(content_label)

        # Insert before the stretch spacer
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)
        self.messages.append(message_widget)

        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        
        return message_widget
    
    def update_last_message(self, message: str):
        """
        Update the content of the last message (for streaming).
        
        Args:
            message: New message content
        """
        if not self.messages:
            return
        
        last_widget = self.messages[-1]
        # Find the content label
        for child in last_widget.findChildren(QLabel):
            if child.objectName() == "chat_content_label":
                child.setText(message)
                break
        
        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
    
    def start_streaming_message(self, sender: str) -> str:
        """
        Start a new streaming message with empty content.
        
        Args:
            sender: Sender name
            
        Returns:
            Message ID for updating
        """
        import uuid
        message_id = str(uuid.uuid4())
        self.append_message(sender, "...", message_id)
        return message_id
    
    def update_streaming_message(self, message_id: str, content: str):
        """
        Update a streaming message by ID.
        
        Args:
            message_id: Message ID
            content: New content
        """
        for widget in self.messages:
            if widget.property("message_id") == message_id:
                # Find the content label
                for child in widget.findChildren(QLabel):
                    if child.objectName() == "chat_content_label":
                        child.setText(content)
                        break
                break
        
        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def clear(self):
        """Clear all messages from the chat history."""
        # Remove all message widgets
        while self.messages:
            message_widget = self.messages.pop()
            message_widget.setParent(None)
            message_widget.deleteLater()
