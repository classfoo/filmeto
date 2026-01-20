"""
LLM Service Module

Implements the LlmService class to wrap LiteLLM functionality and integrate with
the system settings service to manage AI model configurations.
"""
import os
from typing import Optional, Dict, Any, AsyncIterator
import litellm
from app.data.settings import Settings
from utils.i18n_utils import translation_manager


class LlmService:
    """
    Service class that wraps LiteLLM functionality and integrates with system settings.

    This class is responsible for:
    - Retrieving OpenAI settings from the system settings service
    - Initializing LiteLLM with the retrieved settings
    - Providing a clean interface to LiteLLM's functionality
    - Supporting special handling for different AI service providers like DashScope
    """
    
    def __init__(self, workspace=None):
        """
        Initialize the LlmService.

        Args:
            workspace: Workspace instance containing settings. If not provided, will use environment variables.
        """
        self.workspace = workspace
        self.settings = getattr(workspace, 'settings', None) if workspace else None
        self.api_key = None
        self.api_base = None
        self.default_model = 'gpt-4o-mini'
        self.temperature = 0.7
        self.language_prompts = {
            'zh_CN': '请使用中文回答。',
            'en_US': 'Please respond in English.',
            'ja_JP': '日本語で返答してください。',
            'ko_KR': '한국어로 대답해 주세요.',
            'fr_FR': 'Veuillez répondre en français.',
            'de_DE': 'Bitte antworten Sie auf Deutsch.',
            'es_ES': 'Por favor, responda en español.'
        }

        # Initialize the service
        self._initialize_from_settings()
    
    def _detect_provider_from_base_url(self, base_url: str) -> str:
        """Detect the provider type from the base URL."""
        if not base_url:
            return "openai"

        if 'dashscope.aliyuncs.com' in base_url:
            return "dashscope"
        elif '.openai.azure.com' in base_url or 'openai.azure.com' in base_url:
            return "azure"
        elif 'anthropic' in base_url:
            return "anthropic"
        elif 'cohere' in base_url:
            return "cohere"
        elif 'replicate' in base_url:
            return "replicate"
        else:
            # Default to openai for custom endpoints that are OpenAI-compatible
            return "openai"

    def _initialize_from_settings(self):
        """Initialize the service by retrieving settings from the system settings service."""
        if self.settings:
            # Retrieve OpenAI settings from the system settings service
            self.api_key = (self.settings.get('ai_services.openai_api_key') or
                           self.settings.get('ai_services.openai_ak_sk') or
                           os.getenv('OPENAI_API_KEY') or
                           os.getenv('DASHSCOPE_API_KEY'))
            self.api_base = self.settings.get('ai_services.openai_host', os.getenv('OPENAI_BASE_URL'))
            self.default_model = self.settings.get('ai_services.default_model', 'gpt-4o-mini')

            # Detect provider from base URL
            self.provider = self._detect_provider_from_base_url(self.api_base)

            # Set LiteLLM configurations
            if self.api_key:
                litellm.api_key = self.api_key
            if self.api_base:
                # Set the API base for the detected provider
                if self.provider == "dashscope":
                    # For DashScope, use the compatible mode endpoint with proper provider prefix
                    litellm.custom_api_base = self.api_base
                    # Set headers for DashScope if needed
                    litellm.default_headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                else:
                    litellm.api_base = self.api_base
        else:
            # Fallback to environment variables if no settings service is provided
            self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
            self.api_base = os.getenv('OPENAI_BASE_URL', os.getenv('OPENAI_HOST'))
            self.default_model = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')

            # Detect provider from base URL
            self.provider = self._detect_provider_from_base_url(self.api_base)

            # Set LiteLLM configurations
            if self.api_key:
                litellm.api_key = self.api_key
            if self.api_base:
                # Set the API base for the detected provider
                if self.provider == "dashscope":
                    # For DashScope, use the compatible mode endpoint with proper provider prefix
                    litellm.custom_api_base = self.api_base
                    # Set headers for DashScope if needed
                    litellm.default_headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                else:
                    litellm.api_base = self.api_base

    def get_current_language(self) -> str:
        """
        Get the current language from the translation manager.

        Returns:
            Current language code (e.g., 'zh_CN', 'en_US')
        """
        return translation_manager.get_current_language()

    def _inject_language_prompt(self, messages: list) -> list:
        """
        Inject language instruction as system prompt if not already present.

        Args:
            messages: List of messages to potentially modify

        Returns:
            Modified list of messages with language prompt injected if needed
        """
        if not messages:
            return messages

        # Get current language
        current_language = self.get_current_language()
        language_instruction = self.language_prompts.get(current_language, '')

        if not language_instruction:
            # No language instruction defined for this language
            return messages

        # Check if there's already a system message
        has_system_message = any(msg.get('role') == 'system' for msg in messages)

        if has_system_message:
            # If there's already a system message, we'll append our language instruction
            # to the first system message we find
            for msg in messages:
                if msg.get('role') == 'system':
                    current_content = msg.get('content', '')
                    if language_instruction not in current_content:
                        msg['content'] = f"{current_content}\n\n{language_instruction}".strip()
                    break
        else:
            # If there's no system message, insert one at the beginning
            messages = [
                {"role": "system", "content": language_instruction}
            ] + messages

        return messages
    
    def configure(self, api_key: Optional[str] = None, api_base: Optional[str] = None,
                  default_model: Optional[str] = None, temperature: Optional[float] = None):
        """
        Configure the LLM service with specific parameters.

        Args:
            api_key: OpenAI API key
            api_base: OpenAI API base URL
            default_model: Default model to use
            temperature: Temperature setting for the model
        """
        if api_key:
            self.api_key = api_key
            litellm.api_key = api_key

        if api_base:
            self.api_base = api_base
            # Update provider based on the new API base
            self.provider = self._detect_provider_from_base_url(self.api_base)

            # Set the API base for the detected provider
            if self.provider == "dashscope":
                # For DashScope, use the compatible mode endpoint with proper provider prefix
                litellm.custom_api_base = self.api_base
                # Set headers for DashScope if needed
                litellm.default_headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"} if self.api_key else {"Content-Type": "application/json"}
            else:
                litellm.api_base = self.api_base

        if default_model:
            self.default_model = default_model

        if temperature is not None:
            self.temperature = temperature
    
    async def acompletion(self,
                         model: Optional[str] = None,
                         messages: Optional[list] = None,
                         temperature: Optional[float] = None,
                         stream: bool = False,
                         **kwargs) -> Any:
        """
        Async completion method that wraps LiteLLM's acompletion function.

        Args:
            model: Model to use for completion (defaults to self.default_model)
            messages: List of messages for the conversation
            temperature: Temperature setting (defaults to self.temperature)
            stream: Whether to stream the response
            **kwargs: Additional arguments to pass to LiteLLM

        Returns:
            Completion response from LiteLLM
        """
        # Use defaults if not provided
        if model is None:
            model = self.default_model
        if temperature is None:
            temperature = self.temperature
        if messages is None:
            messages = []

        # Inject language prompt based on current language setting
        messages = self._inject_language_prompt(messages)

        # Add any additional configuration from settings
        kwargs.setdefault('temperature', temperature)

        # If using DashScope provider, ensure model name is prefixed with 'dashscope/'
        if self.provider == "dashscope" and not model.startswith('dashscope/'):
            model = f'dashscope/{model}'

        # Call LiteLLM's acompletion normally - it will handle provider-specific logic internally
        return await litellm.acompletion(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )
    
    def completion(self,
                   model: Optional[str] = None,
                   messages: Optional[list] = None,
                   temperature: Optional[float] = None,
                   **kwargs) -> Any:
        """
        Sync completion method that wraps LiteLLM's completion function.

        Args:
            model: Model to use for completion (defaults to self.default_model)
            messages: List of messages for the conversation
            temperature: Temperature setting (defaults to self.temperature)
            **kwargs: Additional arguments to pass to LiteLLM

        Returns:
            Completion response from LiteLLM
        """
        # Use defaults if not provided
        if model is None:
            model = self.default_model
        if temperature is None:
            temperature = self.temperature
        if messages is None:
            messages = []

        # Inject language prompt based on current language setting
        messages = self._inject_language_prompt(messages)

        # Add any additional configuration from settings
        kwargs.setdefault('temperature', temperature)

        # If using DashScope provider, ensure model name is prefixed with 'dashscope/'
        if self.provider == "dashscope" and not model.startswith('dashscope/'):
            model = f'dashscope/{model}'

        # Call LiteLLM's completion normally - it will handle provider-specific logic internally
        return litellm.completion(
            model=model,
            messages=messages,
            **kwargs
        )
    
    async def aembedding(self,
                        model: str,
                        input_text: str) -> Any:
        """
        Async embedding method that wraps LiteLLM's aembedding function.

        Args:
            model: Model to use for embeddings
            input_text: Text to generate embeddings for

        Returns:
            Embedding response from LiteLLM
        """
        # If using DashScope provider, ensure model name is prefixed with 'dashscope/'
        if self.provider == "dashscope" and not model.startswith('dashscope/'):
            model = f'dashscope/{model}'

        # Call LiteLLM's aembedding normally - it will handle provider-specific logic internally
        return await litellm.aembedding(
            model=model,
            input=input_text
        )

    def embedding(self,
                  model: str,
                  input_text: str) -> Any:
        """
        Sync embedding method that wraps LiteLLM's embedding function.

        Args:
            model: Model to use for embeddings
            input_text: Text to generate embeddings for

        Returns:
            Embedding response from LiteLLM
        """
        # If using DashScope provider, ensure model name is prefixed with 'dashscope/'
        if self.provider == "dashscope" and not model.startswith('dashscope/'):
            model = f'dashscope/{model}'

        # Call LiteLLM's embedding normally - it will handle provider-specific logic internally
        return litellm.embedding(
            model=model,
            input=input_text
        )
    
    async def atranscription(self,
                            model: str,
                            audio_file_path: str) -> Any:
        """
        Async transcription method that wraps LiteLLM's atranscription function.

        Args:
            model: Model to use for transcription
            audio_file_path: Path to the audio file to transcribe

        Returns:
            Transcription response from LiteLLM
        """
        # If using DashScope provider, ensure model name is prefixed with 'dashscope/'
        if self.provider == "dashscope" and not model.startswith('dashscope/'):
            model = f'dashscope/{model}'

        return await litellm.atranscription(
            model=model,
            file=audio_file_path
        )

    def transcription(self,
                      model: str,
                      audio_file_path: str) -> Any:
        """
        Sync transcription method that wraps LiteLLM's transcription function.

        Args:
            model: Model to use for transcription
            audio_file_path: Path to the audio file to transcribe

        Returns:
            Transcription response from LiteLLM
        """
        # If using DashScope provider, ensure model name is prefixed with 'dashscope/'
        if self.provider == "dashscope" and not model.startswith('dashscope/'):
            model = f'dashscope/{model}'

        return litellm.transcription(
            model=model,
            file=audio_file_path
        )
    
    def list_models(self) -> list:
        """
        List available models from LiteLLM.
        
        Returns:
            List of available models
        """
        return litellm.model_list
    
    def validate_config(self) -> bool:
        """
        Validate if the LLM service is properly configured.

        Returns:
            True if properly configured, False otherwise
        """
        # Check if either API key is set OR API base is set (for custom endpoints)
        # This allows for services that might use different authentication methods
        return bool(self.api_key) or bool(self.api_base)
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get the current configuration of the LLM service.
        
        Returns:
            Dictionary containing current configuration
        """
        return {
            'api_key_set': bool(self.api_key),
            'api_base': self.api_base,
            'default_model': self.default_model,
            'temperature': self.temperature
        }