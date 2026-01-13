"""Conversation management for agent interactions."""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from utils.yaml_utils import load_yaml, save_yaml

# Import LangChain message types only when needed to avoid circular dependencies
def _get_langchain_types():
    try:
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
        return HumanMessage, AIMessage, SystemMessage, ToolMessage
    except ImportError:
        raise ImportError("langchain-core is required for LangChain message conversion. Please install it.")

logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        data = {
            'role': self.role.value if isinstance(self.role, MessageRole) else self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }
        if self.metadata:
            data['metadata'] = self.metadata
        if self.tool_calls:
            data['tool_calls'] = self.tool_calls
        if self.tool_call_id:
            data['tool_call_id'] = self.tool_call_id
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        role = data['role']
        if isinstance(role, str):
            role = MessageRole(role)
        return cls(
            role=role,
            content=data['content'],
            timestamp=data['timestamp'],
            metadata=data.get('metadata'),
            tool_calls=data.get('tool_calls'),
            tool_call_id=data.get('tool_call_id')
        )


@dataclass
class Conversation:
    """Represents a conversation thread."""
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            'conversation_id': self.conversation_id,
            'title': self.title,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'messages': [msg.to_dict() for msg in self.messages],
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create conversation from dictionary."""
        messages = [Message.from_dict(msg) for msg in data.get('messages', [])]
        return cls(
            conversation_id=data['conversation_id'],
            title=data['title'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            messages=messages,
            metadata=data.get('metadata')
        )
    
    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
    
    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """Get messages in LLM format (OpenAI-compatible)."""
        return [
            {
                'role': msg.role.value if isinstance(msg.role, MessageRole) else msg.role,
                'content': msg.content
            }
            for msg in self.messages
        ]

    def get_langchain_messages(self) -> List[Any]:
        """Convert messages to LangChain format, handling tool call/response mismatches.

        This method ensures that assistant messages with tool_calls are properly paired
        with corresponding tool messages, avoiding the LangChain error:
        'An assistant message with "tool_calls" must be followed by tool messages...'
        """
        HumanMessage, AIMessage, SystemMessage, ToolMessage = _get_langchain_types()

        langchain_messages = []
        i = 0

        while i < len(self.messages):
            msg = self.messages[i]

            if msg.role == MessageRole.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                if msg.tool_calls:
                    # Check if the next message is a corresponding tool message
                    has_corresponding_tool_msg = (
                        i + 1 < len(self.messages) and
                        self.messages[i + 1].role == MessageRole.TOOL and
                        self.messages[i + 1].tool_call_id in [tc.get('id') for tc in msg.tool_calls]
                    )

                    if has_corresponding_tool_msg:
                        # Add the assistant message with tool calls
                        langchain_messages.append(AIMessage(content=msg.content, tool_calls=msg.tool_calls))
                    else:
                        # Skip this assistant message with unpaired tool calls to prevent LangChain error
                        logger.warning(
                            f"Skipping assistant message with tool_calls that has no corresponding tool response. "
                            f"Message content: {msg.content[:50]}..."
                        )
                else:
                    # Regular assistant message without tool calls
                    langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM:
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == MessageRole.TOOL:
                # Only add tool message if it has a corresponding tool_call_id
                if msg.tool_call_id:
                    langchain_messages.append(ToolMessage(content=msg.content, tool_call_id=msg.tool_call_id))
                else:
                    logger.warning(f"Skipping tool message without tool_call_id: {msg.content[:50]}...")

            i += 1

        return langchain_messages


class ConversationManager:
    """Manages conversations for a project."""
    
    def __init__(self, project_path: str):
        """
        Initialize conversation manager.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = project_path
        self.agent_path = os.path.join(project_path, "agent")
        self.conversations_path = os.path.join(self.agent_path, "conversations")
        
        # Create directories if they don't exist
        os.makedirs(self.conversations_path, exist_ok=True)
        
        # Load or create index
        self.index_path = os.path.join(self.agent_path, "conversations_index.yaml")
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load conversations index."""
        if os.path.exists(self.index_path):
            return load_yaml(self.index_path) or {'conversations': []}
        return {'conversations': []}
    
    def _save_index(self):
        """Save conversations index."""
        save_yaml(self.index_path, self.index)
    
    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            title: Optional title for the conversation
            
        Returns:
            New Conversation object
        """
        timestamp = datetime.now().isoformat()
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        conversation = Conversation(
            conversation_id=conversation_id,
            title=title or f"Conversation {len(self.index['conversations']) + 1}",
            created_at=timestamp,
            updated_at=timestamp,
            messages=[],
            metadata={}
        )
        
        # Add to index
        self.index['conversations'].append({
            'conversation_id': conversation_id,
            'title': conversation.title,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at
        })
        self._save_index()
        
        # Save conversation
        self._save_conversation(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation object or None if not found
        """
        conversation_file = os.path.join(self.conversations_path, f"{conversation_id}.json")
        if not os.path.exists(conversation_file):
            return None
        
        with open(conversation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Conversation.from_dict(data)
    
    def save_conversation(self, conversation: Conversation):
        """
        Save a conversation.
        
        Args:
            conversation: Conversation object to save
        """
        self._save_conversation(conversation)
        
        # Update index
        for conv_info in self.index['conversations']:
            if conv_info['conversation_id'] == conversation.conversation_id:
                conv_info['title'] = conversation.title
                conv_info['updated_at'] = conversation.updated_at
                break
        self._save_index()
    
    def _save_conversation(self, conversation: Conversation):
        """Internal method to save conversation to file."""
        conversation_file = os.path.join(self.conversations_path, f"{conversation.conversation_id}.json")
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversations.
        
        Returns:
            List of conversation metadata (id, title, timestamps)
        """
        return sorted(
            self.index['conversations'],
            key=lambda x: x['updated_at'],
            reverse=True
        )
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        conversation_file = os.path.join(self.conversations_path, f"{conversation_id}.json")
        if not os.path.exists(conversation_file):
            return False
        
        # Remove file
        os.remove(conversation_file)
        
        # Remove from index
        self.index['conversations'] = [
            conv for conv in self.index['conversations']
            if conv['conversation_id'] != conversation_id
        ]
        self._save_index()
        
        return True
    
    def add_message(self, conversation_id: str, message: Message) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            message: Message to add
            
        Returns:
            True if successful, False if conversation not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.add_message(message)
        self.save_conversation(conversation)
        return True
    
    def get_or_create_default_conversation(self) -> Conversation:
        """
        Get the most recent conversation or create a new one if none exist.
        
        Returns:
            Conversation object
        """
        conversations = self.list_conversations()
        if conversations:
            # Return most recent conversation
            return self.get_conversation(conversations[0]['conversation_id'])
        else:
            # Create new conversation
            return self.create_conversation(title="New Conversation")

