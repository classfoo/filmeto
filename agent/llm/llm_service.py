"""
LLM Service Module

Implements the LlmService class to wrap LiteLLM functionality and integrate with
the system settings service to manage AI model configurations.
"""
import os
from typing import Optional, Dict, Any, AsyncIterator
import litellm
from app.data.settings import Settings


class LlmService:
    """
    Service class that wraps LiteLLM functionality and integrates with system settings.
    
    This class is responsible for:
    - Retrieving OpenAI settings from the system settings service
    - Initializing LiteLLM with the retrieved settings
    - Providing a clean interface to LiteLLM's functionality
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

        # Initialize the service
        self._initialize_from_settings()
    
    def _initialize_from_settings(self):
        """Initialize the service by retrieving settings from the system settings service."""
        if self.settings:
            # Retrieve OpenAI settings from the system settings service
            self.api_key = self.settings.get('ai_services.openai_api_key', os.getenv('OPENAI_API_KEY'))
            self.api_base = self.settings.get('ai_services.openai_host', os.getenv('OPENAI_BASE_URL'))
            self.default_model = self.settings.get('ai_services.default_model', 'gpt-4o-mini')
            
            # Set LiteLLM configurations
            if self.api_key:
                litellm.api_key = self.api_key
            if self.api_base:
                litellm.api_base = self.api_base
        else:
            # Fallback to environment variables if no settings service is provided
            self.api_key = os.getenv('OPENAI_API_KEY')
            self.api_base = os.getenv('OPENAI_BASE_URL', os.getenv('OPENAI_HOST'))
            self.default_model = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
            
            # Set LiteLLM configurations
            if self.api_key:
                litellm.api_key = self.api_key
            if self.api_base:
                litellm.api_base = self.api_base
    
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
            litellm.api_base = api_base
            
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
        
        # Add any additional configuration from settings
        kwargs.setdefault('temperature', temperature)
        
        # Call LiteLLM's acompletion
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
        
        # Add any additional configuration from settings
        kwargs.setdefault('temperature', temperature)
        
        # Call LiteLLM's completion
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
        return bool(self.api_key)
    
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