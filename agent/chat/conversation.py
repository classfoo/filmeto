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

    def get_messages_as_dicts(self) -> List[Dict[str, Any]]:
        """Get messages as dictionaries with all properties."""
        return [msg.to_dict() for msg in self.messages]

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
    """Manages conversations for projects. Singleton implementation with lazy loading and project-agnostic methods."""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize conversation manager.
        Methods now accept project_path parameter to operate on specific projects.
        """
        if self._initialized:
            return

        self._initialized = True

    def _get_paths_for_project(self, project_path: str) -> tuple:
        """
        Get all necessary paths for a specific project.

        Args:
            project_path: Path to the project directory

        Returns:
            Tuple of (agent_path, conversations_path, index_path)
        """
        agent_path = os.path.join(project_path, "agent")
        conversations_path = os.path.join(agent_path, "chats")  # Updated to use "chats" directory
        index_path = os.path.join(agent_path, "conversations_index.yml")

        # Create directories if they don't exist
        os.makedirs(conversations_path, exist_ok=True)

        return agent_path, conversations_path, index_path

    def _load_index(self, project_path: str) -> Dict[str, Any]:
        """
        Load conversations index for a specific project.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary containing the conversation index
        """
        _, _, index_path = self._get_paths_for_project(project_path)
        if os.path.exists(index_path):
            return load_yaml(index_path) or {'conversations': []}
        return {'conversations': []}

    def _save_index(self, project_path: str, index: Dict[str, Any]):
        """
        Save conversations index for a specific project.

        Args:
            project_path: Path to the project directory
            index: Index data to save
        """
        _, _, index_path = self._get_paths_for_project(project_path)
        save_yaml(index_path, index)

    def create_conversation(self, project_path: str, title: Optional[str] = None) -> Conversation:
        """
        Create a new conversation.

        Args:
            project_path: Path to the project directory
            title: Optional title for the conversation

        Returns:
            New Conversation object
        """
        timestamp = datetime.now().isoformat()
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Load current index
        index = self._load_index(project_path)

        conversation = Conversation(
            conversation_id=conversation_id,
            title=title or f"Conversation {len(index['conversations']) + 1}",
            created_at=timestamp,
            updated_at=timestamp,
            messages=[],
            metadata={}
        )

        # Add to index
        index['conversations'].append({
            'conversation_id': conversation_id,
            'title': conversation.title,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at
        })
        self._save_index(project_path, index)

        # Save conversation
        self._save_conversation(project_path, conversation)

        return conversation

    def get_conversation(self, project_path: str, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            project_path: Path to the project directory
            conversation_id: Conversation ID

        Returns:
            Conversation object or None if not found
        """
        _, conversations_path, _ = self._get_paths_for_project(project_path)
        conversation_file = os.path.join(conversations_path, f"{conversation_id}.json")
        if not os.path.exists(conversation_file):
            return None

        with open(conversation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return Conversation.from_dict(data)

    def save_conversation(self, project_path: str, conversation: Conversation):
        """
        Save a conversation.

        Args:
            project_path: Path to the project directory
            conversation: Conversation object to save
        """
        self._save_conversation(project_path, conversation)

        # Update index
        index = self._load_index(project_path)
        for conv_info in index['conversations']:
            if conv_info['conversation_id'] == conversation.conversation_id:
                conv_info['title'] = conversation.title
                conv_info['updated_at'] = conversation.updated_at
                break
        self._save_index(project_path, index)

    def _save_conversation(self, project_path: str, conversation: Conversation):
        """Internal method to save conversation to file."""
        _, conversations_path, _ = self._get_paths_for_project(project_path)
        conversation_file = os.path.join(conversations_path, f"{conversation.conversation_id}.json")
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)

    def list_conversations(self, project_path: str) -> List[Dict[str, Any]]:
        """
        List all conversations.

        Args:
            project_path: Path to the project directory

        Returns:
            List of conversation metadata (id, title, timestamps)
        """
        index = self._load_index(project_path)
        return sorted(
            index['conversations'],
            key=lambda x: x['updated_at'],
            reverse=True
        )

    def delete_conversation(self, project_path: str, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            project_path: Path to the project directory
            conversation_id: Conversation ID to delete

        Returns:
            True if deleted, False if not found
        """
        _, conversations_path, _ = self._get_paths_for_project(project_path)
        conversation_file = os.path.join(conversations_path, f"{conversation_id}.json")
        if not os.path.exists(conversation_file):
            return False

        # Remove file
        os.remove(conversation_file)

        # Remove from index
        index = self._load_index(project_path)
        index['conversations'] = [
            conv for conv in index['conversations']
            if conv['conversation_id'] != conversation_id
        ]
        self._save_index(project_path, index)

        return True

    def add_message(self, project_path: str, conversation_id: str, message: Message) -> bool:
        """
        Add a message to a conversation.

        Args:
            project_path: Path to the project directory
            conversation_id: Conversation ID
            message: Message to add

        Returns:
            True if successful, False if conversation not found
        """
        conversation = self.get_conversation(project_path, conversation_id)
        if not conversation:
            return False

        conversation.add_message(message)
        self.save_conversation(project_path, conversation)
        return True

    def get_or_create_default_conversation(self, project_path: str) -> Conversation:
        """
        Get the most recent conversation or create a new one if none exist.

        Args:
            project_path: Path to the project directory

        Returns:
            Conversation object
        """
        conversations = self.list_conversations(project_path)
        if conversations:
            # Return most recent conversation
            return self.get_conversation(project_path, conversations[0]['conversation_id'])
        else:
            # Create new conversation
            return self.create_conversation(project_path, title="New Conversation")