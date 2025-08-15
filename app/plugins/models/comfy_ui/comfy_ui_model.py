import asyncio
import json
import os
import random
import threading
from typing import Any

import qasync

from app.data.task import TaskResult
from app.spi.model import BaseModel, BaseModelResult
from utils.comfy_ui_utils import ComfyUIClient
from utils.progress_utils import Progress

class ComfyUiModelResult(BaseModelResult):

    def __init__(self,options:Any):
        super(ComfyUiModelResult, self).__init__()
        self.options = options

    def get_image_path(self):
        file_path =  self.options['output_files'][0]
        if file_path.endswith(".png"):
            return file_path
        return None

    def get_video_path(self):
        file_path =  self.options['output_files'][0]
        if file_path.endswith(".mp4"):
            return file_path
        return None

class  ComfyUiModel(BaseModel):

    def __init__(self):
        super(ComfyUiModel, self).__init__()
        return

    async def text2image(self,prompt:str,save_dir:str, progress:Progress):
        # 示例：加载本地 workflow.json 并运行
        current_path = os.path.dirname(__file__)
        json_path = os.path.join(current_path, "workflows/text_to_image_qwen_image.json")
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
            content = content.replace('$prompt', prompt)
            seed = random.getrandbits(32)
            print(seed)  # 输出 0 ~ 4294967295 之间的数
            content = content.replace('818381787480535', str(seed))
            workflow = json.loads(content)

        # 创建客户端
        client = ComfyUIClient(base_url="http://192.168.1.100:3000")

        # 运行工作流（替换为你的实际输出节点 ID）
        result = await client.run_workflow(
            workflow_json=workflow,
            output_node_ids=["60"],  # ← 替换为你的 SaveImage 节点 ID
            progress = progress,
            save_dir=save_dir,
            timeout=120.0
        )

        # 处理结果
        if result["status"] == "success":
            print("🎉 任务成功！输出文件:")
            for f in result["output_files"]:
                print(f"  - {f}")
        else:
            print(f"💥 失败: {result['error']}")
        return ComfyUiModelResult(result)


    async def upload_image(self, input_image_path: str) -> str:
        """
        使用ComfyUIClient的upload_image方法上传图片到comfyui，并返回远程的文件名称
        """
        client = ComfyUIClient(base_url="http://192.168.1.100:3000")
        try:
            await client.connect()
            result = await client.upload_image(input_image_path)
            # 返回上传后的文件名
            if result and 'name' in result:
                return result['name']
            else:
                print(f"❌ 上传失败，返回结果: {result}")
                return ""
        except Exception as e:
            print(f"❌ 上传图片时发生错误: {e}")
            return ""
        finally:
            await client.close()

    async def image_edit(self, input_image_path: str, prompt: str, save_dir: str, progress: Progress):
        # 使用upload_image方法上传图片并获取远程文件名
        input_image_name = await self.upload_image(input_image_path)
        if not input_image_name:
            return ComfyUiModelResult({"status": "error", "error": "Failed to upload image"})
        
        # 加载本地 workflow.json 并运行
        current_path = os.path.dirname(__file__)
        json_path = os.path.join(current_path, "workflows", "qwen_image_edit.json")

        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
            content = content.replace('$inputImage', input_image_name)
            content = content.replace('$prompt', prompt)
            seed = random.getrandbits(32)
            content = content.replace('$seed', str(seed))
            workflow = json.loads(content)

        # 创建客户端
        client = ComfyUIClient(base_url="http://192.168.1.100:3000")
        # 运行工作流（替换为你的实际输出节点 ID）
        result = await client.run_workflow(
            workflow_json=workflow,
            output_node_ids=["60"],  # ← 替换为你的 SaveImage 节点 ID
            progress = progress,
            save_dir=save_dir,
            timeout=120.0
        )

        # 处理结果
        if result["status"] == "success":
            print("🎉 任务成功！输出文件:")
            for f in result["output_files"]:
                print(f"  - {f}")
        else:
            print(f"💥 失败: {result['error']}")
        return ComfyUiModelResult(result)
    
    async def image2video(self, input_image_path: str, prompt: str, save_dir: str, progress: Progress):
        # 使用upload_image方法上传图片并获取远程文件名
        input_image_name = await self.upload_image(input_image_path)
        if not input_image_name:
            return ComfyUiModelResult({"status": "error", "error": "Failed to upload image"})
        
        # 加载本地 workflow.json 并运行
        current_path = os.path.dirname(__file__)
        json_path = os.path.join(current_path, "workflows/image_to_video_wan_2_2_kj.json")
        
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()
            content = content.replace('$inputImage', input_image_name)
            content = content.replace('$prompt', prompt)
            seed = random.getrandbits(32)
            print(seed)  # 输出 0 ~ 4294967295 之间的数
            content = content.replace('633890936133287', str(seed))
            workflow = json.loads(content)

        # 创建客户端
        client = ComfyUIClient(base_url="http://192.168.1.100:3000")
        # 运行工作流（替换为你的实际输出节点 ID）
        result = await client.run_workflow(
            workflow_json=workflow,
            output_node_ids=["60"],  # ← 替换为你的 SaveImage 节点 ID
            progress = progress,
            save_dir=save_dir,
            timeout=3200.0
        )

        # 处理结果
        if result["status"] == "success":
            print("🎉 任务成功！输出文件:")
            for f in result["output_files"]:
                print(f"  - {f}")
        else:
            print(f"💥 失败: {result['error']}")
        return ComfyUiModelResult(result)