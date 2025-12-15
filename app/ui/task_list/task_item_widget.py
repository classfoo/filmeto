# task_item_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QTextEdit, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from app.ui.base_widget import BaseWidget


class TaskItemWidget(BaseWidget):
    clicked = Signal(object)  # Signal emitted when task item is clicked

    def __init__(self, task, workspace=None, parent=None):
        # 如果没有提供workspace，则不进行连接
        if workspace is not None:
            super().__init__(workspace)
        else:
            super().__init__(None)  # 这将触发错误检查
        self.task_id = task.task_id
        self.task = task
        self.is_selected = False
        # Enable hover events for highlight effect
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)  # Enable hover events
        self.init_ui()
        self.update_display(task)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)

        # 设置固定高度和尺寸策略
        self.setFixedHeight(110)
        self.setFixedWidth(190)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # 设置默认背景色
        self.setStyleSheet("""
            TaskItemWidget {
                background-color: #323436;
                border: 1px solid #505254;
                border-radius: 4px;
            }
        """)

        # 上半部分：图标、标题和进度
        top_layout = QHBoxLayout()
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #292b2e;
                border-radius: 3px;
                color: #E1E1E1;
                font-size: 12px;
            }
        """)
        # Make icon_label not intercept mouse events - let them propagate to parent
        self.icon_label.mousePressEvent = lambda e: self.mousePressEvent(e)

        # 信息区
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 8, QFont.Bold))
        self.title_label.setStyleSheet("color: #E1E1E1;")  # White text for dark theme
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(30)
        # Make title_label not intercept mouse events - let them propagate to parent
        self.title_label.mousePressEvent = lambda e: self.mousePressEvent(e)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(12)
        # Style the progress bar to match dark theme
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #505254;
                border-radius: 4px;
                background-color: #292b2e;
                text-align: center;
                color: #E1E1E1;
                font-size: 8px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                width: 20px;
            }
        """)
        # Make progress_bar not intercept mouse events - let them propagate to parent
        self.progress_bar.mousePressEvent = lambda e: self.mousePressEvent(e)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.progress_bar)

        top_layout.addWidget(self.icon_label)
        top_layout.addLayout(info_layout)
        
        # 日志输出区域
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(45)
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Monaco", 7))  # Use Monaco instead of Consolas
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #292b2e;
                border: 1px solid #505254;
                border-radius: 3px;
                color: #c0c0c0;
                font-size: 8px;
                padding: 2px;
            }
        """)
        # Make log_output not intercept mouse events - let them propagate to parent
        self.log_output.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.log_output.mousePressEvent = lambda e: self.mousePressEvent(e)

        layout.addLayout(top_layout)
        layout.addWidget(self.log_output)
        
        # Add a separator line at the bottom to create spacing
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setStyleSheet("""
            QFrame {
                color: #505254;
                background-color: #505254;
                max-height: 1px;
            }
        """)
        layout.addWidget(self.separator)
        
        # Store original background color for highlight effect
        self.original_background = "#323436"
        self.highlight_background = "#3a3c3f"  # Slightly lighter color for highlight
        self.selected_background = "#4a4c5f"   # Different color for selection

    def mousePressEvent(self, event):
        """Handle mouse click events"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)  # Emit the clicked signal with this widget as parameter

    def set_selected(self, selected):
        """Set the selected state and update appearance"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet(f"""TaskItemWidget {{
                background-color: {self.selected_background};
                border: 2px solid #ffffff;
                border-radius: 4px;
            }}""")
        else:
            self.setStyleSheet(f"""TaskItemWidget {{
                background-color: {self.original_background};
                border: 1px solid #505254;
                border-radius: 4px;
            }}""")

    def update_display(self, task):
        self.title_label.setText(f"{task.title} [{task.tool}-{task.model}]")
        self.progress_bar.setValue(task.percent)

        # 图标映射
        icon_map = {
            "download": "⬇️",
            "upload": "⬆️",
            "convert": "🔄",
            "backup": "📦",
            "sync": "🔁",
            "default": "📋",
            "text2img": "🖼️",
            "generate": "🔄"
        }
        emoji = icon_map.get(task.tool, "📋")
        self.icon_label.setText(emoji)

        # 显示日志信息（如果存在）
        if hasattr(task, 'log') and task.log:
            self.log_output.setPlainText(task.log[-1000:])  # 只显示最后1000个字符
        elif hasattr(task, 'logs') and task.logs:
            # 如果是日志列表，合并显示
            logs_text = "\n".join(task.logs[-10:])  # 显示最后10条日志
            self.log_output.setPlainText(logs_text)
        else:
            # Try to get log from config or create a simple log
            log_text = f"Task {task.task_id} - Status: {task.status}, Progress: {task.percent}%"
            self.log_output.setPlainText(log_text)

    def enterEvent(self, event):
        """当鼠标进入控件时应用高亮效果"""
        self.setStyleSheet(f"""
            TaskItemWidget {{
                background-color: {self.highlight_background};
                border: 1px solid #505254;
                border-radius: 4px;
            }}
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """当鼠标离开控件时移除高亮效果，但保持选中状态"""
        if self.is_selected:
            # Keep selected style when leaving
            self.setStyleSheet(f"""TaskItemWidget {{
                background-color: {self.selected_background};
                border: 2px solid #ffffff;
                border-radius: 4px;
            }}""")
        else:
            # Restore original style if not selected
            self.setStyleSheet(f"""
                TaskItemWidget {{
                    background-color: {self.original_background};
                    border: 1px solid #505254;
                    border-radius: 4px;
                }}
            """)
        super().leaveEvent(event)