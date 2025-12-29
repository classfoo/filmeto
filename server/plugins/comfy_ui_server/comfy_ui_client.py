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

    async def connect(self):
        """Establish HTTP and WebSocket connections"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        
        # Prepare WS URL
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://") + f"/ws?clientId={self.client_id}"
        
        try:
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
        except Exception as e:
            print(f"Failed to connect to ComfyUI WebSocket: {e}")
            self.websocket = None

    async def close(self):
        """Close connections"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def upload_image(self, image_path: str) -> Optional[str]:
        """Upload image to ComfyUI and return the filename"""
        if not os.path.exists(image_path):
            return None
        
        if self.session is None or self.session.closed:
            await self.connect()
            
        try:
            with open(image_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('image', f, filename=os.path.basename(image_path))
                
                async with self.session.post(f"{self.base_url}/upload/image", data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("name")
                    else:
                        print(f"Upload failed: {resp.status}")
        except Exception as e:
            print(f"Upload error: {e}")
        return None

    async def send_prompt(self, prompt_graph: Dict[str, Any]) -> Optional[str]:
        """Submit workflow prompt, returns prompt_id"""
        if self.session is None or self.session.closed:
            await self.connect()
            
        payload = {
            "prompt": prompt_graph,
            "client_id": self.client_id
        }
        
        try:
            async with self.session.post(f"{self.base_url}/prompt", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["prompt_id"]
                else:
                    text = await resp.text()
                    print(f"Prompt submission failed: {resp.status}, {text}")
        except Exception as e:
            print(f"Request error: {e}")
        return None

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history for a prompt"""
        if self.session is None or self.session.closed:
            await self.connect()
            
        try:
            async with self.session.get(f"{self.base_url}/history/{prompt_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get(prompt_id, {})
        except Exception as e:
            print(f"Get history failed: {e}")
        return {}

    async def download_view(self, filename: str, subfolder: str, img_type: str, save_path: Path) -> bool:
        """Download a file from ComfyUI /view endpoint"""
        if self.session is None or self.session.closed:
            await self.connect()
            
        params = {"filename": filename, "subfolder": subfolder, "type": img_type}
        try:
            async with self.session.get(f"{self.base_url}/view", params=params) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    return True
        except Exception as e:
            print(f"Download error: {e}")
        return False

    async def track_progress(
        self, 
        prompt_id: str, 
        prompt_graph: Dict[str, Any],
        progress_callback: Callable[[float, str, Dict[str, Any]], None],
        timeout: float = 600.0
    ):
        """Listen to WebSocket messages and report progress via callback"""
        if self.websocket is None:
            await self.connect()
            
        if self.websocket is None:
            print("Cannot track progress: No WebSocket connection")
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

                    if msg_type == 'executing':
                        node = data.get('node')
                        if node is None and data.get('prompt_id') == prompt_id:
                            # Finished
                            break
                        elif node is not None:
                            node_info = prompt_graph.get(node, {})
                            node_title = node_info.get("_meta", {}).get("title", f"Node {node}")
                            progress_callback(20, f"Executing: {node_title}", {"node": node})
                    
                    elif msg_type == 'progress':
                        value = data.get('value', 0)
                        max_val = data.get('max', 1)
                        if max_val > 0:
                            percent = (value / max_val) * 100
                            # Map 20-90% range to actual generation
                            scaled_percent = 20 + (percent * 0.7)
                            progress_callback(scaled_percent, f"Generating... {value}/{max_val}", data)
                    
                    elif msg_type == 'status':
                        queue_remaining = data.get('status', {}).get('exec_info', {}).get('queue_remaining', 0)
                        if queue_remaining > 0:
                            progress_callback(15, f"Queued (position: {queue_remaining})", {})

                except asyncio.TimeoutError:
                    continue
                except ConnectionClosed:
                    print("WebSocket connection closed, attempting reconnect...")
                    await self.connect()
                    if self.websocket is None: break
        except Exception as e:
            print(f"Error tracking progress: {e}")

    async def run_workflow(
        self,
        prompt_graph: Dict[str, Any],
        progress_callback: Callable[[float, str, Dict[str, Any]], None],
        output_dir: Path,
        task_id: str,
        timeout: float = 600.0
    ) -> List[str]:
        """
        Full workflow execution helper.
        """
        # 1. Connect
        await self.connect()
        
        try:
            # 2. Submit
            progress_callback(10, "Submitting task to ComfyUI...", {})
            prompt_id = await self.send_prompt(prompt_graph)
            if not prompt_id:
                raise Exception("Failed to submit prompt to ComfyUI")

            # 3. Monitor
            await self.track_progress(prompt_id, prompt_graph, progress_callback, timeout)

            # 4. Results
            progress_callback(90, "Finalizing results...", {})
            history = await self.get_history(prompt_id)
            if not history:
                raise Exception(f"Failed to get history for prompt {prompt_id}")

            output_files = []
            outputs = history.get("outputs", {})
            for node_id, node_output in outputs.items():
                media_items = node_output.get("images", []) + node_output.get("videos", []) + node_output.get("gifs", [])
                for item in media_items:
                    filename = item["filename"]
                    subfolder = item.get("subfolder", "")
                    img_type = item.get("type", "output")
                    
                    local_filename = f"{task_id}_{filename}"
                    local_path = output_dir / local_filename
                    
                    success = await self.download_view(filename, subfolder, img_type, local_path)
                    if success:
                        output_files.append(str(local_path))
            
            return output_files

        finally:
            await self.close()

