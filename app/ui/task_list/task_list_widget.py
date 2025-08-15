# task_list_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal, Slot, QFileSystemWatcher
from task_item_widget import TaskItemWidget
from task_loader import TaskLoader, QThreadPool, TaskData
import os

class TaskListWidget(QWidget):
    task_action_signal = Signal(str, str)  # action, task_id

    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.loaded_tasks = {}  # task_id -> widget
        self.all_task_files = []
        self.current_index = 0
        self.page_size = 10
        self.loading = False

        self.thread_pool = QThreadPool.globalInstance()

        # 文件监控器
        self.watcher = QFileSystemWatcher()
        self.watcher.addPath(self.folder_path)
        self.watcher.directoryChanged.connect(self.on_directory_changed)
        self.watcher.fileChanged.connect(self.on_file_changed)

        self.init_ui()
        self.load_all_task_files()
        self.load_more_tasks()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 刷新按钮
        top_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 刷新任务")
        self.refresh_btn.clicked.connect(self.refresh_tasks)
        top_layout.addWidget(self.refresh_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)

        layout.addWidget(self.scroll_area)

        # 滚动到底部加载更多
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_scroll)

    def load_all_task_files(self):
        if not os.path.exists(self.folder_path):
            print(f"⚠️ 任务文件夹不存在: {self.folder_path}")
            return
        try:
            files = [f for f in os.listdir(self.folder_path) if f.endswith(".json")]
            self.all_task_files = sorted(files, key=lambda x: int(os.path.splitext(x)[0]), reverse=True)
        except Exception as e:
            print(f"❌ 读取任务文件夹失败: {e}")

    def load_more_tasks(self):
        if self.loading or self.current_index >= len(self.all_task_files):
            return
        self.loading = True
        loader = TaskLoader(self.folder_path, self.current_index, self.page_size)
        loader.signals.tasks_loaded.connect(self.on_tasks_loaded)
        loader.signals.load_error.connect(lambda e: print(f"❌ 加载任务失败: {e}"))
        self.thread_pool.start(loader)

    @Slot(list)
    def on_tasks_loaded(self, tasks):
        for task_data in tasks:
            if task_data.task_id in self.loaded_tasks:
                # 更新已有任务
                widget = self.loaded_tasks[task_data.task_id]
                widget.update_display(task_data)
                continue
            widget = TaskItemWidget(task_data)
            widget.pause_signal.connect(self.on_task_action)
            widget.resume_signal.connect(self.on_task_action)
            widget.retry_signal.connect(self.on_task_action)
            widget.cancel_signal.connect(self.on_task_action)
            self.scroll_layout.addWidget(widget)
            self.loaded_tasks[task_data.task_id] = widget
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
        self.clear_tasks()
        self.current_index = 0
        self.load_all_task_files()
        self.load_more_tasks()

    def clear_tasks(self):
        """清空当前任务列表"""
        for widget in self.loaded_tasks.values():
            widget.setParent(None)
            widget.deleteLater()
        self.loaded_tasks.clear()
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.takeAt(i).widget().deleteLater()

    @Slot(str)
    def on_directory_changed(self, path):
        """文件夹内容变化（新增/删除文件）"""
        print(f"📁 目录变化: {path}")
        self.refresh_tasks()  # 简化处理：全部刷新

    @Slot(str)
    def on_file_changed(self, path):
        """某个文件被修改"""
        print(f"📄 文件变化: {path}")
        filename = os.path.basename(path)
        if filename.endswith(".json"):
            # 重新加载该任务
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    task_data = TaskData.from_dict(data)
                    if task_data.task_id in self.loaded_tasks:
                        widget = self.loaded_tasks[task_data.task_id]
                        widget.update_display(task_data)
                    else:
                        # 如果是新增的，重新加载整个列表
                        self.refresh_tasks()
            except Exception as e:
                print(f"❌ 解析文件失败 {path}: {e}")