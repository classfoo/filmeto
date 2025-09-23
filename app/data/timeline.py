import os.path
import shutil
from pathlib import Path

from PySide6.QtGui import QPixmap

from app.data.task import TaskResult


class TimelineItem:

    def __init__(self, timelinePath:str,index:int):
        self.time_line_path = timelinePath
        self.index = index
        self.snapshot_path = os.path.join(self.time_line_path,str(self.index),"snapshot.png")


    def getSnapshotImage(self):
        original_pixmap= QPixmap(self.snapshot_path)
        return original_pixmap

    def update_snapshot(self,image_path:str):
        shutil.copy2(image_path, self.snapshot_path)

class Timeline:

    def __init__(self, timelinePath:str):
        self.time_line_path = timelinePath
        try:
            p = Path(self.time_line_path)
            if not p.exists():
                print(f"路径 '{self.time_line_path}' 不存在。")
                return
            if not p.is_dir():
                print(f"路径 '{self.time_line_path}' 不是一个目录。")
                return
            directories = [item.name for item in p.iterdir() if item.is_dir()]
            self.item_count = len(directories)
        except PermissionError:
            print(f"没有权限访问路径 '{self.time_line_path}'。")
            return
        except Exception as e:
            print(f"发生错误: {e}")
            return

    def itemCount(self):
        return self.item_count

    def getItem(self, index:int):
        return TimelineItem(self.time_line_path,index)


    def on_task_finished(self,result:TaskResult):
        item = self.getItem(result.get_timeline())
        item.update_snapshot(result.get_image())