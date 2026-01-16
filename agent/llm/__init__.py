"""
LLM Service Package for Filmeto Agent

This package contains the LlmService class which wraps LiteLLM functionality
and integrates with the system settings service to manage AI model configurations.
"""
from .llm_service import LlmService
from .dashscope_adapter import (
    async_completion_with_dashscope,
    sync_completion_with_dashscope,
    async_embedding_with_dashscope,
    sync_embedding_with_dashscope,
    map_dashscope_model
)

__all__ = [
    "LlmService",
    "async_completion_with_dashscope",
    "sync_completion_with_dashscope",
    "async_embedding_with_dashscope",
    "sync_embedding_with_dashscope",
    "map_dashscope_model"
]