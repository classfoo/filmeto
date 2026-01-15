"""
Example usage of the new LlmService in Filmeto Agent.
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/root/filmeto')

from agent.llm.llm_service import LlmService
from app.data.settings import Settings
from agent.filmeto_agent import FilmetoAgent


def example_usage_with_settings():
    """Example showing how to use LlmService with system settings."""
    print("=== Example: Using LlmService with system settings ===")

    # Assuming you have a workspace with settings
    # In practice, you would have an actual workspace object
    workspace_path = "/tmp/test_workspace"  # Example path
    os.makedirs(workspace_path, exist_ok=True)

    # Create a settings object
    settings = Settings(workspace_path)

    # Create a mock workspace that has a settings attribute
    class MockWorkspace:
        def __init__(self, settings):
            self.settings = settings

    workspace = MockWorkspace(settings)

    # Create the LlmService with workspace (it will internally access settings)
    llm_service = LlmService(workspace)

    # The service will automatically load settings from the settings service
    config = llm_service.get_current_config()
    print(f"LlmService configuration: {config}")

    # You can also manually configure the service
    llm_service.configure(
        api_key="your-openai-api-key-here",
        api_base="https://api.openai.com/v1",
        default_model="gpt-4o",
        temperature=0.5
    )

    print("LlmService configured with custom settings.")
    print()


def example_usage_with_filmeto_agent():
    """Example showing how FilmetoAgent now uses LlmService internally."""
    print("=== Example: FilmetoAgent using LlmService ===")
    
    # Create a FilmetoAgent - it will automatically create/use an LlmService
    # If you pass a workspace with settings, it will use those settings
    agent = FilmetoAgent()
    
    print(f"Agent created with LlmService: {type(agent.llm_service).__name__}")
    
    # The agent can now use the LlmService for AI operations
    # (Actual AI operations would require valid API keys)
    
    # You can also pass a custom LlmService to the agent
    custom_llm_service = LlmService()
    custom_agent = FilmetoAgent(llm_service=custom_llm_service)
    
    print(f"Custom agent created with LlmService: {type(custom_agent.llm_service).__name__}")
    print()


async def example_async_completion():
    """Example showing how to use the async completion method."""
    print("=== Example: Async completion with LlmService ===")
    
    llm_service = LlmService()
    
    # Example of how to call the acompletion method
    # Note: This will require valid API credentials to work properly
    try:
        # This is just a demonstration of the method call
        # In practice, you would need valid API credentials
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        
        print("Calling acompletion method...")
        print("(Note: This would require valid API credentials to complete successfully)")
        
        # The actual call would be:
        # response = await llm_service.acompletion(
        #     model="gpt-4o-mini",
        #     messages=messages,
        #     temperature=0.7
        # )
        # print(f"Response: {response}")
        
    except Exception as e:
        print(f"Expected error due to missing API credentials: {e}")
    
    print()


if __name__ == "__main__":
    print("LlmService Example Usage\n")
    
    example_usage_with_settings()
    example_usage_with_filmeto_agent()
    asyncio.run(example_async_completion())
    
    print("Examples completed!")