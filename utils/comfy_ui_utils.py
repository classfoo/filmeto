# comfyui_client.py - 兼容 Python 3.8 及以下
import asyncio
import json
import os
import time
import traceback
import uuid
import random
from typing import Dict, Any, List, Optional, Tuple  # 使用大写导入

import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed

from utils.progress_utils import Progress


class ComfyUIClient:


    def __init__(self, base_url: str = "http://192.168.1.100:3000"):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        self.session = None
        self.websocket = None
        self.ping_task = None

    async def connect(self):
        """建立 HTTP 和 WebSocket 连接"""
        self.session = aiohttp.ClientSession()
        ws_url = f"ws://{self.base_url[7:]}/ws?clientId={self.client_id}"
        # 使用更安全的连接方式，设置适当的超时和ping/pong参数
        self.websocket = await websockets.connect(
            ws_url,
            ping_interval=20,  # 每20秒发送一次ping
            ping_timeout=10,   # ping超时时间设为10秒
            close_timeout=10   # 关闭超时时间
        )

    async def send_prompt(self, workflow_json: Dict[str, Any]) -> Optional[str]:
        """提交工作流，返回 prompt_id"""
        #str = json.dumps(workflow_json)
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

    async def listen_execution(self, prompt_id: str, timeout: float = 60.0,progress:Progress=None) -> Dict[str, Any]:
        """监听执行状态，直到完成或超时"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=100.0)
                self.update_progress(message, progress, prompt_id)
                history = await self.get_history(prompt_id)
                if history == {}:
                    continue
                progress.on_progress(100, "✅ 执行完成")
                return history
            except asyncio.TimeoutError:
                continue
            except ConnectionClosed as e:
                print(f"WebSocket 连接已关闭: {e}")
                # 重新建立连接
                try:
                    await self.connect()
                except Exception as reconnect_error:
                    print(f"重新连接失败: {reconnect_error}")
                    break
            except Exception as e:
                traceback.print_stack()
                print(f"WebSocket 监听错误: {e}")
                continue
        print("⏰ 超时或出错")
        traceback.print_stack()
        return {}


    def update_progress(self, message, progress, prompt_id):
        """
        优化的进度更新方法，处理ComfyUI的/ws流接口返回
        解析整体进度和相关日志
        
        解析规则：
        - type为"executing"的消息包含node标识节点ID（节点开始/结束执行）
        - type为"progress"的消息通过data中的value和max计算节点进度
        - 整体进度按照总节点数和已执行节点数推算
        """
        msg = json.loads(message)
        msg_type = msg["type"]
        if msg_type == "execution_start":
            # 整个工作流开始执行
            progress.on_log("🚀 开始执行...")
            print("🚀 execution_start...")
        elif msg_type == "progress":
            # 节点进度更新
            data = msg["data"]
            node_id = data.get("node", "unknown")
            value = data.get("value", 0)
            max_val = data.get("max", 1)
            if max_val !=0:
                node_progress = int(value / max_val * 100)
                progress.on_log(f"⏳ 节点 {node_id} 进度: {node_progress}%")
                if node_progress==100:
                    progress.set_current(progress.get_current()+1)
        elif msg_type == "executing":
            # 某个节点执行完成
            data = msg["data"]
            node_id = data.get("node")
            progress.on_log(f"✅ 节点 {node_id} 开始执行...")
        elif msg_type == "executed":
            # 某个节点执行完成
            data = msg["data"]
            node_id = data.get("node")
            progress.on_log(f"✅ 节点 {node_id} 执行完成")
            progress.set_current(progress.get_current() + 1)
        else:
            print(f"⏳{message}")

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

    async def upload_image(self, image_path: str) -> Dict[str, Any]:
        """上传图像文件"""
        if not os.path.exists(image_path):
            print(f"❌ 文件不存在: {image_path}")
            return {}
        
        try:
            # 创建 multipart/form-data 请求来上传文件
            with open(image_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('image', f, filename=os.path.basename(image_path))
                
                async with self.session.post(f"{self.base_url}/upload/image", data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"✅ 上传成功: {image_path}")
                        return result
                    else:
                        print(f"❌ 上传失败: {resp.status}")
                        text = await resp.text()
                        print(f"错误信息: {text}")
                        return {}
        except Exception as e:
            print(f"❌ 上传异常: {e}")
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
        timeout: float = 1200.0,
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
            progress.set_total(len(workflow_json.get("prompt")))
            history = await self.listen_execution(prompt_id, timeout=timeout, progress=progress)
            if not history:
                return {"status": "error", "error": "执行超时或失败"}

            # 下载输出图像
            output_files = []
            filenames = []
            outputs = history.get("outputs", {})
            for node_id in output_node_ids:
                if node_id in outputs:
                    for img in outputs[node_id].get("images", []):
                        filename = img["filename"]
                        filenames.append(filename)
                        subfolder = img["subfolder"]
                        ext = os.path.splitext(filename)[1]
                        save_path = os.path.join(save_dir, f"output.png")
                        success = await self.download_image(filename, subfolder, save_path)
                        if success:
                            output_files.append(save_path)
                    for gifs in outputs[node_id].get("gifs", []):
                        filename = gifs["filename"]
                        filenames.append(filename)
                        subfolder = gifs["subfolder"]
                        ext = os.path.splitext(filename)[1]
                        save_path = os.path.join(save_dir, f"output.mp4")
                        success = await self.download_image(filename, subfolder, save_path)
                        if success:
                            output_files.append(save_path)
            return {
                "status": "success",
                "prompt_id": prompt_id,
                "output_files": output_files,
                "filenames" : filenames
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
    import sys
    
    # 如果命令行参数包含 "upload"，则运行上传示例
    if len(sys.argv) > 1 and sys.argv[1] == "upload":
        async def upload_example():
            # 创建客户端
            client = ComfyUIClient(base_url="http://192.168.1.100:3000")
            await client.connect()
            
            # 上传图片示例
            result = await client.upload_image("example_image.png")  # 替换为你的图片路径
            print(f"上传结果: {result}")
            
            await client.close()
        
        asyncio.run(upload_example())
    else:
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