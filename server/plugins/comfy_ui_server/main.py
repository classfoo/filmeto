"""
ComfyUI Server Plugin

A plugin that integrates ComfyUI for AI image and video generation.
Supports multiple tools via configurable workflows.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional, Tuple

# Import base plugin directly using file path to avoid naming conflicts
import importlib.util

# Get the absolute path to the base_plugin.py file
# Using __file__ to get the absolute path of this file, then navigate to the plugins directory
current_file_path = Path(__file__).resolve()  # Absolute path to this file
plugin_dir = current_file_path.parent  # Current plugin directory
plugins_dir = plugin_dir.parent  # Parent plugins directory (where base_plugin.py is)
base_plugin_path = plugins_dir / "base_plugin.py"  # Path to base_plugin.py

# Load the base plugin module directly
spec = importlib.util.spec_from_file_location("base_plugin", str(base_plugin_path))
base_plugin_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_plugin_module)

# Import the required classes
BaseServerPlugin = base_plugin_module.BaseServerPlugin
ToolConfig = base_plugin_module.ToolConfig

# Import the ComfyUI client using relative import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comfy_ui_client import ComfyUIClient

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

    def init_ui(self, workspace_path: str, server_config: Optional[Dict[str, Any]] = None):
        """
        Initialize custom UI widget for server configuration.

        Args:
            workspace_path: Path to workspace directory
            server_config: Optional existing server configuration

        Returns:
            QWidget: Custom configuration widget
        """
        try:
            # Import the ComfyUI config widget
            from server.plugins.comfy_ui_server.config.comfy_ui_config_widget import ComfyUIConfigWidget

            # Create and return the widget using the plugin info and config
            widget = ComfyUIConfigWidget(workspace_path, server_config, None)
            return widget
        except Exception as e:
            print(f"Failed to create ComfyUI config widget: {e}")
            import traceback
            traceback.print_exc()
            return None

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

    async def _load_workflow(self, name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load workflow JSON from the workflows directory.
        
        Returns:
            tuple: (prompt_graph, filmeto_config)
            - prompt_graph: The ComfyUI workflow prompt graph
            - filmeto_config: Filmeto-specific configuration including node mappings
        """
        workflow_path = self.workflows_dir / f"{name}.json"
        if not workflow_path.exists():
            # Fallback for text2image naming inconsistency
            if name == "text2image":
                workflow_path = self.workflows_dir / "text2image_workflow.json"
            
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
            
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # Extract filmeto configuration (if exists)
        filmeto_config = workflow.get("_filmeto", {})
        
        # Extract prompt graph (ComfyUI workflow)
        prompt_graph = workflow.get("prompt", workflow)
        
        # If prompt_graph is the whole workflow (old format), extract just the prompt
        if "prompt" in prompt_graph and isinstance(prompt_graph["prompt"], dict):
            prompt_graph = prompt_graph["prompt"]
        
        return prompt_graph, filmeto_config

    async def _execute_text2image(self, client, task_id, parameters, progress_callback):
        prompt_text = parameters.get("prompt", "")
        width = parameters.get("width", 720)
        height = parameters.get("height", 1280)
        
        progress_callback(5, "Loading workflow...", {})
        prompt_graph, filmeto_config = await self._load_workflow("text2image")
        
        # Get node mappings from filmeto config
        node_mapping = filmeto_config.get("node_mapping", {})
        prompt_node = node_mapping.get("prompt_node", "6")  # Default fallback
        width_node = node_mapping.get("width_node")  # Optional
        height_node = node_mapping.get("height_node")  # Optional
        
        # Apply prompt to prompt node
        if prompt_node in prompt_graph:
            prompt_graph[prompt_node]["inputs"]["text"] = prompt_text
        
        # Apply width/height if nodes are specified
        if width_node and width_node in prompt_graph:
            prompt_graph[width_node]["inputs"]["width"] = width
        elif not width_node and "58" in prompt_graph:  # Fallback to old hardcoded node
            prompt_graph["58"]["inputs"]["width"] = width
            
        if height_node and height_node in prompt_graph:
            prompt_graph[height_node]["inputs"]["height"] = height
        elif not height_node and "58" in prompt_graph:  # Fallback to old hardcoded node
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
        prompt_graph, filmeto_config = await self._load_workflow("image2image")
        
        # Get node mappings from filmeto config
        node_mapping = filmeto_config.get("node_mapping", {})
        input_node = node_mapping.get("input_node", "133")  # Default fallback
        prompt_node = node_mapping.get("prompt_node", "187:6")  # Default fallback
        
        # Apply input image to input node
        if input_node in prompt_graph:
            prompt_graph[input_node]["inputs"]["image"] = comfy_filename
        elif "133" in prompt_graph:  # Fallback to old hardcoded node
            prompt_graph["133"]["inputs"]["image"] = comfy_filename
        
        # Apply prompt to prompt node
        if prompt_node in prompt_graph:
            prompt_graph[prompt_node]["inputs"]["text"] = prompt_text
        elif "187:6" in prompt_graph:  # Fallback to old hardcoded node
            prompt_graph["187:6"]["inputs"]["text"] = prompt_text
        
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
        prompt_graph, filmeto_config = await self._load_workflow("image2video")
        
        # Get node mappings from filmeto config
        node_mapping = filmeto_config.get("node_mapping", {})
        input_node = node_mapping.get("input_node", "67")  # Default fallback
        prompt_node = node_mapping.get("prompt_node", "16")  # Default fallback
        prompt_input_key = node_mapping.get("prompt_input_key", "positive_prompt")  # Default fallback
        
        # Apply input image to input node
        if input_node in prompt_graph:
            prompt_graph[input_node]["inputs"]["image"] = comfy_filename
        elif "67" in prompt_graph:  # Fallback to old hardcoded node
            prompt_graph["67"]["inputs"]["image"] = comfy_filename
        
        # Apply prompt to prompt node
        if prompt_node in prompt_graph:
            if prompt_input_key in prompt_graph[prompt_node].get("inputs", {}):
                prompt_graph[prompt_node]["inputs"][prompt_input_key] = prompt_text
            else:
                # Try common prompt input keys
                for key in ["text", "positive_prompt", "prompt"]:
                    if key in prompt_graph[prompt_node].get("inputs", {}):
                        prompt_graph[prompt_node]["inputs"][key] = prompt_text
                        break
        elif "16" in prompt_graph:  # Fallback to old hardcoded node
            prompt_graph["16"]["inputs"]["positive_prompt"] = prompt_text
        
        files = await client.run_workflow(prompt_graph, progress_callback, self.output_dir, task_id)
        return {"task_id": task_id, "status": "success", "output_files": files}

if __name__ == "__main__":
    plugin = ComfyUiServerPlugin()
    plugin.run()
