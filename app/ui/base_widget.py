from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QStyleOption, QStyle
from qasync import asyncSlot

from app.data.layer import Layer, LayerManager
from app.data.task import TaskResult, Task
from app.data.timeline import TimelineItem
from app.data.workspace import Workspace


class BaseWidget(QWidget):

    def __init__(self,workspace:Workspace):
        super(BaseWidget, self).__init__()
        # 检查workspace是否为None
        if workspace is None:
            raise ValueError("Workspace cannot be None")
            
        self.workspace = workspace
        # 连接到Workspace的项目切换信号
        self.workspace.connect_project_switched(self.on_project_switched)

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        p=QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget,option,p,self)
        super().paintEvent(event)
    
    def on_project_switched(self, project_name):
        """项目切换时的处理方法，子类可以重写此方法"""
        pass


class BaseTaskWidget(BaseWidget):

    def __init__(self,workspace:Workspace):
        super(BaseTaskWidget, self).__init__(workspace)
        self.workspace = workspace
        self.workspace.connect_task_create(self.on_task_create)
        self.workspace.connect_task_finished(self.on_task_finished)
        self.workspace.connect_timeline_switch(self.on_timeline_switch)
        self.workspace.connect_layer_changed(self.on_layer_changed)

    def on_task_create(self,params):
        return

    # def on_task_execute(self,result:Task):
    #     return

    def on_task_finished(self,result:TaskResult):
        return

    def on_timeline_switch(self,item:TimelineItem):
        return

    def on_layer_changed(self,layer_manager:LayerManager, layer:Layer, change_type:str):
        return