"""
Main agent module for Filmeto application.
Implements the FilmetoAgent singleton class with streaming capabilities.
"""
import asyncio
from typing import AsyncIterator, Dict, List, Optional, Callable
from threading import Lock
from .message import AgentMessage, MessageType


class AgentRole:
    """Represents an agent with a specific role in the conversation."""
    
    def __init__(self, agent_id: str, name: str, role_description: str, handler_func: Callable):
        self.agent_id = agent_id
        self.name = name
        self.role_description = role_description
        self.handler_func = handler_func
    
    async def handle_message(self, message: AgentMessage) -> AsyncIterator[AgentMessage]:
        """Handle a message and yield responses."""
        async for response in self.handler_func(message):
            yield response


class FilmetoAgent:
    """
    Singleton class for managing agent capabilities in Filmeto.
    Provides streaming conversation interface and manages multiple agents.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Ensure only one instance of FilmetoAgent exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(FilmetoAgent, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the FilmetoAgent instance."""
        if not self._initialized:
            self.agents: Dict[str, AgentRole] = {}
            self.conversation_history: List[AgentMessage] = []
            self._initialized = True
    
    def register_agent(self, agent_id: str, name: str, role_description: str, handler_func: Callable):
        """
        Register a new agent with a specific role.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Display name for the agent
            role_description: Description of the agent's role
            handler_func: Async function that handles messages and yields responses
        """
        self.agents[agent_id] = AgentRole(agent_id, name, role_description, handler_func)
    
    def get_agent(self, agent_id: str) -> Optional[AgentRole]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentRole]:
        """List all registered agents."""
        return list(self.agents.values())
    
    async def start_conversation(self, initial_prompt: AgentMessage) -> AsyncIterator[AgentMessage]:
        """
        Start a streaming conversation with the agents.
        
        Args:
            initial_prompt: The initial message to start the conversation
            
        Yields:
            AgentMessage: Stream of messages from various agents
        """
        # Add the initial prompt to history
        self.conversation_history.append(initial_prompt)
        
        # Determine which agent should respond based on the message content or routing rules
        responding_agent = await self._select_responding_agent(initial_prompt)
        
        if responding_agent:
            async for response in responding_agent.handle_message(initial_prompt):
                # Add response to history
                self.conversation_history.append(response)
                yield response
        else:
            # If no specific agent is selected, return a system message
            error_msg = AgentMessage(
                content="No suitable agent found to handle this request.",
                message_type=MessageType.ERROR,
                sender_id="system",
                sender_name="System"
            )
            self.conversation_history.append(error_msg)
            yield error_msg
    
    async def _select_responding_agent(self, message: AgentMessage) -> Optional[AgentRole]:
        """
        Select which agent should respond to a message based on content or routing rules.
        
        Args:
            message: The message to route
            
        Returns:
            AgentRole: The selected agent or None if no agent should respond
        """
        # Simple routing logic - could be enhanced with more sophisticated rules
        content_lower = message.content.lower()
        
        # Check if a specific agent is mentioned in the message
        for agent in self.agents.values():
            if agent.name.lower() in content_lower or agent.agent_id.lower() in content_lower:
                return agent
        
        # Default to first agent if no specific one is mentioned
        if self.agents:
            return next(iter(self.agents.values()))
        
        return None
    
    def get_conversation_history(self) -> List[AgentMessage]:
        """Get the entire conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
    
    async def broadcast_message(self, message: AgentMessage) -> AsyncIterator[AgentMessage]:
        """
        Broadcast a message to all agents and collect their responses.
        
        Args:
            message: The message to broadcast
            
        Yields:
            AgentMessage: Responses from all agents
        """
        for agent in self.agents.values():
            try:
                async for response in agent.handle_message(message):
                    self.conversation_history.append(response)
                    yield response
            except Exception as e:
                error_msg = AgentMessage(
                    content=f"Error in agent {agent.name}: {str(e)}",
                    message_type=MessageType.ERROR,
                    sender_id="system",
                    sender_name="System"
                )
                self.conversation_history.append(error_msg)
                yield error_msg