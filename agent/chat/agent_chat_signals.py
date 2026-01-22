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
            cls._instance.__agent_message_send = blinker.Signal()
        return cls._instance

    def connect(self, receiver, weak: bool = True):
        """
        Connect a receiver function to the agent_message_send signal.

        Args:
            receiver: A function that receives the signal
            weak: Whether to use a weak reference (default True)
        """
        self.__agent_message_send.connect(receiver, weak=weak)

    def disconnect(self, receiver):
        """
        Disconnect a receiver function from the agent_message_send signal.

        Args:
            receiver: The function to disconnect
        """
        self.__agent_message_send.disconnect(receiver)

    async def send_agent_message(self, content: str, sender_id: str = "system", sender_name: str = "System",
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
        self.__agent_message_send.send(self, message=message)
        return message