"""
ComfyUI Server Plugin

A plugin that integrates ComfyUI for AI image and video generation.
Supports multiple tools via configurable workflows.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional

# Add parent directory to path to import base_plugin
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.plugins.base_plugin import BaseServerPlugin, ToolConfig
from server.plugins.comfy_ui_server.comfy_ui_client import ComfyUIClient

class ComfyUiServerPlugin(BaseServerPlugin):
    """
    Plugin for ComfyUI integration.
    """

    def __init__(self):
        super().__init__()
        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        self.workflows_dir = Path(__file__).parent / "workflows"

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin metadata"""
        return {
            "name": "ComfyUI",
            "version": "1.3.0",
            "description": "ComfyUI integration for AI image and video generation",
            "author": "Filmeto Team",
            "engine": "comfyui"
        }

    def get_supported_tools(self) -> List[ToolConfig]:
        """Get list of tools supported by this plugin with their configs"""
        text2image_params = [
            {"name": "prompt", "type": "string", "required": True, "description": "Text prompt for generation"},
            {"name": "width", "type": "integer", "required": False, "default": 720, "description": "Image width"},
            {"name": "height", "type": "integer", "required": False, "default": 1280, "description": "Image height"}
        ]
        
        image2image_params = [
            {"name": "prompt", "type": "string", "required": True, "description": "Text prompt for transformation"},
            {"name": "input_image_path", "type": "string", "required": True, "description": "Path to input image"}
        ]
        
        image2video_params = [
            {"name": "prompt", "type": "string", "required": True, "description": "Text prompt for animation"},
            {"name": "input_image_path", "type": "string", "required": True, "description": "Path to input image"}
        ]

        return [
            ToolConfig(name="text2image", description="Generate image from text prompt using ComfyUI", parameters=text2image_params),
            ToolConfig(name="image2image", description="Transform image using ComfyUI", parameters=image2image_params),
            ToolConfig(name="image2video", description="Animate image using ComfyUI", parameters=image2video_params),
        ]

    async def execute_task(
        self,
        task_data: Dict[str, Any],
        progress_callback: Callable[[float, str, Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Execute a task based on its tool type.
        """
        task_id = task_data.get("task_id", "unknown")
        tool_name = task_data.get("tool_name", "")
        parameters = task_data.get("parameters", {})
        metadata = task_data.get("metadata", {})
        server_config = metadata.get("server_config", {})

        # ComfyUI server details
        server_url = server_config.get("server_url", "http://localhost")
        port = server_config.get("port", 8188)
        base_url = f"{server_url}:{port}"
        
        if not base_url.startswith("http"):
            base_url = "http://" + base_url

        client = ComfyUIClient(base_url)

        try:
            if tool_name == "text2image":
                return await self._execute_text2image(client, task_id, parameters, progress_callback)
            elif tool_name == "image2image":
                return await self._execute_image2image(client, task_id, parameters, progress_callback)
            elif tool_name == "image2video":
                return await self._execute_image2video(client, task_id, parameters, progress_callback)
            else:
                return {
                    "task_id": task_id,
                    "status": "error",
                    "error_message": f"Unsupported tool: {tool_name}",
                    "output_files": []
                }

        except Exception as e:
            print(f"Error executing task with tool {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "task_id": task_id,
                "status": "error",
                "error_message": str(e),
                "output_files": []
            }

    async def _load_workflow(self, name: str) -> Dict[str, Any]:
        """Load workflow JSON from the workflows directory"""
        workflow_path = self.workflows_dir / f"{name}.json"
        if not workflow_path.exists():
            # Fallback for text2image naming inconsistency
            if name == "text2image":
                workflow_path = self.workflows_dir / "text2image_workflow.json"
            
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
            
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        return workflow.get("prompt", workflow)

    async def _execute_text2image(self, client, task_id, parameters, progress_callback):
        prompt_text = parameters.get("prompt", "")
        width = parameters.get("width", 720)
        height = parameters.get("height", 1280)
        
        progress_callback(5, "Loading workflow...", {})
        prompt_graph = await self._load_workflow("text2image")
        
        if "6" in prompt_graph: prompt_graph["6"]["inputs"]["text"] = prompt_text
        if "58" in prompt_graph:
            prompt_graph["58"]["inputs"]["width"] = width
            prompt_graph["58"]["inputs"]["height"] = height
            
        files = await client.run_workflow(prompt_graph, progress_callback, self.output_dir, task_id)
        return {"task_id": task_id, "status": "success", "output_files": files}

    async def _execute_image2image(self, client, task_id, parameters, progress_callback):
        prompt_text = parameters.get("prompt", "")
        input_image_path = parameters.get("input_image_path")
        
        # Check metadata for processed resources (preferred)
        processed_resources = parameters.get("processed_resources")
        if processed_resources:
            input_image_path = processed_resources[0]

        progress_callback(5, "Uploading image...", {})
        comfy_filename = await client.upload_image(input_image_path)
        if not comfy_filename:
            raise Exception("Failed to upload image to ComfyUI")
            
        progress_callback(8, "Loading workflow...", {})
        prompt_graph = await self._load_workflow("image2image")
        
        if "133" in prompt_graph: prompt_graph["133"]["inputs"]["image"] = comfy_filename
        if "187:6" in prompt_graph: prompt_graph["187:6"]["inputs"]["text"] = prompt_text
        
        files = await client.run_workflow(prompt_graph, progress_callback, self.output_dir, task_id)
        return {"task_id": task_id, "status": "success", "output_files": files}

    async def _execute_image2video(self, client, task_id, parameters, progress_callback):
        prompt_text = parameters.get("prompt", "")
        input_image_path = parameters.get("input_image_path")
        
        processed_resources = parameters.get("processed_resources")
        if processed_resources:
            input_image_path = processed_resources[0]

        progress_callback(5, "Uploading image...", {})
        comfy_filename = await client.upload_image(input_image_path)
        if not comfy_filename:
            raise Exception("Failed to upload image to ComfyUI")
            
        progress_callback(8, "Loading workflow...", {})
        prompt_graph = await self._load_workflow("image2video")
        
        if "67" in prompt_graph: prompt_graph["67"]["inputs"]["image"] = comfy_filename
        if "16" in prompt_graph: prompt_graph["16"]["inputs"]["positive_prompt"] = prompt_text
        
        files = await client.run_workflow(prompt_graph, progress_callback, self.output_dir, task_id)
        return {"task_id": task_id, "status": "success", "output_files": files}

if __name__ == "__main__":
    plugin = ComfyUiServerPlugin()
    plugin.run()
