"""
Example implementation showing how to use the FilmetoAgent system.
"""
import asyncio
from typing import AsyncIterator
from agent import FilmetoAgent, AgentMessage
from agent.chat.agent_chat_types import MessageType


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
    # Create an instance of FilmetoAgent with mock workspace and project
    agent_manager = FilmetoAgent(workspace=None, project=None)

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

    print("Starting conversation...")

    # Define callback functions for the chat stream
    def on_token(token):
        print(f"Token received: {token}")

    def on_complete(response):
        print(f"Response complete: {response}")

    # Start the chat stream and process responses
    async for token in agent_manager.chat_stream(
        message="How can we improve user engagement in video editing applications?",
        on_token=on_token,
        on_complete=on_complete
    ):
        print(f"Received token: {token}")
        break  # Just process the first token for this example

    print("\nConversation history:")
    for msg in agent_manager.get_conversation_history():
        print(f"- [{msg.sender_name}]: {msg.content[:50]}...")


if __name__ == "__main__":
    asyncio.run(main())