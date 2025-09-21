import asyncio
import json
import os
import random
import threading

import qasync

from utils.comfy_ui_utils import ComfyUIClient
from utils.progress_utils import Progress


class  ComfyUiModel():

    def __init__(self):
        return

    async def text2img(self,prompt,save_dir, progress:Progress):
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
        return result