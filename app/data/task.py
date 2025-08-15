import os
import asyncio
from typing import Any

from PySide6.QtCore import Signal, QObject

from utils.queue_utils import AsyncQueueManager
from utils.yaml_utils import load_yaml, save_yaml


class Task():

    def __init__(self,path:str,options:Any):
        self.path = path
        self.options = options
        return

class TaskManager(QObject):

    task_execute = Signal(Task)

    def __init__(self,workspace, tasks_path):
        QObject.__init__(self)
        self.workspace = workspace
        self.tasks_path = tasks_path
        self.config = load_yaml(os.path.join(self.tasks_path, "config.yaml"))
        return

    async def start(self):
        self.task_consumer = AsyncQueueManager(
            processor=self.process_task,
            maxsize=1000,
            name="TaskInitQueue"
        )
        await self.task_consumer.start()

    def submit_task(self, options:dict):
        self.task_consumer.put(options)

    async def process_task(self, options:Any):
        num = self.config['task_index']
        self.config['task_index']=num+1
        self.save_config()
        task_fold_path = os.path.join(self.tasks_path, str(num))
        os.makedirs(task_fold_path, exist_ok=True)
        save_yaml(os.path.join(task_fold_path, "config.yaml"), options)
        self.task_execute.emit(Task(task_fold_path,options))
        return

    # async def loop(self):
    #     self.consume()
    #     return

    def save_config(self):
        save_yaml(os.path.join(self.tasks_path, "config.yaml"), self.config)