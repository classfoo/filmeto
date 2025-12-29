"""
ComfyUI Server Plugin

A plugin that integrates ComfyUI for AI image and video generation.
Supports multiple tools via configurable workflows.
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
import uuid
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional

# Add parent directory to path to import base_plugin
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.plugins.base_plugin import BaseServerPlugin, ToolConfig

class ComfyUiServerPlugin(BaseServerPlugin):
    """
    Plugin for ComfyUI integration.
    """

    def __init__(self):
        super().__init__()
        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        self.workflows_dir = Path(__file__).parent / "workflows"
        self.client_id = str(uuid.uuid4())

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin metadata"""
        return {
            "name": "ComfyUI",
            "version": "1.2.0",
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

        try:
            if tool_name == "text2image":
                return await self._execute_text2image_comfy(task_id, base_url, parameters, progress_callback)
            elif tool_name == "image2image":
                return await self._execute_image2image_comfy(task_id, base_url, parameters, task_data.get("resources", []), progress_callback)
            elif tool_name == "image2video":
                return await self._execute_image2video_comfy(task_id, base_url, parameters, task_data.get("resources", []), progress_callback)
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

    async def _upload_image(self, session: aiohttp.ClientSession, base_url: str, image_path: str) -> str:
        """Upload image to ComfyUI and return the filename"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found for upload: {image_path}")
            
        with open(image_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('image', f, filename=os.path.basename(image_path))
            async with session.post(f"{base_url}/upload/image", data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to upload image: {error_text}")
                resp_json = await response.json()
                return resp_json.get("name")

    async def _execute_workflow(
        self,
        task_id: str,
        base_url: str,
        prompt_graph: Dict[str, Any],
        progress_callback: Callable[[float, str, Dict[str, Any]], None]
    ) -> List[str]:
        """Helper to submit workflow and wait for results via WebSocket"""
        progress_callback(10, "Submitting task to ComfyUI...", {})

        async with aiohttp.ClientSession() as session:
            # Submit prompt
            payload = {"prompt": prompt_graph, "client_id": self.client_id}
            async with session.post(f"{base_url}/prompt", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ComfyUI prompt submission failed: {error_text}")
                resp_json = await response.json()
                prompt_id = resp_json.get("prompt_id")

            # Connect to WebSocket for progress
            ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + f"/ws?client_id={self.client_id}"
            
            try:
                async with session.ws_connect(ws_url) as ws:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data['type'] == 'executing':
                                node = data['data']['node']
                                if node is None and data['data']['prompt_id'] == prompt_id:
                                    break
                                elif node is not None:
                                    node_info = prompt_graph.get(node, {})
                                    node_title = node_info.get("_meta", {}).get("title", f"Node {node}")
                                    progress_callback(20, f"Executing: {node_title}", {"node": node})
                            elif data['type'] == 'progress':
                                value, max_val = data['data']['value'], data['data']['max']
                                percent = 20 + (value / max_val * 70)
                                progress_callback(percent, f"Generating... {value}/{max_val}", data['data'])
            except Exception as e:
                print(f"WebSocket error: {e}")

            # Get history
            progress_callback(90, "Finalizing results...", {})
            output_files = []
            async with session.get(f"{base_url}/history/{prompt_id}") as response:
                if response.status == 200:
                    history = await response.json()
                    outputs = history.get(prompt_id, {}).get("outputs", {})
                    for node_id, node_output in outputs.items():
                        # Handle both images and videos
                        media_items = node_output.get("images", []) + node_output.get("videos", []) + node_output.get("gifs", [])
                        for item in media_items:
                            filename = item["filename"]
                            params = {"filename": filename, "subfolder": item.get("subfolder", ""), "type": item.get("type", "output")}
                            async with session.get(f"{base_url}/view", params=params) as media_resp:
                                if media_resp.status == 200:
                                    content = await media_resp.read()
                                    local_path = self.output_dir / f"{task_id}_{filename}"
                                    with open(local_path, "wb") as f:
                                        f.write(content)
                                    output_files.append(str(local_path))
            return output_files

    async def _execute_text2image_comfy(self, task_id, base_url, parameters, progress_callback):
        prompt_text = parameters.get("prompt", "")
        width = parameters.get("width", 720)
        height = parameters.get("height", 1280)
        
        workflow_path = self.workflows_dir / "text2image_workflow.json"
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        prompt_graph = workflow.get("prompt", workflow)
        
        if "6" in prompt_graph: prompt_graph["6"]["inputs"]["text"] = prompt_text
        if "58" in prompt_graph:
            prompt_graph["58"]["inputs"]["width"] = width
            prompt_graph["58"]["inputs"]["height"] = height
            
        files = await self._execute_workflow(task_id, base_url, prompt_graph, progress_callback)
        return {"task_id": task_id, "status": "success", "output_files": files}

    async def _execute_image2image_comfy(self, task_id, base_url, parameters, resources, progress_callback):
        prompt_text = parameters.get("prompt", "")
        input_image_path = parameters.get("input_image_path")
        
        # If resources are provided, use the first processed one
        if resources and 'processed_resources' in parameters: # Actually FilmetoService puts it in metadata
            pass # We'll get it from parameters or resources below
            
        # Re-verify image path from resources if possible
        processed_resources = parameters.get("processed_resources") # Injected by service
        if processed_resources:
            input_image_path = processed_resources[0]

        async with aiohttp.ClientSession() as session:
            comfy_filename = await self._upload_image(session, base_url, input_image_path)
            
        workflow_path = self.workflows_dir / "image2image.json"
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        prompt_graph = workflow.get("prompt", workflow)
        
        if "133" in prompt_graph: prompt_graph["133"]["inputs"]["image"] = comfy_filename
        if "187:6" in prompt_graph: prompt_graph["187:6"]["inputs"]["text"] = prompt_text
        
        files = await self._execute_workflow(task_id, base_url, prompt_graph, progress_callback)
        return {"task_id": task_id, "status": "success", "output_files": files}

    async def _execute_image2video_comfy(self, task_id, base_url, parameters, resources, progress_callback):
        prompt_text = parameters.get("prompt", "")
        input_image_path = parameters.get("input_image_path")
        
        processed_resources = parameters.get("processed_resources")
        if processed_resources:
            input_image_path = processed_resources[0]

        async with aiohttp.ClientSession() as session:
            comfy_filename = await self._upload_image(session, base_url, input_image_path)
            
        workflow_path = self.workflows_dir / "image2video.json"
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        prompt_graph = workflow.get("prompt", workflow)
        
        if "67" in prompt_graph: prompt_graph["67"]["inputs"]["image"] = comfy_filename
        if "16" in prompt_graph: prompt_graph["16"]["inputs"]["positive_prompt"] = prompt_text
        
        files = await self._execute_workflow(task_id, base_url, prompt_graph, progress_callback)
        return {"task_id": task_id, "status": "success", "output_files": files}

if __name__ == "__main__":
    plugin = ComfyUiServerPlugin()
    plugin.run()
