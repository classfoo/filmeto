# task_loader.py
import os
import json
from typing import List, Tuple
from PySide6.QtCore import QObject, Signal, QRunnable, Slot, QThreadPool

class TaskData:
    def __init__(self, task_id: str, title: str, task_type: str, progress: int = 0, status: str = "running"):
        self.task_id = task_id
        self.title = title
        self.task_type = task_type
        self.progress = progress
        self.status = status  # running, paused, failed, completed

    @staticmethod
    def from_dict(data: dict) -> 'TaskData':
        return TaskData(
            task_id=data.get("task_id", ""),
            title=data.get("title", ""),
            task_type=data.get("task_type", "default"),
            progress=data.get("progress", 0),
            status=data.get("status", "running")
        )

class TaskLoaderSignals(QObject):
    tasks_loaded = Signal(list)  # List[TaskData]
    load_error = Signal(str)

class TaskLoader(QRunnable):
    def __init__(self, folder_path: str, start_index: int, count: int):
        super().__init__()
        self.folder_path = folder_path
        self.start_index = start_index
        self.count = count
        self.signals = TaskLoaderSignals()

    @Slot()
    def run(self):
        tasks = []
        try:
            files = sorted(
                [f for f in os.listdir(self.folder_path) if f.endswith(".json")],
                key=lambda x: int(os.path.splitext(x)[0])
            )
            total = len(files)
            end_index = min(self.start_index + self.count, total)
            for i in range(self.start_index, end_index):
                file_path = os.path.join(self.folder_path, files[i])
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    task = TaskData.from_dict(data)
                    tasks.append(task)
            # 逆序加载（最新在前）
            tasks.reverse()
            self.signals.tasks_loaded.emit(tasks)
        except Exception as e:
            self.signals.load_error.emit(str(e))