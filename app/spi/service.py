"""
Service Plugin Interface

Defines the base service interface for AI generation capabilities.
Service plugins implement this interface to provide various AI services
like ComfyUI, Bailian, Gemini, etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path

from utils.progress_utils import Progress


@dataclass
class ServiceCapability:
    """Represents a single capability that a service provides"""
    capability_id: str  # e.g., "text2image", "image2video"
    display_name: str
    description: str
    input_schema: Dict[str, Any]  # Schema defining required input parameters
    output_schema: Dict[str, Any]  # Schema defining expected output structure
    requires_prompt: bool = False
    requires_input_media: bool = False


@dataclass
class ConfigField:
    """Individual configuration field definition"""
    name: str
    label: str
    type: str  # text, number, boolean, select, password
    default: Any
    description: str = ""
    required: bool = False
    validation: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, str]]] = None


@dataclass
class ConfigGroup:
    """Represents a group of related configuration fields"""
    name: str
    label: str
    fields: List[ConfigField]


@dataclass
class ConfigSchema:
    """Defines the configuration structure for a service plugin"""
    groups: List[ConfigGroup]
    version: str = "1.0.0"


@dataclass
class ServiceResult:
    """Result object returned from capability execution"""
    status: str  # success, error, pending
    output_files: List[str]  # Paths to generated output files
    metadata: Dict[str, Any]  # Additional result metadata
    error_message: str = ""
    progress: float = 0.0  # Progress percentage for long-running tasks

    def get_image_path(self) -> Optional[str]:
        """Get the first image file from output files"""
        for file_path in self.output_files:
            if file_path.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                return file_path
        return None

    def get_video_path(self) -> Optional[str]:
        """Get the first video file from output files"""
        for file_path in self.output_files:
            if file_path.endswith(('.mp4', '.mov', '.avi')):
                return file_path
        return None


class BaseService(ABC):
    """
    Base abstract class for service plugins.
    
    All service implementations must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self):
        """Initialize the service"""
        pass

    @classmethod
    @abstractmethod
    def get_service_name(cls) -> str:
        """Returns unique service identifier (e.g., 'comfyui', 'bailian')"""
        pass

    @classmethod
    @abstractmethod
    def get_service_display_name(cls) -> str:
        """Returns human-readable service name (e.g., 'ComfyUI', 'Bailian')"""
        pass

    @classmethod
    @abstractmethod
    def get_service_icon(cls) -> str:
        """Returns icon unicode character for UI display"""
        pass

    @classmethod
    @abstractmethod
    def get_capabilities(cls) -> List[ServiceCapability]:
        """Returns list of supported capabilities"""
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> ConfigSchema:
        """Returns configuration schema definition"""
        pass

    @classmethod
    def get_config_path(cls) -> str:
        """
        Returns path to plugin's YAML config file.
        Default implementation assumes config file is in same directory as service.
        """
        module_path = Path(__file__).parent.parent / "plugins" / "services" / cls.get_service_name()
        config_file = module_path / f"{cls.get_service_name()}_config.yaml"
        return str(config_file)

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """Loads and returns current configuration"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validates configuration against schema"""
        pass

    @abstractmethod
    async def execute_capability(
        self,
        capability_id: str,
        parameters: Dict[str, Any],
        progress: Optional[Progress] = None
    ) -> ServiceResult:
        """
        Executes a specific capability with given parameters.
        
        Args:
            capability_id: The capability to execute (e.g., "text2image")
            parameters: Input parameters for the capability
            progress: Optional progress callback for long-running tasks
            
        Returns:
            ServiceResult with execution results
        """
        pass

    @classmethod
    def get_service_version(cls) -> str:
        """Returns service version (optional, defaults to 1.0.0)"""
        return "1.0.0"

    @classmethod
    def get_service_description(cls) -> str:
        """Returns brief service description (optional)"""
        return ""
