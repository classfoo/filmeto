# task_list_widget.py
import json
import yaml
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal, Slot, QThreadPool
from .task_item_widget import TaskItemWidget
import os

from ..base_widget import BaseWidget, BaseTaskWidget


class TaskListWidget(BaseTaskWidget):
    task_action_signal = Signal(str, str)  # action, task_id

    def __init__(self, parent, workspace):
        super().__init__(workspace)
        self.workspace = workspace
        project = workspace.get_project()
        self.tasks_path = project.get_tasks_path()
        self.task_manager = project.task_manager  # Get the task manager from the project
        self.loaded_tasks = {}  # task_id -> widget
        self.all_task_dirs = []
        self.current_index = 0
        self.page_size = 10
        self.loading = False

        self.thread_pool = QThreadPool.globalInstance()

        # Connect to workspace task progress updates instead of using file system monitoring
        self.workspace.connect_task_progress(self.on_task_progress_update)
        self.init_ui()
        # self.load_all_task_dirs()
        # self.load_more_tasks()
        self.refresh_tasks()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Add some margins to match style

        # 设置背景色匹配右栏
        self.setStyleSheet("background-color: #292b2e;")
        
        # Set size policy to prevent expansion
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # 刷新按钮
        top_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 刷新任务")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 1px solid #505254;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #717171;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_tasks)
        top_layout.addWidget(self.refresh_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # 设置滚动区域样式 - hide scrollbars
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #1e1f22;
                background-color: #292b2e;
            }
            QScrollBar:vertical { 
                width: 0px;
            }
            QScrollBar:horizontal { 
                height: 0px;
            }
        """)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #292b2e;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(5)  # Add spacing between items
        self.scroll_area.setWidget(self.scroll_content)

        layout.addWidget(self.scroll_area)

        # 滚动到底部加载更多
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_scroll)

    def on_task_create(self,task):
        self.refresh_tasks()

    def load_all_task_dirs(self):
        # Get all task directories from TaskManager
        try:
            all_task_ids = sorted([task_id for task_id in self.task_manager.tasks.keys() if task_id.isdigit()], 
                                 key=lambda x: int(x), reverse=True)
            self.all_task_dirs = all_task_ids
        except Exception as e:
            print(f"❌ 读取任务目录失败: {e}")
            self.all_task_dirs = []

    def load_more_tasks(self):
        if self.loading:
            return
        self.loading = True
        
        # Load tasks using TaskManager instead of TaskLoader
        try:
            # Get tasks from TaskManager as Task objects
            tasks = self.task_manager.get_all_tasks(self.current_index, self.page_size)
            
            # Update the all_task_dirs if needed (for pagination control)
            all_task_ids = sorted([task_id for task_id in self.task_manager.tasks.keys() if task_id.isdigit()], 
                                 key=lambda x: int(x), reverse=True)
            self.all_task_dirs = all_task_ids
            
            # Emit the loaded tasks (run in the GUI thread)
            self.on_tasks_loaded(tasks)
            
        except Exception as e:
            print(f"❌ 加载任务失败: {e}")
            self.loading = False

    @Slot(list)
    def on_tasks_loaded(self, tasks):
        for task in tasks:
            if task.task_id in self.loaded_tasks:
                # 更新已有任务
                widget = self.loaded_tasks[task.task_id]
                widget.update_display(task)
                continue
            widget = TaskItemWidget(task)
            self.scroll_layout.addWidget(widget)
            self.loaded_tasks[task.task_id] = widget
        self.current_index += self.page_size
        self.loading = False

    def check_scroll(self, value):
        scrollbar = self.scroll_area.verticalScrollBar()
        if value >= scrollbar.maximum() - 20:  # 阈值
            self.load_more_tasks()

    def on_task_action(self):
        sender = self.sender()
        if hasattr(sender, 'task_id'):
            task_id = sender.task_id
            # 这里可以根据 sender 类型判断 action
            # 为简化，我们统一处理
            pass

    

    # ========== 新增功能 ==========

    @Slot()
    def refresh_tasks(self):
        """手动刷新：重新加载所有任务"""
        print("🔄 手动刷新任务...")
        # Reload all tasks from the task manager
        self.task_manager.load_all_tasks()
        self.clear_tasks()
        self.current_index = 0
        self.load_all_task_dirs()
        self.load_more_tasks()

    def clear_tasks(self):
        """清空当前任务列表"""
        for widget in self.loaded_tasks.values():
            widget.setParent(None)
            widget.deleteLater()
        self.loaded_tasks.clear()
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.takeAt(i).widget().deleteLater()

    def on_task_progress_update(self, progress):
        """Handle task progress updates from workspace"""
        try:
            # Extract task info from progress object
            task_progress_obj = progress  # progress is already a TaskProgress instance
            task = task_progress_obj.task
            task_id = os.path.basename(task.path)  # Extract task_id from path
            percent = task_progress_obj.percent
            logs = task_progress_obj.logs
            
            # Find the corresponding widget and update it
            if task_id in self.loaded_tasks:
                task_widget = self.loaded_tasks[task_id]
                
                # Update task properties directly
                task.percent = percent
                task.log = logs
                
                task_widget.update_display(task)
                print(f"🔄 Updated task {task_id} progress to {percent}%")
            else:
                # Task might not be loaded yet, refresh the task list if needed
                # For now we just log this case
                print(f"Progress update for unloaded task {task_id}, skipping update")
        except Exception as e:
            print(f"❌ Error handling task progress update: {e}")
            import traceback
            traceback.print_exc()