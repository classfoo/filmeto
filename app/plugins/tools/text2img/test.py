# main.py
import sys
import asyncio
import threading
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Signal, QObject

# 全局事件循环（运行在独立线程）
loop = None

def start_async_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

# 启动 asyncio 事件循环线程
async_thread = threading.Thread(target=start_async_loop, daemon=True)
async_thread.start()


class AsyncWorker(QObject):
    # 自定义信号
    trigger = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.window = QWidget()
        self.window.setWindowTitle("PySide6 + Async")
        layout = QVBoxLayout()
        self.button = QPushButton("点击异步请求")
        layout.addWidget(self.button)
        self.window.setLayout(layout)

        # 连接信号到槽
        self.trigger.connect(self.on_trigger_async)
        self.button.clicked.connect(self.on_button_click)

        self.window.show()

    def on_button_click(self):
        # 按钮点击 → 发出信号
        print("按钮被点击，发出信号")
        self.trigger.emit()

    def on_trigger_async(self):
        # ✅ 在 Signal 回调中提交异步任务
        print("Signal 被触发，提交异步任务")
        future = asyncio.run_coroutine_threadsafe(self.async_task(), loop)
        # 可选：添加回调处理结果
        future.add_done_callback(self.on_task_done)

    async def async_task(self):
        print("异步任务开始...")
        await asyncio.sleep(2)  # 模拟网络请求
        print("异步任务完成！")
        return "成功"

    def on_task_done(self, future):
        try:
            result = future.result()
            print(f"任务结果: {result}")
        except Exception as e:
            print(f"任务异常: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    worker = AsyncWorker()
    sys.exit(app.exec())