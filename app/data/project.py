import os.path

from app.data.timeline import Timeline


class Project():
    def __init__(self, projectPath:str, projectName:str):
        self.projectPath = projectPath
        self.projectName = projectName
        return

    def timeline(self):
        return Timeline(os.path.join(self.projectPath, 'timeline'))