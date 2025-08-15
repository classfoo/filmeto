import os

from app.data.project import Project


class Workspace():
    def __init__(self, workspacePath:str,projectName:str):
        self.workspacePath = workspacePath
        self.projectName = projectName
        self.projectPath = os.path.join(self.workspacePath,self.projectName)
        return

    def project(self):
        return Project(self.projectPath, self.projectName)

    def submit_task(self,params):
        print(params)