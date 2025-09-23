from typing import Any

from qasync import asyncSlot

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from utils.progress_utils import Progress


class BaseTool(BaseWidget,Progress):

    def __init__(self,workspace:Workspace):
        super(BaseTool,self).__init__(workspace)
        return

    def submit_task(self,task:Any):
        self.workspace.submit_task(task)

    @asyncSlot()
    async def execute(self, task):
        return