import asyncio
import os

from app.data.project import Project
from app.data.task import TaskManager, TaskResult


class Workspace():

    def __init__(self, workspace_path:str,project_name:str):
        self.workspace_path = workspace_path
        self.project_name = project_name
        self.project_path = os.path.join(self.workspace_path,self.project_name)
        self.project = Project(self, self.project_path, self.project_name)
        return

    def get_project(self):
        return self.project

    async def start(self):
        await self.project.start()

    def connect_task_create(self, func):
        self.project.connect_task_create(func)

    def connect_task_execute(self, func):
        self.project.connect_task_execute(func)

    def connect_task_progress(self, func):
        self.project.connect_task_progress(func)

    def connect_task_finished(self, func):
        self.project.connect_task_finished(func)

    def connect_timeline_switch(self, func):
        self.project.connect_timeline_switch(func)

    def submit_task(self,params):
        print(params)
        self.project.submit_task(params)

    def on_task_finished(self,result:TaskResult):
        self.project.on_task_finished(result)


