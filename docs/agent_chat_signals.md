# Agent Chat Signals

The `agent_chat_signals.py` module provides a signaling mechanism for agent chat functionality using the [blinker](https://blinker.readthedocs.io/) library.

## Components

### AgentMessage Class

The `AgentMessage` class is imported from `agent.chat.agent_chat_message` and represents a message sent by an agent with the following attributes:

- `content` (str): The content of the message
- `message_type` (MessageType): The type of the message (TEXT, CODE, IMAGE, etc.)
- `sender_id` (str): ID of the sender
- `sender_name` (str): Name of the sender
- `timestamp` (datetime): Timestamp of when the message was created
- `metadata` (dict): Additional metadata for the message
- `message_id` (str): Unique identifier for the message
- `structured_content` (List[StructureContent]): Structured content within the message

### AgentChatSignals Class

A singleton class that provides:

- `agent_message_send`: A blinker signal that is emitted when an agent sends a message
- `send_agent_message()`: A method to send an AgentMessage via the signal

## Usage

```python
from agent.chat.agent_chat_signals import AgentChatSignals
from agent.chat.agent_chat_message import MessageType

# Get the singleton instance
signals = AgentChatSignals()

# Connect to the signal
def message_handler(sender, **kwargs):
    message = kwargs.get('message')
    print(f"Received message from {message.sender_name} ({message.sender_id}): {message.content}")

signals.agent_message_send.connect(message_handler)

# Send a message
message = signals.send_agent_message(
    content="Hello, world!",
    sender_id="agent1",
    sender_name="AI Assistant",
    message_type=MessageType.TEXT,
    metadata={"priority": "high"}
)
```

## Thread Safety

The blinker library provides thread-safe signal delivery, making this module suitable for use in multi-threaded environments.