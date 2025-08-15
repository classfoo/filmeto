# main.py
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from task_list_widget import TaskListWidget

TASKS_FOLDER = os.path.join(os.path.dirname(__file__), "tasks")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("无限滚动任务队列（支持刷新与监控）")
        self.resize(600, 500)

        self.task_list = TaskListWidget(TASKS_FOLDER)
        self.setCentralWidget(self.task_list)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())