"""Chat history component for agent panel."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QIcon, QFont, QPen
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
    
    def _create_circular_icon(self, icon_char: str, size: int = 24, bg_color: QColor = None, icon_color: QColor = None, use_iconfont: bool = True) -> QIcon:
        """
        Create a circular icon with an icon actor.
        
        Args:
            icon_char: Icon actor (unicode string or letter)
            size: Icon size in pixels
            bg_color: Background color (default: #4080ff for user, #3d3f4e for agent)
            icon_color: Icon color (default: white)
            use_iconfont: Whether to use iconfont (True) or regular font (False)
            
        Returns:
            QIcon object
        """
        if bg_color is None:
            bg_color = QColor("#4080ff")
        if icon_color is None:
            icon_color = QColor("#ffffff")
        
        # Create pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        # Create painter
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circular background
        rect = QPainterPath()
        rect.addEllipse(0, 0, size, size)
        painter.fillPath(rect, bg_color)
        
        # Draw icon actor
        if use_iconfont:
            font = QFont("iconfont", size // 2)
        else:
            font = QFont()
            font.setPointSize(size // 2)
            font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(icon_color))
        painter.drawText(0, 0, size, size, Qt.AlignCenter, icon_char)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _get_sender_info(self, sender: str):
        """
        Get sender information including icon and alignment.
        
        Args:
            sender: Sender name
            
        Returns:
            Tuple of (is_user, icon_char, bg_color, alignment, use_iconfont)
        """
        # Check if sender is user (支持中文和英文)
        is_user = sender in [tr("用户"), "用户", "User", "user"]
        
        if is_user:
            # User icon: use iconfont user icon
            icon_char = "\ue6b3"  # user icon from iconfont
            bg_color = QColor("#35373a")  # Light gray background (slightly lighter than agent)
            alignment = Qt.AlignLeft  # Left align for consistency
            use_iconfont = True
        else:
            # Agent icon: use letter "A" with regular font
            icon_char = "A"  # Agent initial
            bg_color = QColor("#3d3f4e")  # Dark gray background
            alignment = Qt.AlignLeft
            use_iconfont = False
        
        return is_user, icon_char, bg_color, alignment, use_iconfont

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

        # Get sender information
        is_user, icon_char, bg_color, alignment, use_iconfont = self._get_sender_info(sender)

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

        # Sender row with icon and name
        sender_row = QWidget(message_widget)
        sender_row_layout = QHBoxLayout(sender_row)
        sender_row_layout.setContentsMargins(0, 0, 0, 0)
        sender_row_layout.setSpacing(6)
        
        # Create circular icon
        icon = self._create_circular_icon(icon_char, size=24, bg_color=bg_color, use_iconfont=use_iconfont)
        icon_label = QLabel(sender_row)
        icon_label.setPixmap(icon.pixmap(24, 24))
        icon_label.setFixedSize(24, 24)
        icon_label.setScaledContents(True)
        
        # Sender name label
        sender_label = QLabel(sender, sender_row)
        sender_label.setObjectName("chat_sender_label")
        sender_label.setStyleSheet("""
            QLabel#chat_sender_label {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 0px;
            }
        """)
        
        # Add icon and label based on alignment
        if is_user:
            # User: icon on right, name on right
            sender_row_layout.addStretch()
            sender_row_layout.addWidget(sender_label)
            sender_row_layout.addWidget(icon_label)
        else:
            # Agent: icon on left, name on left
            sender_row_layout.addWidget(icon_label)
            sender_row_layout.addWidget(sender_label)
            sender_row_layout.addStretch()
        
        message_layout.addWidget(sender_row)

        # Message content label
        content_label = QLabel(message, message_widget)
        content_label.setObjectName("chat_content_label")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        
        # Adjust content alignment and style based on sender
        if is_user:
            # User message: left aligned with slightly lighter gray background
            content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            content_label.setStyleSheet("""
                QLabel#chat_content_label {
                    color: #e1e1e1;
                    font-size: 13px;
                    padding: 8px;
                    background-color: #35373a;
                    border: 1px solid #505254;
                    border-radius: 5px;
                }
            """)
        else:
            # Agent message: left aligned with darker gray background
            content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
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
