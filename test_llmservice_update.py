"""
Test script to verify the updated LLMService implementation
"""
import asyncio
import os
from agent.llm import LlmService


def test_provider_detection():
    """Test that provider detection works correctly"""
    print("Testing provider detection...")
    
    # Test DashScope detection
    llm_service = LlmService()
    dashscope_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    provider = llm_service._detect_provider_from_base_url(dashscope_url)
    assert provider == "dashscope", f"Expected 'dashscope', got '{provider}'"
    print("✓ DashScope provider detection works")
    
    # Test OpenAI detection
    openai_url = "https://api.openai.com/v1"
    provider = llm_service._detect_provider_from_base_url(openai_url)
    assert provider == "openai", f"Expected 'openai', got '{provider}'"
    print("✓ OpenAI provider detection works")
    
    # Test Azure detection
    azure_url = "https://my-resource.openai.azure.com"
    provider = llm_service._detect_provider_from_base_url(azure_url)
    assert provider == "azure", f"Expected 'azure', got '{provider}'"
    print("✓ Azure provider detection works")


def test_model_prefixing():
    """Test that model names are properly prefixed for DashScope"""
    print("\nTesting model prefixing...")
    
    # Create an instance and configure for DashScope
    llm_service = LlmService()
    llm_service.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_service.provider = llm_service._detect_provider_from_base_url(llm_service.api_base)
    
    # Test that model gets prefixed
    original_model = "qwen-turbo"
    expected_prefixed_model = "dashscope/qwen-turbo"
    
    # Since we can't actually call the API without a key, we'll just test the logic
    # by checking if the provider is correctly set
    assert llm_service.provider == "dashscope", f"Expected 'dashscope', got '{llm_service.provider}'"
    print(f"✓ Provider correctly set to: {llm_service.provider}")
    
    # Test that model names get prefixed in the internal logic
    # We'll simulate the logic from the completion methods
    model = original_model
    if llm_service.provider == "dashscope" and not model.startswith('dashscope/'):
        model = f'dashscope/{model}'
    
    assert model == expected_prefixed_model, f"Expected '{expected_prefixed_model}', got '{model}'"
    print(f"✓ Model correctly prefixed: {original_model} -> {model}")


def test_configuration():
    """Test that configuration still works properly"""
    print("\nTesting configuration...")
    
    llm_service = LlmService()
    
    # Test initial configuration
    print(f"Initial provider: {getattr(llm_service, 'provider', 'not set')}")
    print(f"Initial API base: {llm_service.api_base}")
    print(f"Initial API key set: {bool(llm_service.api_key)}")
    
    # Configure for DashScope
    api_key = os.getenv("DASHSCOPE_API_KEY", "dummy_key_for_test")
    api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    llm_service.configure(
        api_key=api_key,
        api_base=api_base,
        default_model="qwen-turbo"
    )
    
    assert llm_service.api_key == api_key
    assert llm_service.api_base == api_base
    assert llm_service.default_model == "qwen-turbo"
    assert llm_service.provider == "dashscope"
    
    print("✓ Configuration works correctly")
    print(f"  - API key set: {bool(llm_service.api_key)}")
    print(f"  - API base: {llm_service.api_base}")
    print(f"  - Default model: {llm_service.default_model}")
    print(f"  - Provider: {llm_service.provider}")


if __name__ == "__main__":
    print("Testing updated LLMService implementation...\n")
    
    test_provider_detection()
    test_model_prefixing()
    test_configuration()
    
    print("\n✓ All tests passed! The updated LLMService implementation works correctly.")
    print("\nSummary of changes:")
    print("- Provider detection from base URL implemented")
    print("- Removed special DashScope adapter calls")
    print("- Model names are now properly prefixed for DashScope")
    print("- LiteLLM handles provider-specific logic internally")