# comfyui_gui_client_fixed.py
import asyncio
import json
import os
import uuid
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from PySide6.QtCore import QObject, Signal, QThread, Slot, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QProgressBar, QGroupBox, QScrollArea
)
import aiohttp
import websockets


# ----------------------------- 1. 信号类 -----------------------------
class ComfyUIClientSignals(QObject):
    connected = Signal(bool)
    prompt_queued = Signal(str)
    progress_update = Signal(int, str)
    execution_start = Signal()
    execution_done = Signal(dict)
    error_occurred = Signal(str)
    image_downloaded = Signal(str)


# ----------------------------- 2. 异步客户端（修复线程与事件循环）-----------------------------
class AsyncComfyUIClient(QThread):
    def __init__(self, base_url: str = "http://127.0.0.1:8188", parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        self.session = None
        self.websocket = None
        self.prompt_id = None
        self.signals = ComfyUIClientSignals()
        self.loop = None  # 将事件循环保存为实例属性

    def run(self):
        """在新线程中启动 asyncio 事件循环"""
        # 为当前线程设置事件循环
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        try:
            self.loop.run_until_complete(self._run())
        finally:
            self.loop.close()

    async def _run(self):
        await self.connect()
        if not self.signals.connected:
            return
        await self.listen_events()

    async def connect(self):
        try:
            self.session = aiohttp.ClientSession()
            ws_url = f"ws://{self.base_url[7:]}/ws?clientId={self.client_id}"
            self.websocket = await websockets.connect(ws_url)
            self.signals.connected.emit(True)
            print("✅ WebSocket 连接成功")
        except Exception as e:
            self.signals.error_occurred.emit(f"连接失败: {e}")
            self.signals.connected.emit(False)

    async def listen_events(self):
        try:
            async for message in self.websocket:
                msg = json.loads(message)
                msg_type = msg["type"]

                if msg_type == "status":
                    data = msg["data"]
                    queue_remaining = data["exec_info"]["queue_remaining"]
                    self.signals.progress_update.emit(0, f"队列中... 剩余 {queue_remaining}")

                elif msg_type == "execution_start":
                    self.signals.execution_start.emit()
                    self.signals.progress_update.emit(10, "开始执行...")

                elif msg_type == "execution_cached":
                    self.signals.progress_update.emit(20, "加载缓存...")

                elif msg_type == "progress":
                    data = msg["data"]
                    percent = int(data["value"] / data["max"] * 80)
                    self.signals.progress_update.emit(percent, f"生成中... {percent}%")

                elif msg_type == "executing":
                    data = msg["data"]
                    if data["node"] is None and data["prompt_id"] == self.prompt_id:
                        self.signals.progress_update.emit(100, "执行完成")
                        history = await self.get_history(self.prompt_id)
                        if history:
                            self.signals.execution_done.emit(history)
                        break
        except Exception as e:
            self.signals.error_occurred.emit(f"WebSocket 错误: {e}")

    async def get_history(self, prompt_id: str) -> Optional[Dict]:
        url = f"{self.base_url}/history/{prompt_id}"
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get(prompt_id, {})
        except Exception as e:
            self.signals.error_occurred.emit(f"获取历史失败: {e}")
        return None

    async def queue_prompt(self, workflow: Dict[str, Any]):
        url = f"{self.base_url}/prompt"
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        try:
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.prompt_id = result["prompt_id"]
                    self.signals.prompt_queued.emit(self.prompt_id)
                    print(f"✅ 工作流已提交: {self.prompt_id}")
                else:
                    text = await resp.text()
                    self.signals.error_occurred.emit(f"提交失败: {resp.status}, {text}")
        except Exception as e:
            self.signals.error_occurred.emit(f"请求失败: {e}")

    async def download_image(self, filename: str, subfolder: str, save_path: str):
        params = f"filename={quote(filename)}"
        if subfolder:
            params += f"&subfolder={quote(subfolder)}"
        params += "&type=output"
        url = f"{self.base_url}/view?{params}"
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    self.signals.image_downloaded.emit(save_path)
                    print(f"✅ 下载完成: {save_path}")
                else:
                    self.signals.error_occurred.emit(f"下载失败 {filename}: {resp.status}")
        except Exception as e:
            self.signals.error_occurred.emit(f"下载异常: {e}")

    async def close(self):
        """优雅关闭"""
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()


# ----------------------------- 3. 工具函数 -----------------------------
def find_output_node_ids(workflow: Dict[str, Any], class_types: List[str] = None) -> List[str]:
    if class_types is None:
        class_types = ["SaveImage", "PreviewImage"]
    node_ids = []
    for node_id, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type") in class_types:
            node_ids.append(str(node_id))
    return node_ids


# ----------------------------- 4. 主窗口（修复信号连接）-----------------------------
class ComfyUIWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComfyUI 异步客户端")
        self.resize(800, 600)

        self.client: Optional[AsyncComfyUIClient] = None
        self.workflow_data: Optional[Dict[str, Any]] = None
        self.output_dir = "comfyui_output"

        self.setup_ui()
        self.start_client()

    def setup_ui(self):
        layout = QVBoxLayout()

        group = QGroupBox("操作")
        group_layout = QVBoxLayout()

        self.load_btn = QPushButton("📁 加载 Workflow JSON")
        self.load_btn.clicked.connect(self.load_workflow)

        self.dir_btn = QPushButton("📂 选择输出目录")
        self.dir_btn.clicked.connect(self.select_output_dir)

        self.run_btn = QPushButton("▶️ 运行工作流")
        self.run_btn.clicked.connect(self.run_workflow)
        self.run_btn.setEnabled(False)

        group_layout.addWidget(self.load_btn)
        group_layout.addWidget(self.dir_btn)
        group_layout.addWidget(self.run_btn)
        group.setLayout(group_layout)

        self.status_label = QLabel("等待连接...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)

        scroll = QScrollArea()
        scroll.setWidget(self.log_area)
        scroll.setWidgetResizable(True)

        layout.addWidget(group)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def log(self, msg: str):
        self.log_area.append(msg)

    def start_client(self):
        self.client = AsyncComfyUIClient()
        self.client.start()  # 启动线程，运行 asyncio loop

        # 使用 QTimer 延迟连接信号，确保线程已启动
        QTimer.singleShot(100, self.connect_client_signals)

    def connect_client_signals(self):
        self.client.signals.connected.connect(self.on_connected)
        self.client.signals.progress_update.connect(self.on_progress)
        self.client.signals.prompt_queued.connect(self.on_prompt_queued)
        self.client.signals.execution_done.connect(self.on_execution_done)
        self.client.signals.error_occurred.connect(self.on_error)
        self.client.signals.image_downloaded.connect(self.on_image_downloaded)

    def load_workflow(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择 Workflow JSON", "", "JSON Files (*.json)")
        if not file:
            return
        try:
            with open(file, 'r', encoding='utf-8') as f:
                self.workflow_data = json.load(f)
            self.log(f"✅ 加载 workflow: {os.path.basename(file)}")
            output_nodes = find_output_node_ids(self.workflow_data)
            self.log(f"🔍 检测到输出节点: {output_nodes}")
            self.run_btn.setEnabled(True)
        except Exception as e:
            self.log(f"❌ 加载失败: {e}")

    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir = dir_path
            self.log(f"📁 输出目录: {dir_path}")

    def run_workflow(self):
        if not self.workflow_data:
            self.log("❌ 请先加载 workflow")
            return
        self.run_btn.setEnabled(False)
        self.log("🚀 正在提交工作流...")

        # ✅ 正确方式：将协程提交到 client 的事件循环
        asyncio.run_coroutine_threadsafe(
            self.client.queue_prompt(self.workflow_data),
            self.client.loop  # ✅ 现在 self.client.loop 存在
        )

    @Slot(bool)
    def on_connected(self, success: bool):
        if success:
            self.status_label.setText("🟢 已连接到 ComfyUI")
            self.log("🟢 连接成功")
        else:
            self.status_label.setText("🔴 连接失败")
            self.run_btn.setEnabled(False)

    @Slot(str)
    def on_prompt_queued(self, prompt_id: str):
        self.log(f"📨 已提交任务: {prompt_id}")

    @Slot(int, str)
    def on_progress(self, percent: int, text: str):
        self.progress_bar.setValue(percent)
        self.status_label.setText(text)

    @Slot(dict)
    def on_execution_done(self, history: dict):
        self.log("✅ 执行完成，开始下载输出文件...")
        asyncio.run_coroutine_threadsafe(
            self.download_all_images(history),
            self.client.loop  # ✅ 提交到正确的事件循环
        )

    @Slot(str)
    def on_error(self, msg: str):
        self.log(f"❌ 错误: {msg}")
        self.run_btn.setEnabled(True)

    @Slot(str)
    def on_image_downloaded(self, path: str):
        self.log(f"🖼️  下载完成: {path}")

    async def download_all_images(self, history: dict):
        outputs = history.get("outputs", {})
        downloaded = 0
        for node_id, node_data in outputs.items():
            images = node_data.get("images", [])
            for img in images:
                filename = img["filename"]
                subfolder = img["subfolder"]
                save_path = os.path.join(self.output_dir, subfolder, filename)
                await self.client.download_image(filename, subfolder, save_path)
                downloaded += 1
        self.log(f"🎉 全部 {downloaded} 个文件下载完成！")
        self.run_btn.setEnabled(True)

    def closeEvent(self, event):
        """确保优雅关闭"""
        if self.client and self.client.isRunning():
            # 提交关闭任务到事件循环
            asyncio.run_coroutine_threadsafe(self.client.close(), self.client.loop)
            # 等待线程结束
            self.client.wait(3000)  # 最多等待 3 秒
        super().closeEvent(event)


# ----------------------------- 5. 入口 -----------------------------
if __name__ == "__main__":
    app = QApplication([])
    window = ComfyUIWindow()
    window.show()
    app.exec()