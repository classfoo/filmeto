from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QStyleOption, QStyle
from qasync import asyncSlot

from app.data.task import TaskResult, Task
from app.data.timeline import TimelineItem
from app.data.workspace import Workspace


class BaseWidget(QWidget):

    def __init__(self,workspace:Workspace):
        super(BaseWidget, self).__init__()
        self.workspace = workspace

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        p=QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget,option,p,self)
        super().paintEvent(event)


class BaseTaskWidget(BaseWidget):

    def __init__(self,workspace:Workspace):
        super(BaseTaskWidget, self).__init__(workspace)
        self.workspace = workspace
        self.workspace.connect_task_create(self.on_task_create)
        self.workspace.connect_task_execute(self.on_task_execute)
        self.workspace.connect_task_finished(self.on_task_finished)
        self.workspace.connect_timeline_switch(self.on_timeline_switch)

    @asyncSlot()
    async def on_task_create(self,params):
        return

    @asyncSlot()
    async def on_task_execute(self,result:Task):
        return

    @asyncSlot()
    async def on_task_finished(self,result:TaskResult):
        return

    @asyncSlot()
    async def on_timeline_switch(self,item:TimelineItem):
        return