"""
Example implementation showing how to use the FilmetoAgent system.
"""
import asyncio
from typing import AsyncIterator
from agent import FilmetoAgent, AgentMessage, MessageType


async def creative_writer_handler(message: AgentMessage) -> AsyncIterator[AgentMessage]:
    """Example handler for a creative writer agent."""
    # Simulate processing time
    await asyncio.sleep(0.5)
    
    response = AgentMessage(
        content=f"As a creative writer, I think '{message.content}' has great potential for a story!",
        message_type=MessageType.TEXT,
        sender_id="creative_writer",
        sender_name="Creative Writer"
    )
    yield response


async def technical_expert_handler(message: AgentMessage) -> AsyncIterator[AgentMessage]:
    """Example handler for a technical expert agent."""
    # Simulate processing time
    await asyncio.sleep(0.7)
    
    response = AgentMessage(
        content=f"From a technical perspective, '{message.content}' could be implemented using advanced algorithms.",
        message_type=MessageType.TEXT,
        sender_id="tech_expert",
        sender_name="Technical Expert"
    )
    yield response


async def main():
    """Example usage of the FilmetoAgent system."""
    # Get the singleton instance
    agent_manager = FilmetoAgent()
    
    # Register different agents
    agent_manager.register_agent(
        "creative_writer",
        "Creative Writer",
        "Specializes in creative content and storytelling",
        creative_writer_handler
    )
    
    agent_manager.register_agent(
        "tech_expert", 
        "Technical Expert",
        "Provides technical insights and solutions",
        technical_expert_handler
    )
    
    # Create an initial prompt
    initial_message = AgentMessage(
        content="How can we improve user engagement in video editing applications?",
        message_type=MessageType.TEXT,
        sender_id="user",
        sender_name="User"
    )
    
    print("Starting conversation...")
    
    # Start the conversation and process responses
    async for message in agent_manager.start_conversation(initial_message):
        print(f"[{message.sender_name}]: {message.content}")
        
        # Stop after first response for this example
        break
    
    print("\nConversation history:")
    for msg in agent_manager.get_conversation_history():
        print(f"- [{msg.sender_name}]: {msg.content[:50]}...")


if __name__ == "__main__":
    asyncio.run(main())