"""Example usage of Filmeto Agent module."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import FilmetoAgent
from app.data.workspace import Workspace


async def example_basic_chat():
    """Example 1: Basic chat interaction."""
    print("\n" + "="*60)
    print("Example 1: Basic Chat")
    print("="*60)
    
    # Initialize workspace and get project
    workspace = Workspace("/path/to/workspace", "project_name")
    project = workspace.get_project()
    
    if not project:
        print("No project found. Please create a project first.")
        return
    
    # Create agent
    agent = FilmetoAgent(
        workspace=workspace,
        project=project,
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # Simple chat
    response = await agent.chat("What is the current project about?")
    print(f"\nAgent: {response}")


async def example_streaming_chat():
    """Example 2: Streaming chat with callbacks."""
    print("\n" + "="*60)
    print("Example 2: Streaming Chat")
    print("="*60)
    
    workspace = Workspace("/path/to/workspace", "project_name")
    project = workspace.get_project()
    
    if not project:
        print("No project found.")
        return
    
    agent = FilmetoAgent(
        workspace=workspace,
        project=project,
        streaming=True
    )
    
    print("\nUser: List all characters in my project")
    print("Agent: ", end='', flush=True)
    
    # Stream response with token callback
    async for token in agent.chat_stream(
        message="List all characters in my project",
        on_token=lambda t: print(t, end='', flush=True),
        on_complete=lambda r: print("\n✅ Response complete!")
    ):
        pass


async def example_tool_usage():
    """Example 3: Using agent tools."""
    print("\n" + "="*60)
    print("Example 3: Tool Usage")
    print("="*60)
    
    workspace = Workspace("/path/to/workspace", "project_name")
    project = workspace.get_project()
    
    if not project:
        print("No project found.")
        return
    
    agent = FilmetoAgent(workspace=workspace, project=project)
    
    # Agent will use tools to answer
    questions = [
        "What characters are in my project?",
        "What resources do I have?",
        "What is the current timeline position?",
    ]
    
    for question in questions:
        print(f"\nUser: {question}")
        response = await agent.chat(question)
        print(f"Agent: {response}")


async def example_complex_task():
    """Example 4: Complex multi-step task."""
    print("\n" + "="*60)
    print("Example 4: Complex Task")
    print("="*60)
    
    workspace = Workspace("/path/to/workspace", "project_name")
    project = workspace.get_project()
    
    if not project:
        print("No project found.")
        return
    
    agent = FilmetoAgent(workspace=workspace, project=project)
    
    # Complex request that requires planning
    print("\nUser: Create a video scene with the first character in my project")
    print("Agent: ", end='', flush=True)
    
    async for token in agent.chat_stream(
        message="Create a video scene with the first character in my project",
        on_token=lambda t: print(t, end='', flush=True)
    ):
        pass
    
    print()


async def example_conversation_management():
    """Example 5: Managing conversations."""
    print("\n" + "="*60)
    print("Example 5: Conversation Management")
    print("="*60)
    
    workspace = Workspace("/path/to/workspace", "project_name")
    project = workspace.get_project()
    
    if not project:
        print("No project found.")
        return
    
    agent = FilmetoAgent(workspace=workspace, project=project)
    
    # Create new conversation
    conversation = agent.create_conversation(title="Video Planning Session")
    print(f"\n✅ Created conversation: {conversation.title}")
    print(f"   ID: {conversation.conversation_id}")
    
    # Chat in conversation
    await agent.chat(
        "Let's plan a video about space exploration",
        conversation_id=conversation.conversation_id
    )
    
    # List all conversations
    print("\nAll conversations:")
    conversations = agent.list_conversations()
    for conv in conversations:
        print(f"  - {conv['title']} ({conv['conversation_id']})")
        print(f"    Updated: {conv['updated_at']}")
    
    # Get conversation history
    history = agent.get_conversation_history(conversation.conversation_id)
    print(f"\nConversation has {len(history)} messages")


async def example_custom_tool():
    """Example 6: Adding custom tools."""
    print("\n" + "="*60)
    print("Example 6: Custom Tools")
    print("="*60)
    
    from agent.tools import FilmetoBaseTool
    from pydantic import BaseModel, Field
    
    # Define custom tool
    class GetWeatherInput(BaseModel):
        location: str = Field(description="Location to get weather for")
    
    class GetWeatherTool(FilmetoBaseTool):
        name: str = "get_weather"
        description: str = "Get weather information for a location"
        args_schema: type[BaseModel] = GetWeatherInput
        
        def _run(self, location: str) -> str:
            # Mock weather data
            return f"Weather in {location}: Sunny, 72°F"
    
    workspace = Workspace("/path/to/workspace", "project_name")
    project = workspace.get_project()
    
    if not project:
        print("No project found.")
        return
    
    agent = FilmetoAgent(workspace=workspace, project=project)
    
    # Register custom tool
    agent.tool_registry.register_tool(
        GetWeatherTool(workspace=workspace, project=project)
    )
    
    # Rebuild graph with new tool
    agent.tools = agent.tool_registry.get_all_tools()
    agent.graph = agent._build_graph()
    
    print("\n✅ Custom tool registered")
    print(f"Available tools: {agent.tool_registry.get_tool_names()}")
    
    # Use custom tool
    response = await agent.chat("What's the weather in San Francisco?")
    print(f"\nAgent: {response}")


async def example_error_handling():
    """Example 7: Error handling."""
    print("\n" + "="*60)
    print("Example 7: Error Handling")
    print("="*60)
    
    workspace = Workspace("/path/to/workspace", "project_name")
    project = workspace.get_project()
    
    if not project:
        print("No project found.")
        return
    
    agent = FilmetoAgent(workspace=workspace, project=project)
    
    try:
        # This might fail if API key is not set
        response = await agent.chat("Hello!")
        print(f"Agent: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure to set your OpenAI API key in settings.yaml")


async def main():
    """Run all examples."""
    examples = [
        ("Basic Chat", example_basic_chat),
        ("Streaming Chat", example_streaming_chat),
        ("Tool Usage", example_tool_usage),
        ("Complex Task", example_complex_task),
        ("Conversation Management", example_conversation_management),
        ("Custom Tools", example_custom_tool),
        ("Error Handling", example_error_handling),
    ]
    
    print("\n" + "="*60)
    print("Filmeto Agent Examples")
    print("="*60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    print("\nRunning all examples...")
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)


if __name__ == "__main__":
    # Note: Update workspace path before running
    print("⚠️  Update workspace path in examples before running!")
    print("⚠️  Make sure to set OPENAI_API_KEY environment variable")
    
    # Uncomment to run:
    # asyncio.run(main())

