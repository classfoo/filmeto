"""
Bailian Service Plugin

Service implementation for Alibaba Bailian (Qwen) API integration.
Provides text-to-image generation capabilities.
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.spi.service import (
    BaseService, ServiceCapability, ConfigSchema, ConfigGroup, ConfigField,
    ServiceResult
)
from utils.progress_utils import Progress
from utils.yaml_utils import load_yaml


class BailianService(BaseService):
    """Bailian (Qwen) service implementation"""

    def __init__(self):
        super().__init__()
        self._config = None

    @classmethod
    def get_service_name(cls) -> str:
        return "bailian"

    @classmethod
    def get_service_display_name(cls) -> str:
        return "Bailian"

    @classmethod
    def get_service_icon(cls) -> str:
        return "\ue60c"  # Using an icon from iconfont

    @classmethod
    def get_capabilities(cls) -> List[ServiceCapability]:
        return [
            ServiceCapability(
                capability_id="text2image",
                display_name="Text to Image",
                description="Generate images from text prompts using Qwen models",
                input_schema={"prompt": "string", "save_dir": "string"},
                output_schema={"image_path": "string"},
                requires_prompt=True,
                requires_input_media=False
            )
        ]

    @classmethod
    def get_config_schema(cls) -> ConfigSchema:
        return ConfigSchema(
            version="1.0.0",
            groups=[
                ConfigGroup(
                    name="api",
                    label="API Settings",
                    fields=[
                        ConfigField(
                            name="api_endpoint",
                            label="API Endpoint",
                            type="text",
                            default="https://dashscope.aliyuncs.com/api/v1",
                            required=True,
                            description="Bailian API endpoint URL",
                            validation={"pattern": r"^https?://.*"}
                        ),
                        ConfigField(
                            name="api_key",
                            label="API Key",
                            type="password",
                            default="",
                            required=True,
                            description="Bailian API key for authentication"
                        )
                    ]
                ),
                ConfigGroup(
                    name="model",
                    label="Model Selection",
                    fields=[
                        ConfigField(
                            name="model_name",
                            label="Model Name",
                            type="select",
                            default="qwen-vl-plus",
                            description="Qwen model to use for generation",
                            options=[
                                {"value": "qwen-vl-plus", "label": "Qwen VL Plus"},
                                {"value": "qwen-vl-max", "label": "Qwen VL Max"}
                            ]
                        )
                    ]
                ),
                ConfigGroup(
                    name="generation",
                    label="Generation Parameters",
                    fields=[
                        ConfigField(
                            name="image_size",
                            label="Image Size",
                            type="select",
                            default="1024x1024",
                            description="Output image resolution",
                            options=[
                                {"value": "512x512", "label": "512 × 512"},
                                {"value": "1024x1024", "label": "1024 × 1024"},
                                {"value": "2048x2048", "label": "2048 × 2048"}
                            ]
                        ),
                        ConfigField(
                            name="quality",
                            label="Quality",
                            type="select",
                            default="standard",
                            description="Image quality level",
                            options=[
                                {"value": "draft", "label": "Draft"},
                                {"value": "standard", "label": "Standard"},
                                {"value": "hd", "label": "HD"}
                            ]
                        ),
                        ConfigField(
                            name="steps",
                            label="Generation Steps",
                            type="number",
                            default=20,
                            description="Number of generation steps",
                            validation={"min": 1, "max": 50}
                        )
                    ]
                )
            ]
        )

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if self._config is not None:
            return self._config

        config_path = self.get_config_path()
        try:
            yaml_data = load_yaml(config_path)
            # Parse into simple dict structure
            config = {}
            for group_data in yaml_data.get('groups', []):
                group_name = group_data.get('name')
                config[group_name] = {}
                for field_data in group_data.get('fields', []):
                    field_name = field_data.get('name')
                    config[group_name][field_name] = field_data.get('default')
            
            self._config = config
            return config

        except Exception as e:
            print(f"❌ Failed to load Bailian config: {e}")
            return {}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration"""
        # Basic validation - check required fields
        if 'api' not in config:
            return False
        
        api = config['api']
        if 'api_endpoint' not in api or 'api_key' not in api:
            return False

        # Check API key is not empty
        if not api.get('api_key'):
            print("⚠️ Bailian API key is required")
            return False

        return True

    async def execute_capability(
        self,
        capability_id: str,
        parameters: Dict[str, Any],
        progress: Optional[Progress] = None
    ) -> ServiceResult:
        """Execute a capability"""
        # Load config if not already loaded
        if self._config is None:
            self.load_config()

        # Route to appropriate handler
        if capability_id == "text2image":
            return await self._execute_text2image(parameters, progress)
        else:
            return ServiceResult(
                status="error",
                output_files=[],
                metadata={},
                error_message=f"Unknown capability: {capability_id}"
            )

    async def _execute_text2image(self, parameters: Dict[str, Any], progress: Optional[Progress]) -> ServiceResult:
        """Execute text-to-image generation using Bailian API"""
        try:
            prompt = parameters.get('prompt', '')
            save_dir = parameters.get('save_dir', '')

            # Get config values
            api_config = self._config.get('api', {})
            model_config = self._config.get('model', {})
            gen_config = self._config.get('generation', {})

            api_endpoint = api_config.get('api_endpoint', '')
            api_key = api_config.get('api_key', '')
            model_name = model_config.get('model_name', 'qwen-vl-plus')

            if not api_key:
                return ServiceResult(
                    status="error",
                    output_files=[],
                    metadata={},
                    error_message="API key not configured"
                )

            # For now, this is a placeholder implementation
            # In a real implementation, you would use the dashscope SDK
            # to make the API call
            
            # Example placeholder:
            # from dashscope import ImageSynthesis
            # response = ImageSynthesis.call(
            #     model=model_name,
            #     prompt=prompt,
            #     size=gen_config.get('image_size', '1024x1024'),
            #     quality=gen_config.get('quality', 'standard'),
            #     steps=gen_config.get('steps', 20),
            #     api_key=api_key
            # )
            
            # For demonstration, return a placeholder result
            print(f"🔄 Bailian text2image: {prompt}")
            print(f"   Model: {model_name}")
            print(f"   Size: {gen_config.get('image_size', '1024x1024')}")
            
            return ServiceResult(
                status="error",
                output_files=[],
                metadata={},
                error_message="Bailian service not fully implemented - placeholder only"
            )

        except Exception as e:
            return ServiceResult(
                status="error",
                output_files=[],
                metadata={},
                error_message=str(e)
            )

    @classmethod
    def get_service_version(cls) -> str:
        return "1.0.0"

    @classmethod
    def get_service_description(cls) -> str:
        return "Alibaba Bailian (Qwen) API integration for AI image generation"
