import os
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

    def __init__(self,workspace, project, tasks_path):
        QObject.__init__(self)
        self.workspace = workspace
        self.project = project
        self.tasks_path = tasks_path
        return

    async def start(self):
        self.task_consumer = AsyncQueueManager(
            processor=self.process_task,
            maxsize=1000,
            name="TaskInitQueue"
        )
        await self.task_consumer.start()
        self.execute_consumer = AsyncQueueManager(
            processor=self.process_task,
            maxsize=1000,
            name="TaskExecuteQueue"
        )
        await self.execute_consumer.start()

    def connect_task_execute(self,func):
        self.task_execute.connect(func)

    def submit_task(self, options:dict):
        self.task_consumer.put(options)

    async def process_task(self, options:Any):
        num = self.project.config['task_index']
        self.project.update_config('task_index',num+1)
        task_fold_path = os.path.join(self.tasks_path, str(num))
        os.makedirs(task_fold_path, exist_ok=True)
        save_yaml(os.path.join(task_fold_path, "config.yaml"), options)
        self.task_execute.emit(Task(task_fold_path,options))
        return