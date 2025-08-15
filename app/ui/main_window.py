from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                               QPushButton, QVBoxLayout, QSplitter)
from PySide6.QtCore import Qt

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.mac_button import MacTitleBar
from app.ui.preview import MediaPreviewWidget
from app.ui.project_menu import ProjectMenu
from app.ui.timeline import HorizontalTimeline
from app.plugins.text2img.text2img import Text2Image


class MainWindowTopBar(BaseWidget):

    def __init__(self, window,workspace:Workspace):
        super(MainWindowTopBar,self).__init__()
        self.setObjectName("main_window_top_bar")
        self.window = window
        #central_widget = QWidget(self)
        #central_widget.setObjectName("main_window_top_bar")
        #self.setAutoFillBackground(True)
        self.setFixedHeight(40)
        #widget = QWidget(self)
        #widget.setObjectName("main_window_top_bar")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)


        # mac title bar
        self.title_bar = MacTitleBar(window)
        self.title_bar.setObjectName("main_window_top_bar_left")

        # close
        self.setting_button = QPushButton("C", self)
        self.setting_button.setObjectName("main_window_top_bar_button")

        # add to layout
        self.layout.addWidget(self.title_bar)
        self.layout.addWidget(ProjectMenu(workspace))
        self.layout.addSpacing(100)
        self.layout.addWidget(QPushButton("\ue61f", self))
        self.layout.addWidget(QPushButton("\ue622", self))
        self.layout.addStretch()
        self.layout.addWidget(self.setting_button)
        # mouse move
        self.draggable = True
        self.drag_start_position = None

    def mousePressEvent(self, event: QMouseEvent):
        self.draggable = True
        self.drag_start_position = event.globalPosition().toPoint() - self.window.pos()
        self.window.mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_start_position is None:
            return
        if self.draggable:
            # 移动窗口
            self.window.move(event.globalPosition().toPoint() - self.drag_start_position)
        self.window.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.draggable = False
        self.window.mouseReleaseEvent(event)

class MainWindowBottomBar(BaseWidget):

    def __init__(self, parent):
        super(MainWindowBottomBar,self).__init__()
        self.setObjectName("main_window_bottom_bar")
        self.parent = parent
        self.setFixedHeight(28)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # close
        # self.setting_button = QPushButton("S", self)
        # self.setting_button.setObjectName("main_window_bottom_bar_button")
        # self.layout.addWidget(self.setting_button)


class MainWindowLeftBar(BaseWidget):

    def __init__(self, parent):
        super(MainWindowLeftBar,self).__init__()
        self.setObjectName("main_window_left_bar")
        self.parent = parent
        self.setFixedWidth(40)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        # buttons
        self.resource_button = QPushButton("\ue846", self)
        self.resource_button.setFixedSize(30, 30)
        self.layout.addWidget(self.resource_button,alignment=Qt.AlignCenter)

        self.model_button = QPushButton("\ue82c", self)
        self.model_button.setFixedSize(30, 30)
        self.layout.addWidget(self.model_button,alignment=Qt.AlignCenter)

        self.attach_button = QPushButton("\ue837", self)
        self.attach_button.setFixedSize(30, 30)
        self.layout.addWidget(self.attach_button,alignment=Qt.AlignCenter)

        self.layout.addStretch(0)
        self.timeline_button = QPushButton("\ue834", self)
        self.timeline_button.setFixedSize(30, 30)
        self.layout.addWidget(self.timeline_button,alignment=Qt.AlignCenter)

        self.message_button = QPushButton("\ue82f", self)
        self.message_button.setFixedSize(30, 30)
        self.layout.addWidget(self.message_button,alignment=Qt.AlignCenter)

        self.video_button = QPushButton("\ue874", self)
        self.video_button.setFixedSize(30, 30)
        self.layout.addWidget(self.video_button,alignment=Qt.AlignCenter)

        self.camera_button = QPushButton("\ue84b", self)
        self.camera_button.setFixedSize(30, 30)
        self.layout.addWidget(self.camera_button,alignment=Qt.AlignCenter)

class MainWindowRightBar(BaseWidget):

    def __init__(self, parent):
        super(MainWindowRightBar,self).__init__()
        self.setObjectName("main_window_right_bar")
        self.parent = parent
        self.setFixedWidth(40)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # close
        self.setting_button = QPushButton("S", self)
        self.setting_button.setObjectName("main_window_bottom_bar_button")
        self.setting_button.setFixedSize(45, 30)
        self.layout.addWidget(self.setting_button)

class MainWindowWorkspaceTop(BaseWidget):

    def __init__(self, parent, workspace):
        super(MainWindowWorkspaceTop,self).__init__()
        self.setObjectName("main_window_workspace_top")
        self.parent = parent
        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Horizontal)
        self.setObjectName("main_window_workspace_top_splitter")
        #self.left = QWidget(self)
        #self.resource_tree = ResourceTreeWidget(self)
        #self.resource_tree.load_directory("workspace")
        #self.left.setObjectName("main_window_workspace_top_left")
        #self.splitter.addWidget(self.resource_tree)
        self.tool = Text2Image(self, workspace)
        self.splitter.addWidget(self.tool)
        self.center = MediaPreviewWidget(self)
        self.center.load_file("workspace/demo/timeline/1/snapshot.png")
        self.center.setObjectName("main_window_workspace_top_center")
        self.splitter.addWidget(self.center)
        self.right = QWidget(self)
        self.right.setObjectName("main_window_workspace_top_right")
        self.splitter.addWidget(self.right)
        self.splitter.setSizes([300,1000,300])
        self.layout.addWidget(self.splitter)

class MainWindowWorkspaceBottom(BaseWidget):

    def __init__(self, parent,workspace:Workspace):
        super(MainWindowWorkspaceBottom,self).__init__()
        self.setObjectName("main_window_workspace_bottom")
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.timeline = HorizontalTimeline(self,workspace)
        self.layout.addWidget(self.timeline)


class MainWindowWorkspace(BaseWidget):

    def __init__(self, parent,workspace:Workspace):
        super(MainWindowWorkspace,self).__init__()
        self.setObjectName("main_window_workspace")
        self.parent = parent

        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setObjectName("main_window_workspace_splitter")
        self.workspace_top = MainWindowWorkspaceTop(self,workspace)
        self.splitter.addWidget(self.workspace_top)
        self.workspace_bottom = MainWindowWorkspaceBottom(self,workspace)
        self.splitter.addWidget(self.workspace_bottom)
        self.splitter.setSizes([1200,360])
        self.layout.addWidget(self.splitter)

class MainWindowHLayout(BaseWidget):

    def __init__(self, parent,workspace:Workspace):
        super(MainWindowHLayout,self).__init__()
        self.setObjectName("main_window_h_layout")
        self.parent = parent
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.left_bar = MainWindowLeftBar(self)
        layout.addWidget(self.left_bar)
        self.workspace  = MainWindowWorkspace(self,workspace)
        layout.addWidget(self.workspace, 1)
        self.right_bar = MainWindowRightBar(self)
        layout.addWidget(self.right_bar)


# --- 主窗口 ---
class MainWindow(QMainWindow):

    def __init__(self, workspace:Workspace):
        super(MainWindow,self).__init__()
        self.setGeometry(100, 100, 1600, 900)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.workspace = workspace
        self.project = workspace.project()
        central_widget = QWidget()
        central_widget.setObjectName("main_window")
        # 主布局
        layout = QVBoxLayout()
        layout.setObjectName("main_window_layout")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.top_bar = MainWindowTopBar(self,self.workspace)
        self.top_bar.setObjectName("main_window_top_bar")
        layout.addWidget(self.top_bar)
        self.h_layout = MainWindowHLayout(self,workspace)
        layout.addWidget(self.h_layout, 1)
        self.bottom_bar = MainWindowBottomBar(self)
        self.bottom_bar.setObjectName("main_window_bottom_bar")
        layout.addWidget(self.bottom_bar)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def workspace(self):
        return self.workspace

    def project(self):
        return self.project



