"""
Simple test for the FilmetoAgent implementation.
"""
import asyncio
from agent import FilmetoAgent, AgentMessage, MessageType


async def test_agent_registration():
    """Test registering and retrieving agents."""
    agent_manager = FilmetoAgent(workspace=None, project=None)
    
    # Clear any existing agents
    agent_manager.agents.clear()
    
    # Register a test agent
    async def test_handler(msg: AgentMessage):
        response = AgentMessage(
            content="Test response",
            message_type=MessageType.TEXT,
            sender_id="test_agent",
            sender_name="Test Agent"
        )
        yield response
    
    agent_manager.register_agent(
        "test_agent",
        "Test Agent",
        "A test agent",
        test_handler
    )
    
    # Verify agent was registered
    assert len(agent_manager.list_agents()) == 1
    agent = agent_manager.get_agent("test_agent")
    assert agent is not None
    assert agent.name == "Test Agent"
    
    print("✓ Agent registration test passed")


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
    print("Running FilmetoAgent tests...")
    
    await test_agent_registration()
    await test_chat_stream_functionality()
    
    print("\nAll tests passed! ✓")


if __name__ == "__main__":
    asyncio.run(main())