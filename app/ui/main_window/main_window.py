# -*- coding: utf-8 -*-
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QLineEdit, QTextEdit, QPlainTextEdit)
from PySide6.QtCore import Qt

from app.data.workspace import Workspace
from .top_side_bar import MainWindowTopSideBar
from .bottom_side_bar import MainWindowBottomSideBar
from .h_layout import MainWindowHLayout


# --- 主窗口 ---
class MainWindow(QMainWindow):

    def __init__(self, workspace: Workspace):
        super(MainWindow, self).__init__()
        self.setGeometry(100, 100, 1600, 900)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.workspace = workspace
        self.project = workspace.get_project()
        # 设置主窗口引用到 workspace，方便访问预览组件
        self.workspace._main_window = self
        central_widget = QWidget()
        central_widget.setObjectName("main_window")
        # 主布局
        layout = QVBoxLayout()
        layout.setObjectName("main_window_layout")
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.top_bar = MainWindowTopSideBar(self, self.workspace)
        self.top_bar.setObjectName("main_window_top_bar")
        layout.addWidget(self.top_bar)
        self.h_layout = MainWindowHLayout(self, workspace)
        layout.addWidget(self.h_layout, 1)
        self.bottom_bar = MainWindowBottomSideBar(workspace, self)
        self.bottom_bar.setObjectName("main_window_bottom_bar")
        layout.addWidget(self.bottom_bar)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def workspace(self):
        return self.workspace

    def project(self):
        return self.project
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle global keyboard shortcuts.
        Spacebar toggles play/pause unless a text input is focused.
        """
        if event.key() == Qt.Key_Space:
            # Check if focus is on a text input widget
            focused_widget = self.focusWidget()
            
            # If focused widget is a text input, let it handle the spacebar
            if isinstance(focused_widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
                super().keyPressEvent(event)
                return
            
            # Otherwise, toggle play/pause
            play_control = self.bottom_bar.play_control
            play_control.set_playing(not play_control.is_playing())
            event.accept()
        else:
            super().keyPressEvent(event)

