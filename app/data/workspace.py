import asyncio
import os

from app.data.project import Project
from app.data.task import TaskManager


class Workspace():

    def __init__(self, workspace_path:str,project_name:str):
        self.workspace_path = workspace_path
        self.project_name = project_name
        self.project_path = os.path.join(self.workspace_path,self.project_name)
        self.tasks_path = os.path.join(self.project_path,"tasks")
        self.task_manager = TaskManager(self, self.tasks_path)
        self.task_manager.task_execute.connect
        return

    def project(self):
        return Project(self.project_path, self.project_name)

    def submit_task(self,params):
        print(params)
        self.task_manager.submit_task(params)

    async def start(self):
        await self.task_manager.start()