# task_item_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class TaskItemWidget(QWidget):
    pause_signal = Signal(str)
    resume_signal = Signal(str)
    retry_signal = Signal(str)
    cancel_signal = Signal(str)

    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_id = task_data.task_id
        self.init_ui()
        self.update_display(task_data)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # 信息区
        info_layout = QVBoxLayout()
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.progress_bar)

        # 按钮区
        btn_layout = QHBoxLayout()
        self.btn_pause = QPushButton("⏸️")
        self.btn_resume = QPushButton("▶️")
        self.btn_retry = QPushButton("🔄")
        self.btn_cancel = QPushButton("❌")

        self.btn_pause.clicked.connect(lambda: self.pause_signal.emit(self.task_id))
        self.btn_resume.clicked.connect(lambda: self.resume_signal.emit(self.task_id))
        self.btn_retry.clicked.connect(lambda: self.retry_signal.emit(self.task_id))
        self.btn_cancel.clicked.connect(lambda: self.cancel_signal.emit(self.task_id))

        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_resume)
        btn_layout.addWidget(self.btn_retry)
        btn_layout.addWidget(self.btn_cancel)

        layout.addWidget(self.icon_label)
        layout.addLayout(info_layout)
        layout.addLayout(btn_layout)

    def update_display(self, task_data):
        self.title_label.setText(f"[{task_data.task_type}] {task_data.title}")
        self.progress_bar.setValue(task_data.progress)

        # 图标映射
        icon_map = {
            "download": "⬇️",
            "upload": "⬆️",
            "convert": "🔄",
            "backup": "📦",
            "sync": "🔁",
            "default": "📋"
        }
        emoji = icon_map.get(task_data.task_type, "📋")
        self.icon_label.setText(emoji)

        # 按钮状态
        status = task_data.status
        self.btn_pause.setVisible(status == "running")
        self.btn_resume.setVisible(status == "paused")
        self.btn_retry.setVisible(status == "failed")
        self.btn_cancel.setVisible(status != "completed")