# Filmeto Agent System

The Filmeto Agent system provides AI-powered conversational capabilities for the Filmeto application. It implements a multi-agent architecture with streaming message capabilities.

## Components

### AgentMessage
- Defines the standardized message format used throughout the system
- Supports multiple content types (text, code, image, video, audio, file, command, error, system, tool_call, tool_response)
- Includes metadata, timestamps, and sender information

### MessageType Enum
- Enumerates all supported message types
- Enables different card types in the UI based on message type

### AgentRole
- Represents an individual agent with specific capabilities
- Contains a handler function that processes messages and generates responses

### FilmetoAgent (Singleton)
- Central manager for all agents in the system
- Provides streaming conversation interface
- Manages conversation history
- Routes messages to appropriate agents
- Supports broadcasting messages to all agents

## Usage

### Registering Agents
```python
from agent import FilmetoAgent, AgentMessage, MessageType

async def my_agent_handler(message: AgentMessage) -> AsyncIterator[AgentMessage]:
    # Process the message and yield responses
    response = AgentMessage(
        content="Response content",
        message_type=MessageType.TEXT,
        sender_id="my_agent",
        sender_name="My Agent"
    )
    yield response

# Get the singleton instance
agent_manager = FilmetoAgent()

# Register an agent
agent_manager.register_agent(
    "my_agent_id",
    "My Agent Name",
    "Description of what this agent does",
    my_agent_handler
)
```

### Starting a Conversation
```python
initial_message = AgentMessage(
    content="Hello, agents!",
    message_type=MessageType.TEXT,
    sender_id="user",
    sender_name="User"
)

async for message in agent_manager.start_conversation(initial_message):
    # Process each message in the stream
    print(f"[{message.sender_name}]: {message.content}")
```

## Streaming Interface

The agent system provides an asynchronous iterator interface for streaming responses:

```python
async def chat_stream(self, initial_prompt: AgentMessage) -> AsyncIterator[AgentMessage]:
```

This allows the UI (AgentPanel) to receive messages in real-time as they are generated, displaying them as cards in the conversation.

## Agent Panel Integration

The AgentPanel should:
1. Initialize the FilmetoAgent when the first prompt is sent
2. Handle the streaming responses and update the conversation UI
3. Render different card types based on the MessageType
4. Support multi-agent conversations by leveraging the routing capabilities