# async_queue.py
import asyncio
from asyncio import Queue, Task
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AsyncQueueManager:
    """
    基于 qasync 的非等待式异步消费队列管理器
    专为 PySide/PyQt 设计，支持 GUI 主线程中安全运行 asyncio
    """

    def __init__(
        self,
        processor: Callable[[Any], None],
        maxsize: int = 100,
        name: str = "AsyncConsumer"
    ):
        """
        :param processor: 异步处理函数，签名: async def func(item) -> None
        :param maxsize: 队列最大容量
        :param name: 消费者名称（用于日志）
        """
        if not asyncio.iscoroutinefunction(processor):
            raise TypeError("processor 必须是一个 async def 函数")

        self.processor = processor
        self.queue = Queue(maxsize=maxsize)
        self.name = name
        self._task: Optional[Task] = None
        self._running = False

    def put(self, item: Any):
        """
        非等待式提交任务（线程安全，可在任意线程调用）
        立即返回，不阻塞生产者
        """
        if not self._running:
            raise RuntimeError(f"{self.name} 尚未启动，请先调用 start()")

        # 使用 asyncio.run_coroutine_threadsafe 确保线程安全
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._put_safe(item),
                asyncio.get_event_loop()
            )
            # 不 await，立即返回
        except Exception as e:
            logger.error(f"❌ 提交任务失败 {item}: {e}")

    async def _put_safe(self, item: Any):
        """安全入队（避免 QueueFull）"""
        if self.queue.full():
            logger.warning(f"⚠️ {self.name} 队列已满，丢弃任务: {item}")
            return
        self.queue.put_nowait(item)

    async def start(self):
        """启动消费者（必须在事件循环中调用）"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run(), name=f"{self.name}-runner")
        logger.info(f"✅ {self.name} 已启动 | 容量: {self.queue.maxsize}")

    async def stop(self):
        """停止消费者，等待当前任务完成"""
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"🛑 {self.name} 已停止")

    async def join(self):
        """等待所有任务处理完成"""
        await self.queue.join()

    async def _run(self):
        """后台消费循环"""
        logger.info(f"🟢 {self.name} 循环开始")
        while self._running:
            try:
                item = await self.queue.get()
                try:
                    await self.processor(item)
                except Exception as e:
                    logger.error(f"❌ {self.name} 处理失败 {item}: {e}", exc_info=True)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                logger.info(f"🛑 {self.name} 被取消")
                break
            except Exception as e:
                logger.error(f"❌ {self.name} 发生未预期错误: {e}", exc_info=True)
        logger.info(f"👋 {self.name} 循环退出")