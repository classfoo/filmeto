import os.path

from app.data.task import TaskManager, TaskResult
from app.data.timeline import Timeline
from utils.yaml_utils import load_yaml, save_yaml

class Project():

    def __init__(self, workspace, project_path:str, project_name:str):
        self.workspace = workspace
        self.project_path = project_path
        self.project_name = project_name
        self.config = load_yaml(os.path.join(self.project_path, "project.yaml"))
        self.tasks_path = os.path.join(self.project_path,"tasks")
        self.task_manager = TaskManager(self.workspace, self, self.tasks_path)
        self.timeline =  Timeline(self.workspace, self, os.path.join(self.project_path, 'timeline'))


    async def start(self):
        await self.task_manager.start()

    def connect_task_create(self,func):
        self.task_manager.connect_task_create(func)

    def connect_task_execute(self,func):
        self.task_manager.connect_task_execute(func)

    def connect_task_progress(self,func):
        self.task_manager.connect_task_progress(func)

    def connect_task_finished(self,func):
        self.task_manager.connect_task_finished(func)

    def connect_timeline_switch(self,func):
        self.timeline.connect_timeline_switch(func)

    def get_timeline(self):
        return self.timeline

    def get_timeline_index(self):
        return self.config['timeline_index']

    def update_config(self, key,value):
        self.config[key]=value
        save_yaml(os.path.join(self.project_path, "project.yaml"), self.config)

    def submit_task(self,params):
        print(params)
        params['timeline_index'] = self.config['timeline_index']
        self.task_manager.submit_task(params)

    def on_task_finished(self,result:TaskResult):
        self.timeline.on_task_finished(result)
        self.task_manager.on_task_finished(result)

    def get_tasks_path(self):
        return self.tasks_path
