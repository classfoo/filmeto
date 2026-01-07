import os
from typing import Any, Optional

from blinker import signal

from app.spi.model import BaseModelResult
from utils import dict_utils
from utils.async_queue_utils import AsyncQueue
from utils.progress_utils import Progress
from utils.queue_utils import AsyncQueueManager
from utils.yaml_utils import load_yaml, save_yaml


class Task():

    def __init__(self, task_manager, path: str, options: Any):
        self.task_manager = task_manager
        self.path = path
        self.config_path = os.path.join(self.path, "config.yaml")
        self.options = options or {}
        
        # Extract properties from options that were in TaskData
        self.task_id = os.path.basename(path)  # Get task ID from path
        self.title = f'Task {self.task_id}'
        self.tool = self.options.get("tool", "txt2img")
        self.model = self.options.get("model", "comfyui")
        self.percent = self.options.get("percent", 0)
        self.status = self.options.get("status", "running")
        self.log = self.options.get("log", "")  # For compatibility
        return

    def get_config_path(self):
        return self.config_path

    def update_from_config(self):
        """Update task properties from config file"""
        if os.path.exists(self.config_path):
            from utils.yaml_utils import load_yaml
            config = load_yaml(self.config_path) or {}
            self.options.update(config)
            
            # Update properties from the config
            self.title = f'Task {self.task_id}'
            self.tool = config.get("task_type", "txt2img")
            self.model = self.options.get("model", "comfyui")
            self.percent = config.get("progress", 0)
            self.status = config.get("status", "running")
            self.log = config.get("log", "")

class TaskResult():
    def __init__(self,task:Task, result:BaseModelResult):
        self.task = task
        self.result = result
        return

    def get_timeline_index(self):
        return self.task.options['timeline_index']

    def get_timeline_item_id(self):
        return self.task.options.get('timeline_item_id', self.task.options.get('timeline_index'))

    def get_image_path(self):
        return self.result.get_image_path()

    def get_video_path(self):
        return self.result.get_video_path()

    def get_task(self):
        return self.task

    def get_task_id(self):
        return self.task.task_id

class TaskProgress(Progress):

    def __init__(self,task:Task):
        super(TaskProgress, self).__init__()
        self.task = task
        self.percent = 0
        self.logs = ''

    def on_progress(self, percent:int, logs:str):
        self.percent = percent
        self.logs = logs
        dict_utils.set_value(self.task.options, 'percent', percent)
        dict_utils.set_value(self.task.options, 'logs', logs)
        #刷新进度
        save_yaml(self.task.config_path, self.task.options)
        self.task.task_manager.on_task_progress(self)

class TaskManager():
    """
    TaskManager manages tasks at the timeline_item level.
    Each timeline_item has its own TaskManager and task storage directory.
    """

    task_create = signal("task_create")

    task_finished = signal("task_finished")

    task_progress = signal("task_progress")

    def __init__(self, timeline_item, tasks_path: str):
        """
        Initialize TaskManager for a specific timeline_item.
        
        Args:
            timeline_item: The TimelineItem instance this manager belongs to
            tasks_path: Path to the tasks directory for this timeline_item
        """
        self.timeline_item = timeline_item
        self.tasks_path = tasks_path
        self.tasks = {}  # task_id -> Task object
        self.create_consumer = AsyncQueue()
        self.create_consumer.connect("create", self.create_task)
        self.execute_consumer = AsyncQueue()
        
        # Create tasks directory if it doesn't exist
        os.makedirs(self.tasks_path, exist_ok=True)
        return

    async def start(self):
        # Load all existing tasks from the tasks directory
        self.load_all_tasks()

    def connect_task_create(self, func):
        self.task_create.connect(func)

    def connect_task_execute(self, func):
        self.execute_consumer.connect("execute", func)

    def connect_task_progress(self, func):
        self.task_progress.connect(func)

    def connect_task_finished(self, func):
        self.task_finished.connect(func)

    def submit_task(self, options: dict):
        self.create_consumer.add("create", options)

    def _get_next_task_index(self) -> int:
        """Get the next task index for this timeline_item"""
        task_index = self.timeline_item.get_config_value('task_index') or 0
        return task_index

    def _increment_task_index(self):
        """Increment the task index for this timeline_item"""
        current = self._get_next_task_index()
        self.timeline_item.set_config_value('task_index', current + 1)

    async def create_task(self, options: Any):
        num = self._get_next_task_index()
        self._increment_task_index()
        task_fold_path = os.path.join(self.tasks_path, str(num))
        os.makedirs(task_fold_path, exist_ok=True)
        save_yaml(os.path.join(task_fold_path, "config.yaml"), options)
        task = Task(self, task_fold_path, options)
        self.tasks[str(num)] = task
        self.task_create.send(task)
        self.execute_consumer.add("execute", task)
        return

    def on_task_progress(self, task_progress: TaskProgress):
        self.task_progress.send(task_progress)

    def on_task_finished(self, result: TaskResult):
        self.task_finished.send(result)

    def load_all_tasks(self):
        """Load all existing tasks from the tasks directory"""
        if not os.path.exists(self.tasks_path):
            print(f"⚠️ Tasks directory does not exist: {self.tasks_path}")
            return []

        try:
            # Get all task directories (numbered folders)
            task_dirs = []
            for d in os.listdir(self.tasks_path):
                dir_path = os.path.join(self.tasks_path, d)
                if os.path.isdir(dir_path) and d.isdigit():
                    task_dirs.append(d)

            # Clear existing tasks before loading
            self.tasks.clear()

            # Load each task
            loaded_tasks = []
            for task_dir_name in task_dirs:
                task_dir_path = os.path.join(self.tasks_path, task_dir_name)
                
                # Load config file for the task
                config_path = os.path.join(task_dir_path, "config.yaml")
                options = {}
                if os.path.exists(config_path):
                    from utils.yaml_utils import load_yaml
                    options = load_yaml(config_path) or {}
                
                # Create Task object
                task = Task(self, task_dir_path, options)
                self.tasks[task_dir_name] = task
                loaded_tasks.append(task)
            
            print(f"✅ Loaded {len(loaded_tasks)} tasks from {self.tasks_path}")
            return loaded_tasks

        except Exception as e:
            print(f"❌ Error loading tasks: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_task_by_id(self, task_id: str):
        """Get a task by its ID"""
        return self.tasks.get(task_id)

    def load_tasks_paginated(self, start_index: int, count: int):
        """Load tasks in a paginated manner (similar to task_loader functionality)"""
        all_task_ids = sorted([task_id for task_id in self.tasks.keys() if task_id.isdigit()], 
                             key=lambda x: int(x), reverse=True)
        
        # Get the slice of task IDs to load
        end_index = min(start_index + count, len(all_task_ids))
        task_ids_to_load = all_task_ids[start_index:end_index]
        
        # Get the actual task objects
        tasks = []
        for task_id in task_ids_to_load:
            task = self.tasks.get(task_id)
            if task:
                tasks.append(task)
        
        return tasks

    def get_all_tasks(self, start_index: int = 0, count: int = None):
        """Get all tasks as Task objects for UI (replaces previous task_loader functionality)"""
        if count is None:
            # Load all tasks without pagination
            all_task_ids = sorted([task_id for task_id in self.tasks.keys() if task_id.isdigit()], 
                                 key=lambda x: int(x), reverse=True)
            task_ids_to_load = all_task_ids[start_index:]
        else:
            # Load paginated tasks
            all_task_ids = sorted([task_id for task_id in self.tasks.keys() if task_id.isdigit()], 
                                 key=lambda x: int(x), reverse=True)
            end_index = min(start_index + count, len(all_task_ids))
            task_ids_to_load = all_task_ids[start_index:end_index]
        
        # Get the actual task objects
        task_list = []
        for task_id in task_ids_to_load:
            task = self.tasks.get(task_id)
            if task:
                task_list.append(task)
        
        return task_list
    
    def get_timeline_item_id(self) -> int:
        """Get the timeline item ID this manager belongs to"""
        return self.timeline_item.get_index()
    
    @property
    def project(self):
        """Get the project this task manager belongs to (for backward compatibility)"""
        return self.timeline_item.timeline.project


