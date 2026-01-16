"""
DashScope Adapter Module

This module provides a specialized adapter for Alibaba Cloud DashScope API
to handle any specific requirements or differences from the standard OpenAI API.
"""
import os
import litellm
from typing import Optional, Dict, Any, AsyncIterator
from litellm import acompletion, completion, aembedding, embedding, atranscription, transcription


def setup_dashscope_config(api_key: str, api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
    """
    Setup configuration for DashScope API compatibility.
    
    Args:
        api_key: The API key for DashScope
        api_base: The base URL for DashScope API (default is compatible mode)
    """
    # Set the API key for DashScope
    litellm.api_key = api_key
    
    # Set the custom API base for DashScope
    litellm.custom_api_base = api_base
    
    # Set headers required by DashScope if needed
    litellm.default_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


async def async_completion_with_dashscope(
    model: str,
    messages: list,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    **kwargs
) -> Any:
    """
    Async completion function specifically adapted for DashScope API.

    Args:
        model: The model to use for completion
        messages: List of messages for the conversation
        temperature: Temperature setting for the model
        api_key: DashScope API key (optional, can be set globally)
        api_base: DashScope API base URL (optional, defaults to compatible mode)
        **kwargs: Additional arguments to pass to the API

    Returns:
        Completion response from DashScope
    """
    # If API key is provided, set it up temporarily
    if api_key:
        setup_dashscope_config(api_key, api_base)

    # Call LiteLLM's acompletion with DashScope-specific model mapping if needed
    # Some DashScope models might need to be mapped to their compatible names
    mapped_model = map_dashscope_model(model)

    # Prepare the arguments for LiteLLM
    args = {
        "model": mapped_model,
        "messages": messages
    }

    if temperature is not None:
        args["temperature"] = temperature

    # Add any additional arguments
    args.update(kwargs)

    return await acompletion(**args)


def sync_completion_with_dashscope(
    model: str,
    messages: list,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    **kwargs
) -> Any:
    """
    Sync completion function specifically adapted for DashScope API.

    Args:
        model: The model to use for completion
        messages: List of messages for the conversation
        temperature: Temperature setting for the model
        api_key: DashScope API key (optional, can be set globally)
        api_base: DashScope API base URL (optional, defaults to compatible mode)
        **kwargs: Additional arguments to pass to the API

    Returns:
        Completion response from DashScope
    """
    # If API key is provided, set it up temporarily
    if api_key:
        setup_dashscope_config(api_key, api_base)

    # Call LiteLLM's completion with DashScope-specific model mapping if needed
    mapped_model = map_dashscope_model(model)

    # Prepare the arguments for LiteLLM
    args = {
        "model": mapped_model,
        "messages": messages
    }

    if temperature is not None:
        args["temperature"] = temperature

    # Add any additional arguments
    args.update(kwargs)

    return completion(**args)


def map_dashscope_model(model: str) -> str:
    """
    Map standard model names to DashScope-compatible model names if needed.

    Args:
        model: The original model name

    Returns:
        The DashScope-compatible model name
    """
    # Common mappings for DashScope models
    model_mappings = {
        # Standard OpenAI models to DashScope equivalents
        "gpt-4": "qwen-max",  # Using Qwen as equivalent to GPT-4
        "gpt-4o-mini": "qwen-plus",  # Using Qwen+ as equivalent to GPT-4o-mini
        "gpt-3.5-turbo": "qwen-turbo",  # Using Qwen-Turbo as equivalent to GPT-3.5
        # Add more mappings as needed
    }

    # Get the mapped model name
    mapped_model = model_mappings.get(model, model)

    # Prepend 'dashscope/' prefix for LiteLLM to recognize the provider
    if not mapped_model.startswith('dashscope/'):
        mapped_model = f'dashscope/{mapped_model}'

    return mapped_model


async def async_embedding_with_dashscope(
    model: str,
    input_text: str,
    api_key: Optional[str] = None,
    api_base: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
) -> Any:
    """
    Async embedding function specifically adapted for DashScope API.
    
    Args:
        model: The model to use for embeddings
        input_text: Text to generate embeddings for
        api_key: DashScope API key (optional, can be set globally)
        api_base: DashScope API base URL (optional, defaults to compatible mode)
        
    Returns:
        Embedding response from DashScope
    """
    if api_key:
        setup_dashscope_config(api_key, api_base)
    
    # Map model name if needed
    mapped_model = map_dashscope_model(model)
    
    return await aembedding(
        model=mapped_model,
        input=input_text
    )


def sync_embedding_with_dashscope(
    model: str,
    input_text: str,
    api_key: Optional[str] = None,
    api_base: Optional[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
) -> Any:
    """
    Sync embedding function specifically adapted for DashScope API.
    
    Args:
        model: The model to use for embeddings
        input_text: Text to generate embeddings for
        api_key: DashScope API key (optional, can be set globally)
        api_base: DashScope API base URL (optional, defaults to compatible mode)
        
    Returns:
        Embedding response from DashScope
    """
    if api_key:
        setup_dashscope_config(api_key, api_base)
    
    # Map model name if needed
    mapped_model = map_dashscope_model(model)
    
    return embedding(
        model=mapped_model,
        input=input_text
    )