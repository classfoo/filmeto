"""Chat message widget for displaying individual messages in chat history."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt, QDateTime
from utils.i18n_utils import tr


class ChatMessageWidget(QWidget):
    """Widget for displaying a single chat message (user or AI)."""
    
    def __init__(self, message: str, is_user: bool = True, timestamp: QDateTime = None, parent=None):
        """
        Initialize chat message widget.
        
        Args:
            message: Message content
            is_user: True if message is from user, False if from AI
            timestamp: Optional timestamp for the message
            parent: Parent widget
        """
        super().__init__(parent)
        self._is_user = is_user
        self._message = message
        self._timestamp = timestamp or QDateTime.currentDateTime()
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Set up UI components."""
        # Main container layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(0)
        
        # Message container frame
        self.message_frame = QFrame()
        self.message_frame.setObjectName("chat_message_frame")
        # Set maximum width to 80% of parent (will be handled by layout)
        self.message_frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        
        frame_layout = QVBoxLayout(self.message_frame)
        frame_layout.setContentsMargins(12, 10, 12, 10)
        frame_layout.setSpacing(6)
        
        # Message content label
        self.content_label = QLabel(self._message)
        self.content_label.setObjectName("chat_message_content")
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.content_label.setOpenExternalLinks(True)
        
        # Timestamp label (small, subtle)
        time_str = self._timestamp.toString("hh:mm")
        self.timestamp_label = QLabel(time_str)
        self.timestamp_label.setObjectName("chat_message_timestamp")
        
        frame_layout.addWidget(self.content_label)
        frame_layout.addLayout(self._create_timestamp_layout())
        
        # Add frame to main layout with proper alignment
        if self._is_user:
            main_layout.addStretch()
            main_layout.addWidget(self.message_frame, 0, Qt.AlignRight)
        else:
            main_layout.addWidget(self.message_frame, 0, Qt.AlignLeft)
            main_layout.addStretch()
    
    def _create_timestamp_layout(self):
        """Create layout for timestamp."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(self.timestamp_label)
        return layout
    
    def _apply_style(self):
        """Apply styling based on message type."""
        if self._is_user:
            # User message: right-aligned, blue background
            self.message_frame.setStyleSheet("""
                QFrame#chat_message_frame {
                    background-color: #4080ff;
                    border: none;
                    border-radius: 12px;
                }
            """)
            # Set maximum width (80% of typical screen width, ~800px)
            self.message_frame.setMaximumWidth(640)
            self.content_label.setStyleSheet("""
                QLabel#chat_message_content {
                    color: #ffffff;
                    font-size: 14px;
                    line-height: 1.5;
                    background-color: transparent;
                }
            """)
            self.timestamp_label.setStyleSheet("""
                QLabel#chat_message_timestamp {
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 11px;
                    background-color: transparent;
                }
            """)
        else:
            # AI message: left-aligned, dark background
            self.message_frame.setStyleSheet("""
                QFrame#chat_message_frame {
                    background-color: #2b2d30;
                    border: 1px solid #3d3f4e;
                    border-radius: 12px;
                }
            """)
            # Set maximum width (80% of typical screen width, ~800px)
            self.message_frame.setMaximumWidth(640)
            self.content_label.setStyleSheet("""
                QLabel#chat_message_content {
                    color: #e1e1e1;
                    font-size: 14px;
                    line-height: 1.5;
                    background-color: transparent;
                }
            """)
            self.timestamp_label.setStyleSheet("""
                QLabel#chat_message_timestamp {
                    color: rgba(225, 225, 225, 0.5);
                    font-size: 11px;
                    background-color: transparent;
                }
            """)

