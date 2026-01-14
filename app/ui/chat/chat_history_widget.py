"""Chat history component for agent panel with multi-agent support.

This module provides a group-chat style presentation for multi-agent conversations,
with support for streaming content, structured data, and concurrent agent execution.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QIcon, QFont, QPen

from agent.filmeto_agent import AgentRole
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr

# Lazy imports - defer heavy imports until first use
if TYPE_CHECKING:
    from app.data.workspace import Workspace
    from app.ui.chat.agent_message_card import AgentMessageCard, UserMessageCard

class ChatHistoryWidget(BaseWidget):
    """Chat history component for displaying multi-agent conversation messages.
    
    Features:
    - Group-chat style presentation with multiple agent cards
    - Streaming content updates per agent
    - Structured content display (plans, tasks, media, references)
    - Concurrent agent execution visualization
    - Dynamic card updates during streaming
    """
    
    # Signals
    reference_clicked = Signal(str, str)  # ref_type, ref_id
    message_complete = Signal(str, str)  # message_id, agent_name
    
    def __init__(self, workspace: 'Workspace', parent=None):
        """Initialize the chat history widget."""
        super().__init__(workspace)
        if parent:
            self.setParent(parent)
        
        # Message tracking
        self.messages: List[QWidget] = []  # All message widgets
        self._message_cards: Dict[str, AgentMessageCard] = {}  # message_id -> card
        self._agent_current_cards: Dict[str, str] = {}  # agent_name -> current message_id
        self._scroll_timer = QTimer()
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._scroll_to_bottom)
        
        self._setup_ui()
    
    def _create_circular_icon(
        self,
        icon_char: str,
        size: int = 24,
        bg_color: QColor = None,
        icon_color: QColor = None,
        use_iconfont: bool = True
    ) -> QIcon:
        """Create a circular icon with an icon character."""
        if bg_color is None:
            bg_color = QColor("#4080ff")
        if icon_color is None:
            icon_color = QColor("#ffffff")
        
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QPainterPath()
        rect.addEllipse(0, 0, size, size)
        painter.fillPath(rect, bg_color)
        
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
        """Get sender information including icon and alignment."""
        is_user = sender in [tr("用户"), "用户", "User", "user"]
        
        if is_user:
            icon_char = "\ue6b3"
            bg_color = QColor("#35373a")
            alignment = Qt.AlignLeft
            use_iconfont = True
        else:
            icon_char = "A"
            bg_color = QColor("#3d3f4e")
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
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)
    
    def _scroll_to_bottom(self):
        """Scroll to bottom of chat."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _schedule_scroll(self):
        """Schedule a scroll to bottom (debounced)."""
        self._scroll_timer.start(50)  # 50ms debounce
    
    # ========================================================================
    # Legacy API (for backward compatibility)
    # ========================================================================
    
    def append_message(self, sender: str, message: str, message_id: str = None) -> QWidget:
        """Append a message to the chat history (legacy API)."""
        if not message:
            return None

        # Lazy import when first needed
        from app.ui.chat.agent_message_card import AgentMessageCard, UserMessageCard

        is_user, icon_char, bg_color, alignment, use_iconfont = self._get_sender_info(sender)

        # Create appropriate card
        if is_user:
            card = UserMessageCard(message, self.messages_container)
        else:
            # For legacy API, use agent role based on sender name
            agent_role = AgentRole.from_agent_name(sender)
            if sender.lower() in ["agent", tr("Agent").lower()]:
                agent_role = AgentRole.COORDINATOR
            
            # Generate message_id if not provided
            if not message_id:
                import uuid
                message_id = str(uuid.uuid4())
            
            card = AgentMessageCard(
                message_id=message_id,
                agent_name=sender,
                agent_role=agent_role,
                parent=self.messages_container
            )
            card.set_content(message)
            
            self._message_cards[message_id] = card

        # Insert before the stretch spacer
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, card)
        self.messages.append(card)

        self._schedule_scroll()
        
        return card
    
    def update_last_message(self, message: str):
        """Update the content of the last message (legacy API)."""
        if not self.messages:
            return
        
        # Lazy import when first needed
        from app.ui.chat.agent_message_card import AgentMessageCard
        
        last_widget = self.messages[-1]
        if isinstance(last_widget, AgentMessageCard):
            last_widget.set_content(message)
        else:
            # Old style widget
            for child in last_widget.findChildren(QLabel):
                if child.objectName() == "chat_content_label":
                    child.setText(message)
                    break
        
        self._schedule_scroll()
    
    def start_streaming_message(self, sender: str) -> str:
        """Start a new streaming message (legacy API)."""
        import uuid
        message_id = str(uuid.uuid4())
        self.append_message(sender, "...", message_id)
        return message_id
    
    def update_streaming_message(self, message_id: str, content: str):
        """Update a streaming message by ID (legacy API)."""
        card = self._message_cards.get(message_id)
        if card:
            card.set_content(content)
        else:
            # Fallback to old method
            for widget in self.messages:
                if hasattr(widget, 'property') and widget.property("message_id") == message_id:
                    for child in widget.findChildren(QLabel):
                        if child.objectName() == "chat_content_label":
                            child.setText(content)
                            break
                    break
        
        self._schedule_scroll()
    
    # ========================================================================
    # Multi-Agent Streaming API
    # ========================================================================
    
    def add_user_message(self, content: str):
        """Add a user message card."""
        # Lazy import when first needed
        from app.ui.chat.agent_message_card import UserMessageCard
        
        card = UserMessageCard(content, self.messages_container)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, card)
        self.messages.append(card)
        self._schedule_scroll()
        return card
    
    def get_or_create_agent_card(
        self,
        message_id: str,
        agent_name: str,
        agent_role = None
    ):
        """Get or create an agent message card."""
        if message_id in self._message_cards:
            return self._message_cards[message_id]
        
        # Lazy import when first needed
        from app.ui.chat.agent_message_card import AgentMessageCard
        from agent.streaming.protocol import AgentRole
        
        # Create new card
        if agent_role is None:
            agent_role = AgentRole.from_agent_name(agent_name)
        
        card = AgentMessageCard(
            message_id=message_id,
            agent_name=agent_name,
            agent_role=agent_role,
            parent=self.messages_container
        )
        
        # Connect signals
        card.reference_clicked.connect(self.reference_clicked.emit)
        
        # Add to layout
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, card)
        self.messages.append(card)
        self._message_cards[message_id] = card
        self._agent_current_cards[agent_name] = message_id
        
        self._schedule_scroll()
        return card
    
    def get_agent_current_card(self, agent_name: str):
        """Get the current active card for an agent."""
        message_id = self._agent_current_cards.get(agent_name)
        if message_id:
            return self._message_cards.get(message_id)
        return None
    
    def update_agent_card(
        self,
        message_id: str,
        content: str = None,
        append: bool = True,
        is_thinking: bool = False,
        thinking_text: str = "",
        is_complete: bool = False,
        structured_content = None,
        error: str = None
    ):
        """Update an agent message card."""
        card = self._message_cards.get(message_id)
        if not card:
            return
        
        if content is not None:
            if append:
                card.append_content(content)
            else:
                card.set_content(content)
        
        if is_thinking:
            card.set_thinking(True, thinking_text)
        elif is_complete or content is not None:
            card.set_thinking(False)
        
        if is_complete:
            card.set_complete(True)
        
        if structured_content:
            card.add_structured_content(structured_content)
        
        if error:
            card.set_error(error)
        
        self._schedule_scroll()
    
    @Slot(object, object)
    def handle_stream_event(self, event, session):
        """Handle a streaming event from the agent system."""
        # Lazy import when first needed
        from agent.streaming.protocol import StreamEventType, AgentRole, ThinkingContent
        
        event_type = event.event_type
        
        # Skip user-initiated events
        if event.agent_role == AgentRole.USER:
            return
        
        # Handle different event types
        if event_type == StreamEventType.AGENT_START:
            # Create or get card for this agent
            self.get_or_create_agent_card(
                event.message_id,
                event.agent_name,
                event.agent_role
            )
            self.update_agent_card(
                event.message_id,
                is_thinking=True
            )
            
        elif event_type == StreamEventType.AGENT_THINKING:
            card = self._message_cards.get(event.message_id)
            if not card:
                card = self.get_or_create_agent_card(
                    event.message_id,
                    event.agent_name,
                    event.agent_role
                )
            
            thinking_text = ""
            if event.structured_content and isinstance(event.structured_content, ThinkingContent):
                thinking_text = event.structured_content.data.get("thinking_text", "")
            
            self.update_agent_card(
                event.message_id,
                is_thinking=True,
                thinking_text=thinking_text
            )
            
        elif event_type == StreamEventType.AGENT_CONTENT:
            card = self._message_cards.get(event.message_id)
            if not card:
                card = self.get_or_create_agent_card(
                    event.message_id,
                    event.agent_name,
                    event.agent_role
                )
            
            append = event.metadata.get("append", True)
            self.update_agent_card(
                event.message_id,
                content=event.content,
                append=append,
                structured_content=event.structured_content
            )
            
        elif event_type == StreamEventType.CONTENT_TOKEN:
            card = self._message_cards.get(event.message_id)
            if not card:
                card = self.get_or_create_agent_card(
                    event.message_id,
                    event.agent_name,
                    event.agent_role
                )
            
            self.update_agent_card(
                event.message_id,
                content=event.content,
                append=True
            )
            
        elif event_type == StreamEventType.AGENT_COMPLETE:
            self.update_agent_card(
                event.message_id,
                is_complete=True,
                content=event.content if event.content else None,
                append=False
            )
            self.message_complete.emit(event.message_id, event.agent_name)
            
        elif event_type == StreamEventType.AGENT_ERROR:
            self.update_agent_card(
                event.message_id,
                error=event.content,
                is_complete=True
            )
            
        elif event_type == StreamEventType.PLAN_CREATED:
            card = self._message_cards.get(event.message_id)
            if not card:
                card = self.get_or_create_agent_card(
                    event.message_id,
                    event.agent_name or "Planner",
                    AgentRole.PLANNER
                )
            
            if event.structured_content:
                self.update_agent_card(
                    event.message_id,
                    structured_content=event.structured_content
                )
            
        elif event_type == StreamEventType.PLAN_TASK_START:
            card = self._message_cards.get(event.message_id)
            if not card:
                card = self.get_or_create_agent_card(
                    event.message_id,
                    event.agent_name,
                    event.agent_role
                )
            
            if event.structured_content:
                self.update_agent_card(
                    event.message_id,
                    is_thinking=True,
                    structured_content=event.structured_content
                )
            
        elif event_type == StreamEventType.PLAN_TASK_COMPLETE:
            if event.structured_content:
                self.update_agent_card(
                    event.message_id,
                    structured_content=event.structured_content,
                    is_complete=True
                )
            
        elif event_type == StreamEventType.CONTENT_MEDIA:
            if event.structured_content:
                self.update_agent_card(
                    event.message_id,
                    structured_content=event.structured_content
                )
            
        elif event_type == StreamEventType.CONTENT_REFERENCE:
            if event.structured_content:
                self.update_agent_card(
                    event.message_id,
                    structured_content=event.structured_content
                )
    
    def sync_from_session(self, session):
        """Synchronize display from a stream session."""
        for message in session.get_all_messages():
            card = self._message_cards.get(message.message_id)
            if not card:
                card = self.get_or_create_agent_card(
                    message.message_id,
                    message.agent_name,
                    message.agent_role
                )
            
            # Update content
            card.set_content(message.content)
            
            # Update thinking state
            if message.is_thinking:
                card.set_thinking(True, message.thinking_content)
            else:
                card.set_thinking(False)
            
            # Update completion state
            if message.is_complete:
                card.set_complete(True)
            
            # Update error
            if message.error:
                card.set_error(message.error)
            
            # Add structured contents
            card.clear_structured_content()
            for structured in message.structured_contents:
                card.add_structured_content(structured)
        
        self._schedule_scroll()

    def clear(self):
        """Clear all messages from the chat history."""
        while self.messages:
            message_widget = self.messages.pop()
            message_widget.setParent(None)
            message_widget.deleteLater()
        
        self._message_cards.clear()
        self._agent_current_cards.clear()
