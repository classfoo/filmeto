import asyncio
import os

from app.data.project import Project
from app.data.task import TaskManager


class Workspace():

    def __init__(self, workspace_path:str,project_name:str):
        self.workspace_path = workspace_path
        self.project_name = project_name
        self.project_path = os.path.join(self.workspace_path,self.project_name)
        self.project_obj = Project(self, self.project_path, self.project_name)
        return

    def project(self):
        return self.project_obj

    async def start(self):
        await self.project_obj.start()

    def connect_task_execute(self, func):
        self.project_obj.connect_task_execute(func)

    def connect_task_finished(self, func):
        self.project_obj.connect_task_finished(func)

    def submit_task(self,params):
        print(params)
        self.project_obj.submit_task(params)

    def on_task_finished(self,result):
        self.project_obj.on_task_finished(result)


