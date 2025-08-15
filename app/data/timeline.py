import os.path
import shutil
from pathlib import Path

from PySide6.QtGui import QPixmap, Qt

from app.data.task import TaskResult

from blinker import signal

from utils import dict_utils
from utils.yaml_utils import load_yaml


class TimelineItem:

    def __init__(self, timelinePath:str,index:int):
        self.time_line_path = timelinePath
        self.index = index
        self.image_path = os.path.join(self.time_line_path, str(self.index), "image.png")
        self.video_path = os.path.join(self.time_line_path, str(self.index), "video.mp4")
        self.config_path = os.path.join(self.time_line_path,str(self.index),"config.yaml")
        self.config = load_yaml(self.config_path)


    def get_image(self):
        original_pixmap= QPixmap(self.image_path)
        return original_pixmap

    def update_image(self, image_path:str):
        if image_path is None:
            return
        shutil.copy2(image_path, self.image_path)

    def update_video(self, video_path:str):
        if video_path is None:
            return
        shutil.copy2(video_path, self.video_path)

    def update_config(self,config_path:str):
        shutil.copy2(config_path, self.config_path)

    def get_image_path(self):
        return self.image_path

    def get_video_path(self):
        return self.video_path

    def get_preview_path(self):
        if os.path.exists(self.video_path):
            return self.video_path
        return self.image_path

    def get_prompt(self):
        return dict_utils.get_value(self.config, 'prompt')

    def get_index(self):
        return self.index

class Timeline:

    timeline_switch = signal("timeline_switch")

    def __init__(self, workspace, project, timelinePath:str):
        self.workspace = workspace
        self.project = project
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

    def connect_timeline_switch(self,func):
        self.timeline_switch.connect(func)

    def get_item_count(self):
        return self.item_count

    def get_item(self, index:int):
        return TimelineItem(self.time_line_path,index)
    
    def get_items(self):
        """Get all timeline items as a list"""
        items = []
        for i in range(1, self.item_count + 1):  # Timeline items start from index 1
            item = self.get_item(i)
            # Only add items that actually exist (have content)
            if os.path.exists(item.get_image_path()) or os.path.exists(item.get_video_path()):
                items.append(item)
        return items


    def on_task_finished(self,result:TaskResult):
        item = self.get_item(result.get_timeline_index())
        item.update_image(result.get_image_path())
        item.update_video(result.get_video_path())
        item.update_config(result.get_task().get_config_path())
    
    def refresh_count(self):
        """Refresh the item count by recounting directories"""
        try:
            p = Path(self.time_line_path)
            if not p.exists() or not p.is_dir():
                return
            directories = [item.name for item in p.iterdir() if item.is_dir()]
            self.item_count = len(directories)
        except Exception as e:
            print(f"Error refreshing timeline count: {e}")
    
    def add_item(self):
        """Add a new timeline item and return its index"""
        self.refresh_count()
        new_index = self.item_count + 1
        new_item_path = os.path.join(self.time_line_path, str(new_index))
        os.makedirs(new_item_path, exist_ok=True)
        self.add_image(new_index)
        self.refresh_count()  # Update the count
        num = self.project.config['timeline_size']
        self.project.update_config('timeline_size',num+1)
        self.project.update_config('timeline_index',num+1)
        return new_index

    def add_image(self, new_index):
        # Create a default snapshot image file if it doesn't exist
        new_item_path = os.path.join(self.time_line_path, str(new_index))
        default_snapshot_path = os.path.join(new_item_path, "image.png")
        if not os.path.exists(default_snapshot_path):
            # For now, create a blank image - we'll create a simple placeholder
            # by creating a blank QPixmap and saving it
            from PySide6.QtGui import QPixmap, QPainter, QColor
            pixmap = QPixmap(720, 1280)  # Default size
            pixmap.fill(QColor(50, 50, 50))  # Dark gray background

            painter = QPainter(pixmap)
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, f"Card {new_index}")
            painter.end()
            pixmap.save(default_snapshot_path)

    def set_item_index(self, index):
        self.project.update_config('timeline_index',index)
        item = self.get_item(index)
        self.timeline_switch.send(item)