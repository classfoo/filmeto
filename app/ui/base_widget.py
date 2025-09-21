from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QStyleOption, QStyle
from qasync import asyncSlot

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
        workspace.connect_task_finished(self.on_task_finished)

    @asyncSlot()
    async def on_task_finished(self,result):
        return