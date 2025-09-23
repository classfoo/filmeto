# comfyui_client.py - 兼容 Python 3.8 及以下
import asyncio
import json
import os
import time
import uuid
import random
from typing import Dict, Any, List, Optional, Tuple  # 使用大写导入

import aiohttp
import websockets

from utils.progress_utils import Progress


class ComfyUIClient:
    def __init__(self, base_url: str = "http://192.168.1.100:3000"):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        self.session = None
        self.websocket = None

    async def connect(self):
        """建立 HTTP 和 WebSocket 连接"""
        self.session = aiohttp.ClientSession()
        ws_url = f"ws://{self.base_url[7:]}/ws?clientId={self.client_id}"
        self.websocket = await websockets.connect(ws_url)

    async def send_prompt(self, workflow_json: Dict[str, Any]) -> Optional[str]:
        """提交工作流，返回 prompt_id"""
        str = json.dumps(workflow_json)
        payload = {
            "prompt": workflow_json['prompt'],
            "client_id": self.client_id
        }
        try:
            async with self.session.post(f"{self.base_url}/prompt", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["prompt_id"]
                else:
                    text = await resp.text()
                    print(f"❌ 提交失败: {resp.status}, {text}")
        except Exception as e:
            print(f"❌ 请求失败: {e}")
        return None

    async def listen_execution(self, prompt_id: str, timeout: float = 60.0) -> Dict[str, Any]:
        """监听执行状态，直到完成或超时"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                msg = json.loads(message)
                msg_type = msg["type"]

                if msg_type == "execution_start":
                    print("🚀 开始执行...")
                elif msg_type == "execution_cached":
                    print("🧠 节点已缓存...")
                elif msg_type == "progress":
                    data = msg["data"]
                    percent = int(data["value"] / data["max"] * 100)
                    print(f"⏳ 进度: {percent}%")
                elif msg_type == "executing":
                    data = msg["data"]
                    if data["node"] is None and data["prompt_id"] == prompt_id:
                        print("✅ 执行完成")
                        return await self.get_history(prompt_id)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"WebSocket 监听错误: {e}")
                break
        print("⏰ 超时或出错")
        return {}

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """获取执行历史"""
        try:
            async with self.session.get(f"{self.base_url}/history/{prompt_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get(prompt_id, {})
        except Exception as e:
            print(f"获取历史失败: {e}")
        return {}

    async def download_image(self, filename: str, subfolder: str, save_path: str):
        """下载图像文件"""
        params = f"filename={filename}&subfolder={subfolder}&type=output"
        url = f"{self.base_url}/view?{params}"
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    print(f"✅ 下载完成: {save_path}")
                    return True
                else:
                    print(f"❌ 下载失败 {filename}: {resp.status}")
        except Exception as e:
            print(f"❌ 下载异常: {e}")
        return False

    async def run_workflow(
        self,
        workflow_json: Dict[str, Any],
        output_node_ids: List[str],
        progress: Progress,
        save_dir: str = "output_images",
        timeout: float = 120.0,
    ) -> Dict[str, Any]:
        """
        运行工作流并下载输出
        返回结果字典
        """
        await self.connect()
        try:
            # 提交任务
            prompt_id = await self.send_prompt(workflow_json)
            if not prompt_id:
                return {"status": "error", "error": "无法提交任务"}

            # 监听执行
            history = await self.listen_execution(prompt_id, timeout=timeout)
            if not history:
                return {"status": "error", "error": "执行超时或失败"}

            # 下载输出图像
            output_files = []
            outputs = history.get("outputs", {})
            for node_id in output_node_ids:
                if node_id in outputs:
                    for img in outputs[node_id].get("images", []):
                        filename = img["filename"]
                        subfolder = img["subfolder"]
                        ext = os.path.splitext(filename)[1]
                        save_path = os.path.join(save_dir, f"output.png")
                        success = await self.download_image(filename, subfolder, save_path)
                        if success:
                            output_files.append(save_path)

            return {
                "status": "success",
                "prompt_id": prompt_id,
                "output_files": output_files
            }

        finally:
            await self.close()

    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()


# ----------------------------- 示例用法 -----------------------------
if __name__ == "__main__":
    # 示例：加载本地 workflow.json 并运行
    with open("test.json", "r", encoding="utf-8") as f:
        content = f.read()
        content = content.replace('$prompt','1 girl')
        seed = random.getrandbits(32)
        print(seed)  # 输出 0 ~ 4294967295 之间的数
        content = content.replace('818381787480535', str(seed))
        workflow = json.loads(content)

    # 创建客户端
    client = ComfyUIClient(base_url="http://192.168.1.100:3000")

    # 运行工作流（替换为你的实际输出节点 ID）
    result = asyncio.run(client.run_workflow(
        workflow_json=workflow,
        output_node_ids=["60"],  # ← 替换为你的 SaveImage 节点 ID
        save_dir="output_images",
        timeout=120.0
    ))

    # 处理结果
    if result["status"] == "success":
        print("🎉 任务成功！输出文件:")
        for f in result["output_files"]:
            print(f"  - {f}")
    else:
        print(f"💥 失败: {result['error']}")