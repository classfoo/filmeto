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
            "version": "1.1.0",
            "description": "ComfyUI integration for AI image and video generation",
            "author": "Filmeto Team",
            "engine": "comfyui"
        }

    def get_supported_tools(self) -> List[ToolConfig]:
        """Get list of tools supported by this plugin with their configs"""
        text2image_params = [
            {
                "name": "prompt",
                "type": "string",
                "required": True,
                "description": "Text prompt for generation"
            },
            {
                "name": "negative_prompt",
                "type": "string",
                "required": False,
                "default": "",
                "description": "Negative prompt"
            },
            {
                "name": "width",
                "type": "integer",
                "required": False,
                "default": 720,
                "description": "Image width"
            },
            {
                "name": "height",
                "type": "integer",
                "required": False,
                "default": 1280,
                "description": "Image height"
            }
        ]

        return [
            ToolConfig(name="text2image", description="Generate image from text prompt using ComfyUI", parameters=text2image_params),
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
        tool_name = task_data.get("tool_name", "") # Changed from 'tool' to 'tool_name' as per FilmetoTask.to_dict()
        parameters = task_data.get("parameters", {})
        metadata = task_data.get("metadata", {})
        server_config = metadata.get("server_config", {})

        # ComfyUI server details
        server_url = server_config.get("server_url", "http://localhost")
        port = server_config.get("port", 8188)
        base_url = f"{server_url}:{port}"
        
        # Ensure URL starts with http
        if not base_url.startswith("http"):
            base_url = "http://" + base_url

        try:
            if tool_name == "text2image":
                return await self._execute_text2image_comfy(task_id, base_url, parameters, progress_callback)
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

    async def _execute_text2image_comfy(
        self,
        task_id: str,
        base_url: str,
        parameters: Dict[str, Any],
        progress_callback: Callable[[float, str, Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """Execute text-to-image task using actual ComfyUI API"""
        prompt_text = parameters.get("prompt", "")
        width = parameters.get("width", 720)
        height = parameters.get("height", 1280)

        progress_callback(5, "Loading workflow...", {})
        
        # Load workflow
        workflow_path = self.workflows_dir / "text2image_workflow.json"
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
            
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # The workflow JSON from the file has a "prompt" key that contains the actual ComfyUI graph
        prompt_graph = workflow.get("prompt", workflow)

        # Inject parameters into the graph
        # Based on text2image_workflow.json:
        # Node 6: Positive Prompt (CLIPTextEncode)
        # Node 58: Latent Image Size (EmptySD3LatentImage)
        
        if "6" in prompt_graph:
            prompt_graph["6"]["inputs"]["text"] = prompt_text
        
        if "58" in prompt_graph:
            prompt_graph["58"]["inputs"]["width"] = width
            prompt_graph["58"]["inputs"]["height"] = height

        progress_callback(10, "Submitting task to ComfyUI...", {})

        async with aiohttp.ClientSession() as session:
            # Submit prompt
            payload = {
                "prompt": prompt_graph,
                "client_id": self.client_id
            }
            
            async with session.post(f"{base_url}/prompt", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ComfyUI prompt submission failed: {error_text}")
                
                resp_json = await response.json()
                prompt_id = resp_json.get("prompt_id")
                print(f"Submitted to ComfyUI, prompt_id: {prompt_id}")

            # Connect to WebSocket for progress
            ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + f"/ws?client_id={self.client_id}"
            
            output_images = []
            
            try:
                async with session.ws_connect(ws_url) as ws:
                    progress_callback(15, "Waiting for ComfyUI execution...", {"prompt_id": prompt_id})
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            if data['type'] == 'executing':
                                node = data['data']['node']
                                if node is None and data['data']['prompt_id'] == prompt_id:
                                    # Execution finished
                                    break
                                elif node is not None:
                                    # Get node title if possible
                                    node_info = prompt_graph.get(node, {})
                                    node_title = node_info.get("_meta", {}).get("title", f"Node {node}")
                                    progress_callback(20, f"Executing: {node_title}", {"node": node})
                            
                            elif data['type'] == 'progress':
                                value = data['data']['value']
                                max_val = data['data']['max']
                                percent = (value / max_val) * 100
                                # Map 20-90% range to actual generation
                                scaled_percent = 20 + (percent * 0.7)
                                progress_callback(scaled_percent, f"Generating... {value}/{max_val}", data['data'])
                            
                            elif data['type'] == 'status':
                                # Check queue status
                                queue_remaining = data['data']['status']['exec_info']['queue_remaining']
                                if queue_remaining > 0:
                                    progress_callback(15, f"Queued (position: {queue_remaining})", {})

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
            except Exception as e:
                print(f"WebSocket error: {e}")
                # Continue anyway, we can check history

            # Execution finished, get history to find output files
            progress_callback(90, "Finalizing results...", {})
            
            async with session.get(f"{base_url}/history/{prompt_id}") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get history for {prompt_id}")
                
                history = await response.json()
                prompt_history = history.get(prompt_id, {})
                outputs = prompt_history.get("outputs", {})
                
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        for img in node_output["images"]:
                            filename = img["filename"]
                            subfolder = img.get("subfolder", "")
                            img_type = img.get("type", "output")
                            
                            # Download image
                            params = {"filename": filename, "subfolder": subfolder, "type": img_type}
                            async with session.get(f"{base_url}/view", params=params) as img_resp:
                                if img_resp.status == 200:
                                    content = await img_resp.read()
                                    # Save to our output dir
                                    local_filename = f"{task_id}_{filename}"
                                    local_path = self.output_dir / local_filename
                                    with open(local_path, "wb") as f:
                                        f.write(content)
                                    output_images.append(str(local_path))

            if not output_images:
                raise Exception("No images generated by ComfyUI")

            # Prepare final result
            return {
                "task_id": task_id,
                "status": "success",
                "output_files": output_images,
                "metadata": {
                    "prompt": prompt_text,
                    "width": width,
                    "height": height,
                    "prompt_id": prompt_id
                }
            }

if __name__ == "__main__":
    # Create and run the plugin
    plugin = ComfyUiServerPlugin()
    plugin.run()
