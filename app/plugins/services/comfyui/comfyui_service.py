"""
ComfyUI Service Plugin

Service implementation for ComfyUI integration.
Provides text-to-image, image editing, and image-to-video capabilities.
"""

import os
import json
import random
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.spi.service import (
    BaseService, ServiceCapability, ConfigSchema, ConfigGroup, ConfigField,
    ServiceResult
)
from utils.comfy_ui_utils import ComfyUIClient
from utils.progress_utils import Progress
from utils.yaml_utils import load_yaml


class ComfyUIService(BaseService):
    """ComfyUI service implementation"""

    def __init__(self):
        super().__init__()
        self._config = None

    @classmethod
    def get_service_name(cls) -> str:
        return "comfyui"

    @classmethod
    def get_service_display_name(cls) -> str:
        return "ComfyUI"

    @classmethod
    def get_service_icon(cls) -> str:
        return "\ue60b"  # Using text2img icon from iconfont

    @classmethod
    def get_capabilities(cls) -> List[ServiceCapability]:
        return [
            ServiceCapability(
                capability_id="text2image",
                display_name="Text to Image",
                description="Generate images from text prompts",
                input_schema={"prompt": "string", "save_dir": "string"},
                output_schema={"image_path": "string"},
                requires_prompt=True,
                requires_input_media=False
            ),
            ServiceCapability(
                capability_id="image_edit",
                display_name="Image Editing",
                description="Edit images based on text prompts",
                input_schema={"prompt": "string", "input_image": "string", "save_dir": "string"},
                output_schema={"image_path": "string"},
                requires_prompt=True,
                requires_input_media=True
            ),
            ServiceCapability(
                capability_id="image2video",
                display_name="Image to Video",
                description="Generate videos from images with text prompts",
                input_schema={"prompt": "string", "input_image": "string", "save_dir": "string"},
                output_schema={"video_path": "string"},
                requires_prompt=True,
                requires_input_media=True
            )
        ]

    @classmethod
    def get_config_schema(cls) -> ConfigSchema:
        return ConfigSchema(
            version="1.0.0",
            groups=[
                ConfigGroup(
                    name="connection",
                    label="Connection Settings",
                    fields=[
                        ConfigField(
                            name="server_url",
                            label="Server URL",
                            type="text",
                            default="http://192.168.1.100",
                            required=True,
                            description="ComfyUI server address",
                            validation={"pattern": r"^https?://.*"}
                        ),
                        ConfigField(
                            name="port",
                            label="Port",
                            type="number",
                            default=3000,
                            required=True,
                            description="ComfyUI server port",
                            validation={"min": 1, "max": 65535}
                        ),
                        ConfigField(
                            name="timeout",
                            label="Timeout (seconds)",
                            type="number",
                            default=120,
                            description="Request timeout in seconds",
                            validation={"min": 10, "max": 600}
                        ),
                        ConfigField(
                            name="enable_ssl",
                            label="Enable SSL",
                            type="boolean",
                            default=False,
                            description="Use HTTPS connection"
                        )
                    ]
                ),
                ConfigGroup(
                    name="authentication",
                    label="Authentication",
                    fields=[
                        ConfigField(
                            name="api_key",
                            label="API Key",
                            type="password",
                            default="",
                            description="Optional API key for authentication"
                        )
                    ]
                ),
                ConfigGroup(
                    name="workflows",
                    label="Workflow Settings",
                    fields=[
                        ConfigField(
                            name="text2image_workflow",
                            label="Text to Image Workflow",
                            type="text",
                            default="workflows/text_to_image_qwen_image.json",
                            description="Path to text-to-image workflow JSON file"
                        ),
                        ConfigField(
                            name="image_edit_workflow",
                            label="Image Edit Workflow",
                            type="text",
                            default="workflows/qwen_image_edit.json",
                            description="Path to image editing workflow JSON file"
                        ),
                        ConfigField(
                            name="image2video_workflow",
                            label="Image to Video Workflow",
                            type="text",
                            default="workflows/image_to_video_wan_2_2_kj.json",
                            description="Path to image-to-video workflow JSON file"
                        )
                    ]
                ),
                ConfigGroup(
                    name="performance",
                    label="Performance",
                    fields=[
                        ConfigField(
                            name="max_concurrent_jobs",
                            label="Max Concurrent Jobs",
                            type="number",
                            default=1,
                            description="Maximum number of concurrent jobs",
                            validation={"min": 1, "max": 10}
                        ),
                        ConfigField(
                            name="queue_timeout",
                            label="Queue Timeout (seconds)",
                            type="number",
                            default=3200,
                            description="Maximum time to wait in queue",
                            validation={"min": 60, "max": 7200}
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
            print(f"❌ Failed to load ComfyUI config: {e}")
            return {}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration"""
        # Basic validation - check required fields
        if 'connection' not in config:
            return False
        
        conn = config['connection']
        if 'server_url' not in conn or 'port' not in conn:
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
        elif capability_id == "image_edit":
            return await self._execute_image_edit(parameters, progress)
        elif capability_id == "image2video":
            return await self._execute_image2video(parameters, progress)
        else:
            return ServiceResult(
                status="error",
                output_files=[],
                metadata={},
                error_message=f"Unknown capability: {capability_id}"
            )

    async def _execute_text2image(self, parameters: Dict[str, Any], progress: Optional[Progress]) -> ServiceResult:
        """Execute text-to-image generation"""
        try:
            prompt = parameters.get('prompt', '')
            save_dir = parameters.get('save_dir', '')

            # Load workflow
            workflow_path = self._get_workflow_path('text2image_workflow')
            workflow = self._load_workflow(workflow_path, prompt)

            # Get server URL
            base_url = self._get_base_url()

            # Create client and run workflow
            client = ComfyUIClient(base_url=base_url)
            result = await client.run_workflow(
                workflow_json=workflow,
                output_node_ids=["60"],
                progress=progress,
                save_dir=save_dir,
                timeout=self._config.get('connection', {}).get('timeout', 120)
            )

            if result["status"] == "success":
                return ServiceResult(
                    status="success",
                    output_files=result["output_files"],
                    metadata=result,
                    progress=100.0
                )
            else:
                return ServiceResult(
                    status="error",
                    output_files=[],
                    metadata=result,
                    error_message=result.get("error", "Unknown error")
                )

        except Exception as e:
            return ServiceResult(
                status="error",
                output_files=[],
                metadata={},
                error_message=str(e)
            )

    async def _execute_image_edit(self, parameters: Dict[str, Any], progress: Optional[Progress]) -> ServiceResult:
        """Execute image editing"""
        try:
            prompt = parameters.get('prompt', '')
            input_image = parameters.get('input_image', '')
            save_dir = parameters.get('save_dir', '')

            # Upload image first
            base_url = self._get_base_url()
            client = ComfyUIClient(base_url=base_url)
            
            await client.connect()
            upload_result = await client.upload_image(input_image)
            await client.close()

            if not upload_result or 'name' not in upload_result:
                return ServiceResult(
                    status="error",
                    output_files=[],
                    metadata={},
                    error_message="Failed to upload image"
                )

            # Load workflow
            workflow_path = self._get_workflow_path('image_edit_workflow')
            workflow_content = self._load_workflow_content(workflow_path)
            workflow_content = workflow_content.replace('$inputImage', upload_result['name'])
            workflow_content = workflow_content.replace('$prompt', prompt)
            workflow_content = workflow_content.replace('$seed', str(random.getrandbits(32)))
            workflow = json.loads(workflow_content)

            # Run workflow
            result = await client.run_workflow(
                workflow_json=workflow,
                output_node_ids=["60"],
                progress=progress,
                save_dir=save_dir,
                timeout=self._config.get('connection', {}).get('timeout', 120)
            )

            if result["status"] == "success":
                return ServiceResult(
                    status="success",
                    output_files=result["output_files"],
                    metadata=result,
                    progress=100.0
                )
            else:
                return ServiceResult(
                    status="error",
                    output_files=[],
                    metadata=result,
                    error_message=result.get("error", "Unknown error")
                )

        except Exception as e:
            return ServiceResult(
                status="error",
                output_files=[],
                metadata={},
                error_message=str(e)
            )

    async def _execute_image2video(self, parameters: Dict[str, Any], progress: Optional[Progress]) -> ServiceResult:
        """Execute image-to-video generation"""
        try:
            prompt = parameters.get('prompt', '')
            input_image = parameters.get('input_image', '')
            save_dir = parameters.get('save_dir', '')

            # Upload image first
            base_url = self._get_base_url()
            client = ComfyUIClient(base_url=base_url)
            
            await client.connect()
            upload_result = await client.upload_image(input_image)
            await client.close()

            if not upload_result or 'name' not in upload_result:
                return ServiceResult(
                    status="error",
                    output_files=[],
                    metadata={},
                    error_message="Failed to upload image"
                )

            # Load workflow
            workflow_path = self._get_workflow_path('image2video_workflow')
            workflow_content = self._load_workflow_content(workflow_path)
            workflow_content = workflow_content.replace('$inputImage', upload_result['name'])
            workflow_content = workflow_content.replace('$prompt', prompt)
            workflow_content = workflow_content.replace('633890936133287', str(random.getrandbits(32)))
            workflow = json.loads(workflow_content)

            # Run workflow
            result = await client.run_workflow(
                workflow_json=workflow,
                output_node_ids=["60"],
                progress=progress,
                save_dir=save_dir,
                timeout=self._config.get('performance', {}).get('queue_timeout', 3200)
            )

            if result["status"] == "success":
                return ServiceResult(
                    status="success",
                    output_files=result["output_files"],
                    metadata=result,
                    progress=100.0
                )
            else:
                return ServiceResult(
                    status="error",
                    output_files=[],
                    metadata=result,
                    error_message=result.get("error", "Unknown error")
                )

        except Exception as e:
            return ServiceResult(
                status="error",
                output_files=[],
                metadata={},
                error_message=str(e)
            )

    def _get_base_url(self) -> str:
        """Get base URL from config"""
        conn = self._config.get('connection', {})
        server = conn.get('server_url', 'http://192.168.1.100')
        port = conn.get('port', 3000)
        return f"{server}:{port}"

    def _get_workflow_path(self, workflow_key: str) -> str:
        """Get workflow file path from config"""
        workflows = self._config.get('workflows', {})
        relative_path = workflows.get(workflow_key, '')
        
        # Resolve relative to comfyui model directory
        models_dir = Path(__file__).parent.parent.parent / "models" / "comfy_ui"
        return str(models_dir / relative_path)

    def _load_workflow(self, workflow_path: str, prompt: str) -> Dict:
        """Load and prepare workflow JSON"""
        content = self._load_workflow_content(workflow_path)
        content = content.replace('$prompt', prompt)
        content = content.replace('818381787480535', str(random.getrandbits(32)))
        return json.loads(content)

    def _load_workflow_content(self, workflow_path: str) -> str:
        """Load workflow file content"""
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return f.read()

    @classmethod
    def get_service_version(cls) -> str:
        return "1.0.0"

    @classmethod
    def get_service_description(cls) -> str:
        return "ComfyUI integration for AI image and video generation"
