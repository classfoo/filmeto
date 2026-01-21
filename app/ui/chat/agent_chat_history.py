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

from agent.chat.agent_chat_message import AgentMessage
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr

# Lazy imports - defer heavy imports until first use
if TYPE_CHECKING:
    from app.data.workspace import Workspace
    from app.ui.chat.agent_chat_message_card import AgentMessageCard, UserMessageCard

class AgentChatHistoryWidget(BaseWidget):
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

        # Sub-agent metadata cache
        self._crew_member_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_crew_member_metadata()

        # Connect to project switched signal to refresh metadata when project changes
        if self.workspace:
            try:
                self.workspace.connect_project_switched(self._on_project_switched)
            except AttributeError:
                # In case the workspace doesn't have this method
                pass

        self._setup_ui()

    def refresh_crew_member_metadata(self):
        """Refresh crew member metadata when project changes."""
        self._load_crew_member_metadata()

    def _on_project_switched(self, project_name: str):
        """Handle project switched event."""
        print(f"Project switched to: {project_name}, refreshing crew member metadata")
        self.refresh_crew_member_metadata()

    def _load_crew_member_metadata(self):
        """Load crew member objects including color configurations."""
        try:
            # Import here to avoid circular imports
            from agent.crew.crew_service import CrewService

            # Get the current project
            project = self.workspace.get_project()
            if project:
                # Initialize crew member service
                crew_member_service = CrewService()

                # Load crew members for the project
                crew_members = crew_member_service.get_project_crew_members(project)

                # Convert to a dictionary using crew member names as keys for easy lookup
                self._crew_member_metadata = {}
                for name, crew_member in crew_members.items():
                    # Use the crew member's actual name as the key (normalized to lowercase)
                    self._crew_member_metadata[crew_member.config.name.lower()] = crew_member

                print(f"Loaded crew members for project: {len(self._crew_member_metadata)} agents")
            else:
                print("No project found, clearing crew member metadata")
                self._crew_member_metadata = {}
        except Exception as e:
            print(f"Error loading crew members: {e}")
            self._crew_member_metadata = {}

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
        layout.setContentsMargins(6, 6, 6, 6)  # Match agent_prompt_widget margins
        layout.setSpacing(0)

        # Scroll area for chat messages
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #252525;
                border: none;  /* Remove border to match agent_prompt_widget style */
                border-radius: 0px;  /* Remove border radius */
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
        self.messages_layout.setContentsMargins(5, 10, 5, 10)
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
        from app.ui.chat.agent_chat_message_card import AgentMessageCard, UserMessageCard
        from agent.chat.agent_chat_message import AgentMessage as ChatAgentMessage, MessageType

        is_user, icon_char, bg_color, alignment, use_iconfont = self._get_sender_info(sender)

        # Create appropriate card
        if is_user:
            card = UserMessageCard(message, self.messages_container)
        else:
            # Generate message_id if not provided
            if not message_id:
                import uuid
                message_id = str(uuid.uuid4())

            # Create an AgentMessage with the content
            agent_message = ChatAgentMessage(
                content=message,
                message_type=MessageType.TEXT,
                sender_id=sender,
                sender_name=sender,
                message_id=message_id
            )

            # Get the color and icon for this agent from metadata
            # Ensure metadata is loaded
            if not self._crew_member_metadata:
                self._load_crew_member_metadata()

            agent_color = "#4a90e2"  # Default color
            agent_icon = "🤖"  # Default icon

            # Normalize the sender to lowercase to match metadata keys
            normalized_sender = sender.lower()
            sender_crew_member = self._crew_member_metadata.get(normalized_sender)
            if sender_crew_member:
                agent_color = sender_crew_member.config.color
                agent_icon = sender_crew_member.config.icon
            else:
                # For user messages, we typically don't want to use sub-agent colors
                # But if sender happens to match a sub-agent name, we'll use that color
                print(f"Note: Sender '{normalized_sender}' not found in sub-agent metadata (this is normal for user messages)")
                agent_color = '#4a90e2'  # Default color
                agent_icon = '🤖'  # Default icon

            # Use the same crew member object for metadata
            crew_member_obj = sender_crew_member

            # Convert crew member object to metadata format
            if crew_member_obj:
                crew_member_data = {
                    'name': crew_member_obj.config.name,
                    'description': crew_member_obj.config.description,
                    'color': crew_member_obj.config.color,
                    'icon': crew_member_obj.config.icon,
                    'soul': crew_member_obj.config.soul,
                    'skills': crew_member_obj.config.skills,
                    'model': crew_member_obj.config.model,
                    'temperature': crew_member_obj.config.temperature,
                    'max_steps': crew_member_obj.config.max_steps,
                    'config_path': crew_member_obj.config.config_path,
                    'crew_title': crew_member_obj.config.metadata.get('crew_title', normalized_sender)
                }
            else:
                crew_member_data = {}

            card = AgentMessageCard(
                agent_message=agent_message,
                agent_color=agent_color,  # Pass the color to the card
                agent_icon=agent_icon,    # Pass the icon to the card
                crew_member_metadata=crew_member_data,  # Pass the crew member metadata
                parent=self.messages_container
            )

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
        from app.ui.chat.agent_chat_message_card import AgentMessageCard

        last_widget = self.messages[-1]
        if isinstance(last_widget, AgentMessageCard):
            # Update the content in the agent_message and refresh the display
            last_widget.agent_message.content = message
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
            # Update the content in the agent_message and refresh the display
            card.agent_message.content = content
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
        from app.ui.chat.agent_chat_message_card import UserMessageCard
        
        card = UserMessageCard(content, self.messages_container)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, card)
        self.messages.append(card)
        self._schedule_scroll()
        return card
    
    def get_or_create_agent_card(
        self,
        message_id: str,
        agent_name: str,
        title = None  # This parameter is kept for compatibility but not used
    ):
        """Get or create an agent message card."""
        if message_id in self._message_cards:
            return self._message_cards[message_id]

        # Lazy import when first needed
        from app.ui.chat.agent_chat_message_card import AgentMessageCard
        from agent.chat.agent_chat_message import AgentMessage as ChatAgentMessage, MessageType

        # Create an empty AgentMessage
        agent_message = ChatAgentMessage(
            content="",
            message_type=MessageType.TEXT,
            sender_id=agent_name,
            sender_name=agent_name,
            message_id=message_id
        )

        # Get the color and icon for this agent from metadata
        # Ensure metadata is loaded
        if not self._crew_member_metadata:
            self._load_crew_member_metadata()

        agent_color = "#4a90e2"  # Default color
        agent_icon = "🤖"  # Default icon

        # Normalize the agent_name to lowercase to match metadata keys
        normalized_agent_name = agent_name.lower()
        agent_crew_member = self._crew_member_metadata.get(normalized_agent_name)
        if agent_crew_member:
            agent_color = agent_crew_member.config.color
            agent_icon = agent_crew_member.config.icon
        else:
            print(f"Warning: No metadata found for agent {normalized_agent_name}, available: {list(self._crew_member_metadata.keys())}")
            agent_color = '#4a90e2'  # Default color
            agent_icon = '🤖'  # Default icon

        # Use the same crew member object for metadata
        crew_member_obj = agent_crew_member

        # Convert crew member object to metadata format
        if crew_member_obj:
            crew_member_data = {
                'name': crew_member_obj.config.name,
                'description': crew_member_obj.config.description,
                'color': crew_member_obj.config.color,
                'icon': crew_member_obj.config.icon,
                'soul': crew_member_obj.config.soul,
                'skills': crew_member_obj.config.skills,
                'model': crew_member_obj.config.model,
                'temperature': crew_member_obj.config.temperature,
                'max_steps': crew_member_obj.config.max_steps,
                'config_path': crew_member_obj.config.config_path,
                'crew_title': crew_member_obj.config.metadata.get('crew_title', normalized_agent_name)
            }
        else:
            crew_member_data = {}

        card = AgentMessageCard(
            agent_message=agent_message,
            agent_color=agent_color,  # Pass the color to the card
            agent_icon=agent_icon,    # Pass the icon to the card
            crew_member_metadata=crew_member_data,  # Pass the crew member metadata
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

        # For the new structure, we need to update the underlying agent message
        # and then update the card display
        if content is not None:
            if append and card.agent_message.content:
                card.agent_message.content += content
            else:
                card.agent_message.content = content

        # Update the card's display
        card.set_content(card.agent_message.content)

        # For now, we're not handling thinking state in the new structure
        # But we can add structured content if provided
        if structured_content:
            # Add the structured content to the card
            card.add_structure_content_widget(structured_content)

        if error:
            # Show error in content
            card.agent_message.content = f"❌ Error: {error}"
            card.set_content(card.agent_message.content)

        self._schedule_scroll()
    
    @Slot(object, object)
    def handle_stream_event(self, event, session):
        """Handle a streaming event from the agent system."""
        # Handle different types of events based on event_type
        if event.event_type == "error":
            # Handle error events - data contains content and session_id
            error_content = event.data.get('content', 'Unknown error occurred')

            # Create a message ID for the error
            import uuid
            message_id = str(uuid.uuid4())

            # Create or update the card with the error content
            card = self.get_or_create_agent_card(
                message_id,
                "System",  # Error messages come from the system
                "System"
            )

            # Update the card with the error content
            self.update_agent_card(
                message_id,
                content=error_content,
                append=False,  # Set as complete content
                error=error_content
            )
        elif event.event_type == "agent_response":
            # Handle agent response events - data comes from event.data
            content = event.data.get('content', '')
            sender_name = event.data.get('sender_name', 'Unknown')
            session_id = event.data.get('session_id', 'unknown')

            # Create a unique message ID for this response
            import uuid
            message_id = f"response_{session_id}_{uuid.uuid4()}"

            # Create or update the card with the content
            card = self.get_or_create_agent_card(
                message_id,
                sender_name,  # This will be normalized in get_or_create_agent_card
                sender_name
            )

            # Update the card with the content
            self.update_agent_card(
                message_id,
                content=content,
                append=False  # Set as complete content
            )
        elif event.event_type in ["skill_start", "skill_progress", "skill_end"]:
            # Handle skill events (start, progress, end)
            skill_name = event.data.get('skill_name', 'Unknown')
            sender_name = event.data.get('sender_name', 'Unknown')
            message_id = event.data.get('message_id', str(uuid.uuid4()))

            # Determine the status based on event type
            if event.event_type == "skill_start":
                status = "starting"
                message = f"Starting skill: {skill_name}"
                content = f"[Skill: {skill_name}] Starting execution..."
            elif event.event_type == "skill_progress":
                status = "in_progress"
                message = event.data.get('progress_text', 'Processing...')
                content = f"[Skill: {skill_name}] {message}"
            elif event.event_type == "skill_end":
                status = "completed"
                result = event.data.get('result', 'No result returned')
                message = result
                content = f"[Skill: {skill_name}] Completed. Result: {result}"
            else:
                status = "unknown"
                message = "Unknown skill status"
                content = f"[Skill: {skill_name}] {message}"

            # Get or create the card
            card = self.get_or_create_agent_card(
                message_id,
                sender_name,
                sender_name
            )

            # Create structured content for skill execution
            from agent.chat.agent_chat_message import StructureContent, ContentType
            skill_content = StructureContent(
                content_type=ContentType.SKILL,
                data={
                    "status": status,
                    "skill_name": skill_name,
                    "message": message
                },
                title=f"Skill: {skill_name}",
                description=f"Skill execution {status}"
            )

            # Update the card with the structured content
            self.update_agent_card(
                message_id,
                content=content,
                append=False,
                structured_content=skill_content
            )
        elif hasattr(event, 'content') and event.content:
            # Handle regular content events (fallback for other types)
            # Create or update the card with the content
            card = self._message_cards.get(event.message_id)
            if not card:
                agent_name = getattr(event, 'agent_name', 'Unknown')
                card = self.get_or_create_agent_card(
                    event.message_id,
                    agent_name,
                    getattr(event, 'title', None)
                )

            # Update the card with the content
            self.update_agent_card(
                event.message_id,
                content=event.content,
                append=True
            )
    
    def sync_from_session(self, session):
        """Synchronize display from a stream session."""
        # For now, we'll just iterate through messages and update the cards
        # This method may need to be adapted depending on the session structure
        pass

    def clear(self):
        """Clear all messages from the chat history."""
        while self.messages:
            message_widget = self.messages.pop()
            message_widget.setParent(None)
            message_widget.deleteLater()

        self._message_cards.clear()
        self._agent_current_cards.clear()
