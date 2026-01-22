"""
Agent Chat Signals Module

This module provides a singleton class AgentChatSignals that manages
blinker signals for agent chat functionality.
"""

import blinker
from typing import Any
from .agent_chat_message import AgentMessage, MessageType


class AgentChatSignals:
    """
    Singleton class that provides blinker signals for agent chat functionality.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.agent_message_send = blinker.Signal()
        return cls._instance

    def send_agent_message(self, content: str, sender_id: str = "system", sender_name: str = "System",
                          message_type: MessageType = MessageType.TEXT, metadata: dict = None) -> AgentMessage:
        """
        Send an agent message via the blinker signal.

        Args:
            content: The content of the message
            sender_id: ID of the sender (defaults to "system")
            sender_name: Name of the sender (defaults to "System")
            message_type: Type of the message (defaults to MessageType.TEXT)
            metadata: Additional metadata for the message (optional)

        Returns:
            AgentMessage: The message object that was sent
        """
        message = AgentMessage(
            content=content,
            message_type=message_type,
            sender_id=sender_id,
            sender_name=sender_name,
            metadata=metadata or {}
        )
        self.agent_message_send.send(self, message=message)
        return message