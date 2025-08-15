import os.path
from pathlib import Path

from PySide6.QtGui import QPixmap


class TimelineItem:

    def __init__(self, timelinePath:str,index:int):
        self.time_line_path = timelinePath
        self.index = index

    def getSnapshotImage(self):
        snapshot_path = os.path.join(self.time_line_path,str(self.index),"snapshot.png")
        original_pixmap= QPixmap(snapshot_path)
        return original_pixmap

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