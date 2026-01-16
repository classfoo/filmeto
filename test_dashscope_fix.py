"""
Test script to verify DashScope API integration with LiteLLM
"""
import asyncio
import os
from agent.llm import LlmService


def test_dashscope_integration():
    """Test DashScope API integration"""
    print("Testing DashScope API integration...")
    
    # Create an instance of LlmService
    llm_service = LlmService()
    
    # Configure for DashScope
    api_key = os.getenv("DASHSCOPE_API_KEY", "YOUR_DASHSCOPE_API_KEY_HERE")
    api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    llm_service.configure(
        api_key=api_key,
        api_base=api_base,
        default_model="qwen-turbo"  # Using a common DashScope model
    )
    
    print(f"API Base: {llm_service.api_base}")
    print(f"API Key Set: {bool(llm_service.api_key)}")
    print(f"Default Model: {llm_service.default_model}")
    
    # Test sync completion
    try:
        print("\nTesting sync completion...")
        response = llm_service.completion(
            messages=[{"role": "user", "content": "Hello, how are you?"}]
        )
        print("Sync completion successful!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Sync completion failed: {e}")
    
    # Test async completion
    try:
        print("\nTesting async completion...")
        async def test_async():
            response = await llm_service.acompletion(
                messages=[{"role": "user", "content": "What is your name?"}]
            )
            print("Async completion successful!")
            print(f"Response: {response}")
        
        asyncio.run(test_async())
    except Exception as e:
        print(f"Async completion failed: {e}")


if __name__ == "__main__":
    test_dashscope_integration()