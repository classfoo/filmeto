"""
Utility functions for the Filmeto agent system.
"""
import logging
from typing import Dict, Any
from agent.chat.agent_chat_message import AgentMessage

logger = logging.getLogger(__name__)


def create_text_message(content: str, sender_id: str, sender_name: str = "") -> AgentMessage:
    """
    Helper function to create a text message.

    Args:
        content: The text content of the message
        sender_id: The ID of the sender
        sender_name: The display name of the sender

    Returns:
        AgentMessage: A properly formatted text message
    """
    from agent.chat.agent_chat_message import MessageType
    message = AgentMessage(
        content=content,
        message_type=MessageType.TEXT,
        sender_id=sender_id,
        sender_name=sender_name
    )
    logger.info(f"📝 Created text message: id={message.message_id}, sender='{sender_id}', content_preview='{content[:50]}{'...' if len(content) > 50 else ''}'")
    return message


def create_error_message(content: str, sender_id: str = "system", sender_name: str = "System") -> AgentMessage:
    """
    Helper function to create an error message.

    Args:
        content: The error content
        sender_id: The ID of the sender (defaults to system)
        sender_name: The display name of the sender (defaults to System)

    Returns:
        AgentMessage: A properly formatted error message
    """
    from agent.chat.agent_chat_message import MessageType
    message = AgentMessage(
        content=content,
        message_type=MessageType.ERROR,
        sender_id=sender_id,
        sender_name=sender_name
    )
    logger.info(f"❌ Created error message: id={message.message_id}, sender='{sender_id}', content_preview='{content[:50]}{'...' if len(content) > 50 else ''}'")
    return message


def create_system_message(content: str) -> AgentMessage:
    """
    Helper function to create a system message.

    Args:
        content: The system message content

    Returns:
        AgentMessage: A properly formatted system message
    """
    from agent.chat.agent_chat_message import MessageType
    message = AgentMessage(
        content=content,
        message_type=MessageType.SYSTEM,
        sender_id="system",
        sender_name="System"
    )
    logger.info(f"⚙️ Created system message: id={message.message_id}, sender='system', content_preview='{content[:50]}{'...' if len(content) > 50 else ''}'")
    return message


def format_card_data(message: AgentMessage) -> Dict[str, Any]:
    """
    Format message data for UI card display.

    Args:
        message: The AgentMessage to format

    Returns:
        Dictionary containing formatted data for UI rendering
    """
    return {
        "id": message.message_id,
        "content": message.content,
        "type": message.message_type.value,
        "sender": {
            "id": message.sender_id,
            "name": message.sender_name
        },
        "timestamp": message.timestamp.isoformat(),
        "metadata": message.metadata,
        "structured_content": [item.to_dict() for item in message.structured_content]
    }