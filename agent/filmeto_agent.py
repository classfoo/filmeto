"""
Main agent module for Filmeto application.
Implements the FilmetoAgent class with streaming capabilities.
"""
import asyncio
import uuid
from typing import AsyncIterator, Dict, List, Optional, Callable, Any
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


class AgentStreamSession:
    """Represents a streaming session with the agent."""
    
    def __init__(self, session_id: str, initial_message: str):
        self.session_id = session_id
        self.initial_message = initial_message
        self.responses = []
        self.is_active = True


class StreamEvent:
    """Represents an event in the streaming process."""
    
    def __init__(self, event_type: str, data: Any, timestamp: float = None):
        import time
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or time.time()


class FilmetoAgent:
    """
    Class for managing agent capabilities in Filmeto.
    Provides streaming conversation interface and manages multiple agents.
    """
    
    def __init__(self, workspace=None, project=None, model='gpt-4o-mini', temperature=0.7, streaming=True):
        """Initialize the FilmetoAgent instance."""
        self.workspace = workspace
        self.project = project
        self.model = model
        self.temperature = temperature
        self.streaming = streaming
        self.agents: Dict[str, AgentRole] = {}
        self.conversation_history: List[AgentMessage] = []
        self.ui_callbacks = []
        self.current_session: Optional[AgentStreamSession] = None
        self.production_agent = None  # Will be set by the actual AI implementation
        
        # Initialize the actual production agent (this would typically connect to an AI service)
        self._init_production_agent()
    
    def _init_production_agent(self):
        """Initialize the production agent (placeholder implementation)."""
        # This would normally connect to an actual AI service like OpenAI, etc.
        # For now, we'll just set a flag indicating it's not configured
        # In a real implementation, this would check for API keys and initialize accordingly
        import os
        api_key = os.getenv("OPENAI_API_KEY")  # Or whatever service is being used
        if api_key:
            # Initialize the actual AI agent here
            pass
        else:
            # Production agent not configured due to missing API key
            pass
    
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

    def add_ui_callback(self, callback):
        """Add a UI callback for streaming events."""
        if callback not in self.ui_callbacks:
            self.ui_callbacks.append(callback)

    def remove_ui_callback(self, callback):
        """Remove a UI callback."""
        if callback in self.ui_callbacks:
            self.ui_callbacks.remove(callback)

    def get_current_session(self) -> Optional[AgentStreamSession]:
        """Get the current streaming session."""
        return self.current_session

    async def chat_stream(self, message: str, on_token=None, on_complete=None, on_stream_event=None):
        """
        Stream responses for a chat conversation with the agents.
        
        Args:
            message: The message to process
            on_token: Callback for each token received
            on_complete: Callback when response is complete
            on_stream_event: Callback for stream events
        """
        # Create an AgentMessage from the string
        initial_prompt = AgentMessage(
            content=message,
            message_type=MessageType.TEXT,
            sender_id="user",
            sender_name="User"
        )
        
        # Create a new session
        session_id = str(uuid.uuid4())
        self.current_session = AgentStreamSession(session_id, message)
        
        # Add the initial prompt to history
        self.conversation_history.append(initial_prompt)
        
        # Send a stream event for the user message
        if on_stream_event:
            on_stream_event(StreamEvent("user_message", {"content": message, "session_id": session_id}))
        
        # Determine which agent should respond based on the message content or routing rules
        responding_agent = await self._select_responding_agent(initial_prompt)
        
        if responding_agent:
            async for response in responding_agent.handle_message(initial_prompt):
                # Add response to history
                self.conversation_history.append(response)
                
                # Call the on_token callback if provided
                if on_token:
                    on_token(response.content)
                
                # Send a stream event for the agent response
                if on_stream_event:
                    on_stream_event(StreamEvent("agent_response", {
                        "content": response.content,
                        "sender_name": response.sender_name,
                        "message_type": response.message_type.value,
                        "session_id": session_id
                    }))
                
                # Yield the response content (token)
                yield response.content
        else:
            # If no specific agent is selected, return a system message
            error_msg = AgentMessage(
                content="No suitable agent found to handle this request.",
                message_type=MessageType.ERROR,
                sender_id="system",
                sender_name="System"
            )
            self.conversation_history.append(error_msg)
            
            # Call the on_token callback if provided
            if on_token:
                on_token(error_msg.content)
            
            # Send a stream event for the error
            if on_stream_event:
                on_stream_event(StreamEvent("error", {
                    "content": error_msg.content,
                    "session_id": session_id
                }))
            
            yield error_msg.content

        # Call on_complete callback if provided
        if on_complete:
            on_complete(message)

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

    def update_context(self, project=None):
        """Update the agent context with new project information."""
        if project:
            self.project = project

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
                    yield response.content  # Yield just the content for consistency
            except Exception as e:
                error_msg = AgentMessage(
                    content=f"Error in agent {agent.name}: {str(e)}",
                    message_type=MessageType.ERROR,
                    sender_id="system",
                    sender_name="System"
                )
                self.conversation_history.append(error_msg)
                yield error_msg.content  # Yield just the content for consistency