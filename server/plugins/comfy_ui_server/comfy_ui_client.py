"""
ComfyUI Client Utility

Handles HTTP and WebSocket communication with ComfyUI server.
Adapted from utils/comfy_ui_utils.py for server-side plugin use.
"""

import asyncio
import json
import os
import time
import uuid
import logging
import aiohttp
import websockets
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from websockets.exceptions import ConnectionClosed

class ComfyUIClient:
    """
    Client for interacting with ComfyUI API.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket = None
        
        # Initialize logger
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.client_id}")

    async def connect(self):
        """Establish HTTP and WebSocket connections"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            self.logger.debug(f"Created new aiohttp session")

        # Prepare WS URL
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://") + f"/ws?clientId={self.client_id}"
        self.logger.debug(f"Connecting to WebSocket: {ws_url}")

        try:
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.logger.info(f"Successfully connected to ComfyUI WebSocket at {ws_url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket {ws_url}: {e}")
            # Don't print to stdout as it interferes with JSON-RPC communication
            # Instead, we can log to a file or just silently handle the error
            self.websocket = None

    async def close(self):
        """Close connections"""
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket connection closed")
            self.websocket = None
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("HTTP session closed")
            self.session = None

    async def upload_image(self, image_path: str) -> Optional[str]:
        """Upload image to ComfyUI and return the filename"""
        self.logger.info(f"Uploading image: {image_path}")
        
        if not os.path.exists(image_path):
            self.logger.error(f"Image file does not exist: {image_path}")
            return None
        
        if self.session is None or self.session.closed:
            await self.connect()
            
        try:
            with open(image_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('image', f, filename=os.path.basename(image_path))

                async with self.session.post(f"{self.base_url}/upload/image", data=data) as resp:
                    self.logger.debug(f"Upload response status: {resp.status}")
                    
                    if resp.status == 200:
                        result = await resp.json()
                        self.logger.info(f"Successfully uploaded image: {result.get('name')}")
                        return result.get("name")
                    else:
                        text = await resp.text()
                        self.logger.error(f"Upload failed with status {resp.status}: {text}")
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            # Upload error but don't print to stdout
            pass
        return None

    async def send_prompt(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Submit workflow, returns prompt_id
        
        Args:
            workflow: Standard ComfyUI workflow JSON (may include prompt, extra_data, _filmeto, etc.)
        
        The workflow can be:
        - A full workflow JSON with prompt, extra_data, and _filmeto sections
        - Just the prompt graph (nodes dictionary)
        - A workflow with client_id field (will be replaced with current client_id)
        """
        self.logger.info(f"Submitting workflow to ComfyUI at {self.base_url}/prompt")
        
        if self.session is None or self.session.closed:
            await self.connect()
            
        # Prepare the workflow for submission
        # If the workflow contains a "prompt" key, use the whole workflow as is
        # If it doesn't have "prompt" key, it's likely already the prompt graph
        workflow_to_send = workflow.copy()
        
        # Extract the prompt graph if it's wrapped in a "prompt" key
        # Standard ComfyUI workflow JSONs have the node graph at the root level
        if "prompt" in workflow_to_send:
            # If it has a "prompt" key, use the whole workflow as is
            # Replace client_id if present to ensure WebSocket routing works correctly
            if "client_id" in workflow_to_send:
                old_client_id = workflow_to_send["client_id"]
                workflow_to_send["client_id"] = self.client_id
                self.logger.debug(f"Replaced client_id from {old_client_id} to {self.client_id}")
            else:
                workflow_to_send["client_id"] = self.client_id
                self.logger.debug(f"Set client_id to {self.client_id}")
            payload = workflow_to_send
            self.logger.debug(f"Using full workflow with prompt key")
        else:
            # If it doesn't have a "prompt" key, it's already the prompt graph
            # IMPORTANT: Don't add client_id to the prompt graph itself, only to the payload
            # The prompt graph should only contain node definitions, not client_id
            payload = {
                "prompt": workflow_to_send,
                "client_id": self.client_id
            }
            self.logger.debug(f"Using prompt graph directly")
        
        # Count nodes in the prompt graph (not including client_id)
        prompt_graph = payload.get("prompt", {})
        node_count = len([k for k in prompt_graph.keys() if k != "client_id"])
        self.logger.debug(f"Sending request with payload containing {node_count} nodes")
        
        try:
            async with self.session.post(f"{self.base_url}/prompt", json=payload) as resp:
                self.logger.debug(f"Prompt submission response status: {resp.status}")
                
                if resp.status == 200:
                    result = await resp.json()
                    prompt_id = result["prompt_id"]
                    self.logger.info(f"Successfully submitted workflow. Prompt ID: {prompt_id}")
                    return prompt_id
                else:
                    text = await resp.text()
                    self.logger.error(f"Prompt submission failed with status {resp.status}: {text}")
                    # Prompt submission failed but don't print to stdout
                    pass
        except Exception as e:
            self.logger.error(f"Request error during prompt submission: {e}")
            # Request error but don't print to stdout
            pass
        return None

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history for a prompt"""
        self.logger.debug(f"Fetching history for prompt_id: {prompt_id}")
        
        if self.session is None or self.session.closed:
            await self.connect()
            
        try:
            async with self.session.get(f"{self.base_url}/history/{prompt_id}") as resp:
                self.logger.debug(f"History request response status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    history = data.get(prompt_id, {})
                    self.logger.info(f"Successfully retrieved history for prompt {prompt_id}")
                    return history
                else:
                    text = await resp.text()
                    self.logger.error(f"Failed to get history for {prompt_id}, status {resp.status}: {text}")
        except Exception as e:
            self.logger.error(f"Exception while getting history for {prompt_id}: {e}")
            # Get history failed but don't print to stdout
            pass
        return {}

    async def download_view(self, filename: str, subfolder: str, img_type: str, save_path: Path) -> bool:
        """Download a file from ComfyUI /view endpoint"""
        self.logger.info(f"Downloading file: {filename} from subfolder {subfolder}, type {img_type} to {save_path}")
        
        if self.session is None or self.session.closed:
            await self.connect()
            
        params = {"filename": filename, "subfolder": subfolder, "type": img_type}
        try:
            async with self.session.get(f"{self.base_url}/view", params=params) as resp:
                self.logger.debug(f"Download response status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.read()
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    self.logger.info(f"Successfully downloaded file to {save_path}")
                    return True
                else:
                    text = await resp.text()
                    self.logger.error(f"Download failed with status {resp.status}: {text}")
        except Exception as e:
            self.logger.error(f"Exception during download of {filename}: {e}")
            # Download error but don't print to stdout
            pass
        return False

    async def track_progress(
        self, 
        prompt_id: str, 
        workflow: Dict[str, Any],
        progress_callback: Callable[[float, str, Dict[str, Any]], None],
        timeout: float = 600.0
    ):
        """Listen to WebSocket messages and report progress via callback"""
        self.logger.info(f"Starting to track progress for prompt {prompt_id}, timeout: {timeout}s")
        
        if self.websocket is None:
            await self.connect()
            
        if self.websocket is None:
            self.logger.error("Cannot track progress: WebSocket connection is not available")
            # Cannot track progress but don't print to stdout
            return

        start_time = time.time()
        try:
            while time.time() - start_time < timeout:
                try:
                    # Non-blocking wait for message
                    message_raw = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    msg = json.loads(message_raw)
                    msg_type = msg.get("type")
                    data = msg.get("data", {})
                    
                    self.logger.debug(f"Received WebSocket message: type={msg_type}, data={data}")

                    if msg_type == 'executing':
                        node = data.get('node')
                        if node is None and data.get('prompt_id') == prompt_id:
                            self.logger.info(f"Execution completed for prompt {prompt_id}")
                            # Finished
                            break
                        elif node is not None:
                            node_info = workflow.get(node, {})
                            node_title = node_info.get("_meta", {}).get("title", f"Node {node}")
                            self.logger.info(f"Executing node: {node_title} ({node})")
                            progress_callback(20, f"Executing: {node_title}", {"node": node})
                    
                    elif msg_type == 'progress':
                        value = data.get('value', 0)
                        max_val = data.get('max', 1)
                        if max_val > 0:
                            percent = (value / max_val) * 100
                            # Map 20-90% range to actual generation
                            scaled_percent = 20 + (percent * 0.7)
                            self.logger.debug(f"Progress update: {value}/{max_val} ({percent:.1f}%)")
                            progress_callback(scaled_percent, f"Generating... {value}/{max_val}", data)
                    
                    elif msg_type == 'status':
                        queue_remaining = data.get('status', {}).get('exec_info', {}).get('queue_remaining', 0)
                        if queue_remaining > 0:
                            self.logger.info(f"Task queued with {queue_remaining} remaining")
                            progress_callback(15, f"Queued (position: {queue_remaining})", {})

                except asyncio.TimeoutError:
                    continue
                except ConnectionClosed:
                    self.logger.warning("WebSocket connection closed, attempting to reconnect")
                    # WebSocket connection closed, attempting reconnect silently
                    await self.connect()
                    if self.websocket is None: 
                        self.logger.error("Failed to reconnect WebSocket, stopping progress tracking")
                        break
        except Exception as e:
            self.logger.error(f"Error tracking progress for prompt {prompt_id}: {e}")
            # Error tracking progress but don't print to stdout
            pass

    async def run_workflow(
        self,
        workflow: Dict[str, Any],
        progress_callback: Callable[[float, str, Dict[str, Any]], None],
        output_dir: Path,
        task_id: str,
        timeout: float = 600.0
    ) -> List[str]:
        """
        Full workflow execution helper.
        """
        self.logger.info(f"Starting workflow execution for task {task_id}")
        
        # 1. Connect
        await self.connect()
        
        try:
            # 2. Submit
            progress_callback(10, "Submitting task to ComfyUI...", {})
            prompt_id = await self.send_prompt(workflow)
            if not prompt_id:
                self.logger.error("Failed to submit prompt to ComfyUI")
                raise Exception("Failed to submit prompt to ComfyUI")

            self.logger.info(f"Successfully submitted workflow, assigned prompt_id: {prompt_id}")
            
            # 3. Monitor
            self.logger.info(f"Starting progress tracking for prompt {prompt_id}")
            await self.track_progress(prompt_id, workflow, progress_callback, timeout)
            self.logger.info(f"Progress tracking completed for prompt {prompt_id}")

            # 4. Results
            progress_callback(90, "Finalizing results...", {})
            history = await self.get_history(prompt_id)
            if not history:
                self.logger.error(f"Failed to get history for prompt {prompt_id}")
                raise Exception(f"Failed to get history for prompt {prompt_id}")

            self.logger.info(f"Retrieved execution history with {len(history.get('outputs', {}))} output nodes")
            
            output_files = []
            outputs = history.get("outputs", {})
            for node_id, node_output in outputs.items():
                media_items = node_output.get("images", []) + node_output.get("videos", []) + node_output.get("gifs", [])
                self.logger.debug(f"Processing node {node_id} with {len(media_items)} media items")
                
                for item in media_items:
                    filename = item["filename"]
                    subfolder = item.get("subfolder", "")
                    img_type = item.get("type", "output")
                    
                    local_filename = f"{task_id}_{filename}"
                    local_path = output_dir / local_filename
                    
                    self.logger.debug(f"Downloading media item: {filename} from subfolder {subfolder}")
                    success = await self.download_view(filename, subfolder, img_type, local_path)
                    if success:
                        output_files.append(str(local_path))
                        self.logger.info(f"Successfully downloaded: {local_path}")
                    else:
                        self.logger.error(f"Failed to download: {filename}")
            
            self.logger.info(f"Workflow execution completed. Generated {len(output_files)} output files")
            return output_files

        finally:
            await self.close()
            self.logger.info(f"Workflow execution for task {task_id} finished and connections closed")

