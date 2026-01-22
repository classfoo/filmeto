"""
Simple test for the AgentPanel integration with chat_stream.
"""
import asyncio
from agent import FilmetoAgent, AgentMessage
from agent.chat.agent_chat_types import MessageType


async def test_chat_stream_method_exists():
    """Test that the chat_stream method exists and is accessible."""
    agent_manager = FilmetoAgent(workspace=None, project=None)
    
    # Verify the method exists
    assert hasattr(agent_manager, 'chat_stream'), "chat_stream method should exist"
    
    # Verify it's callable
    assert callable(getattr(agent_manager, 'chat_stream')), "chat_stream should be callable"
    
    print("✓ chat_stream method exists and is callable")


async def test_chat_stream_functionality():
    """Test that chat_stream works with the new interface."""
    agent_manager = FilmetoAgent(workspace=None, project=None)
    
    # Clear any existing agents
    agent_manager.agents.clear()
    
    # Register a test agent
    async def echo_handler(msg: AgentMessage):
        response = AgentMessage(
            content=f"Echo: {msg.content}",
            message_type=MessageType.TEXT,
            sender_id="echo_agent",
            sender_name="Echo Agent"
        )
        yield response
    
    agent_manager.register_agent(
        "echo_agent",
        "Echo Agent",
        "An agent that echoes messages",
        echo_handler
    )
    
    # Test that chat_stream works with the new interface
    responses = []
    async for token in agent_manager.chat_stream(
        message="Hello, world!",
        on_token=lambda t: responses.append(t)
    ):
        break  # Just get the first token for this test
    
    assert len(responses) >= 1
    assert "Echo: Hello, world!" in responses[0]
    
    print("✓ chat_stream functionality test passed")


async def main():
    """Run all tests."""
    print("Testing AgentPanel integration with chat_stream...")
    
    await test_chat_stream_method_exists()
    await test_chat_stream_functionality()
    
    print("\nAll integration tests passed! ✓")


if __name__ == "__main__":
    asyncio.run(main())