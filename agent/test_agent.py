"""
Simple test for the FilmetoAgent implementation.
"""
import asyncio
from agent import FilmetoAgent, AgentMessage, MessageType


async def test_agent_registration():
    """Test registering and retrieving agents."""
    agent_manager = FilmetoAgent()
    
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


async def test_singleton_behavior():
    """Test that FilmetoAgent behaves as a singleton."""
    agent1 = FilmetoAgent()
    agent2 = FilmetoAgent()
    
    # They should be the same instance
    assert agent1 is agent2
    
    # Register an agent with one instance
    async def dummy_handler(msg: AgentMessage):
        yield msg
    
    agent1.register_agent("dummy", "Dummy", "A dummy agent", dummy_handler)
    
    # Should be accessible from the other instance
    assert agent2.get_agent("dummy") is not None
    
    print("✓ Singleton behavior test passed")


async def test_message_streaming():
    """Test the streaming message functionality."""
    agent_manager = FilmetoAgent()
    
    # Clear any existing agents
    agent_manager.agents.clear()
    
    # Register a test agent that yields multiple messages
    async def streaming_handler(msg: AgentMessage):
        for i in range(3):
            response = AgentMessage(
                content=f"Response {i+1}",
                message_type=MessageType.TEXT,
                sender_id="stream_test",
                sender_name="Stream Test Agent"
            )
            yield response
            await asyncio.sleep(0.1)  # Small delay to simulate processing
    
    agent_manager.register_agent(
        "stream_test",
        "Stream Test Agent",
        "An agent that streams multiple messages",
        streaming_handler
    )
    
    # Create initial message
    initial_msg = AgentMessage(
        content="Test message",
        message_type=MessageType.TEXT,
        sender_id="user",
        sender_name="User"
    )
    
    # Collect streamed responses
    responses = []
    count = 0
    async for response in agent_manager.start_conversation(initial_msg):
        responses.append(response)
        count += 1
        if count >= 3:  # We expect 3 responses from the handler
            break
    
    assert len(responses) == 3
    assert all(r.content.startswith("Response") for r in responses)
    
    print("✓ Message streaming test passed")


async def main():
    """Run all tests."""
    print("Running FilmetoAgent tests...")
    
    await test_agent_registration()
    await test_singleton_behavior()
    await test_message_streaming()
    
    print("\nAll tests passed! ✓")


if __name__ == "__main__":
    asyncio.run(main())