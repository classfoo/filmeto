import os.path
import os
from typing import List, Dict, Any
from datetime import datetime

from blinker import signal
from PySide6.QtCore import QTimer

from app.data.task import TaskManager, TaskResult
from app.data.timeline import Timeline
from app.data.drawing import Drawing
from utils.yaml_utils import load_yaml, save_yaml


class Project():

    timeline_position=signal('timeline_position')

    def __init__(self, workspace, project_path:str, project_name:str, load_data:bool = True):
        self.workspace = workspace
        self.project_path = project_path
        self.project_name = project_name
        self.config = load_yaml(os.path.join(self.project_path, "project.yaml"))
        self.tasks_path = os.path.join(self.project_path,"tasks")
        self.task_manager = TaskManager(self.workspace, self, self.tasks_path)
        self.timeline =  Timeline(self.workspace, self, os.path.join(self.project_path, 'timeline'))
        self.drawing = Drawing(self.workspace, self)
        
        # Debounced save mechanism for high-frequency updates (like timeline_position)
        self._pending_save = False
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)  # Save every 500ms at most
        self._save_timer.timeout.connect(self._flush_config)
        
        # 只有在load_data为True时才自动加载项目中的所有任务
        if load_data:
            self.load_all_tasks()


    async def start(self):
        await self.task_manager.start()

    def connect_task_create(self,func):
        self.task_manager.connect_task_create(func)

    def connect_task_execute(self,func):
        self.task_manager.connect_task_execute(func)

    def connect_task_progress(self,func):
        self.task_manager.connect_task_progress(func)

    def connect_task_finished(self,func):
        self.task_manager.connect_task_finished(func)

    def connect_timeline_switch(self,func):
        self.timeline.connect_timeline_switch(func)

    def connect_layer_changed(self,func):
        self.timeline.connect_layer_changed(func)
    
    def connect_timeline_changed(self, func):
        """Connect to timeline_changed signal (fired when timeline item composition completes)"""
        self.timeline.connect_timeline_changed(func)

    def connect_timeline_position(self,func):
        self.timeline_position.connect(func)

    def get_timeline(self):
        return self.timeline

    def get_timeline_index(self):
        return self.config['timeline_index']
    
    def get_timeline_position(self) -> float:
        """获取时间线当前播放位置（秒）"""
        return self.config.get('timeline_position', 0.0)
    
    def set_timeline_position(self, position: float, flush: bool = False):
        """设置时间线当前播放位置（秒）
        
        Args:
            position: 时间线位置（秒）
            flush: 是否立即写入文件（默认False，使用防抖机制）
            
        Returns:
            bool: True if position was set successfully, False if rejected due to boundary validation
        """
        # Validate boundary conditions
        if position < 0:
            return False
        
        timeline_duration = self.calculate_timeline_duration()
        if position > timeline_duration:
            return False
        
        # Round to millisecond precision
        position = round(position, 3)
        
        self.config['timeline_position'] = position
        if flush:
            # Immediate save
            self._flush_config()
        else:
            # Debounced save - mark as pending and restart timer
            self._pending_save = True
            self._save_timer.start()
        
        # Send timeline_position signal
        self.timeline_position.send(position)
        
        return True
    
    def get_timeline_duration(self) -> float:
        """获取时间线总时长（秒）"""
        return self.config.get('timeline_duration', 0.0)
    
    def set_timeline_duration(self, duration: float):
        """设置时间线总时长（秒）"""
        self.update_config('timeline_duration', duration)
    
    def get_item_duration(self, item_index: int) -> float:
        """Get duration for a specific timeline item
        
        Args:
            item_index: Timeline item index (1-based)
            
        Returns:
            float: Duration in seconds (default 1.0 if not set)
        """
        item_durations = self.config.get('timeline_item_durations', {})
        return item_durations.get(str(item_index), 1.0)
    
    def set_item_duration(self, item_index: int, duration: float):
        """Set duration for a specific timeline item
        
        Args:
            item_index: Timeline item index (1-based)
            duration: Duration in seconds
        """
        if 'timeline_item_durations' not in self.config:
            self.config['timeline_item_durations'] = {}
        self.config['timeline_item_durations'][str(item_index)] = duration
        save_yaml(os.path.join(self.project_path, "project.yaml"), self.config)
    
    def has_item_duration(self, item_index: int) -> bool:
        """Check if duration is set for a specific timeline item
        
        Args:
            item_index: Timeline item index (1-based)
            
        Returns:
            bool: True if duration is set, False otherwise
        """
        item_durations = self.config.get('timeline_item_durations', {})
        return str(item_index) in item_durations
    
    def calculate_timeline_duration(self) -> float:
        """Calculate total timeline duration by summing all item durations
        
        Returns:
            float: Total duration in seconds
        """
        item_durations = self.config.get('timeline_item_durations', {})
        return sum(item_durations.values())

    def get_config(self):
        return self.config

    def _flush_config(self):
        """Flush pending config changes to disk"""
        if self._pending_save:
            save_yaml(os.path.join(self.project_path, "project.yaml"), self.config)
            self._pending_save = False
    
    def update_config(self, key, value, debounced: bool = False):
        """更新配置项
        
        Args:
            key: 配置键
            value: 配置值
            debounced: 是否使用防抖保存（默认False，立即保存）
        """
        self.config[key] = value
        if debounced:
            self._pending_save = True
            self._save_timer.start()
        else:
            save_yaml(os.path.join(self.project_path, "project.yaml"), self.config)
    
    def get_drawing(self) -> 'Drawing':
        return self.drawing

    def submit_task(self,params):
        print(params)
        params['timeline_index'] = self.get_timeline_index()
        self.task_manager.submit_task(params)

    def on_task_finished(self,result:TaskResult):
        self.timeline.on_task_finished(result)
        self.task_manager.on_task_finished(result)

    def get_tasks_path(self):
        return self.tasks_path
    
    def load_all_tasks(self):
        """加载项目中的所有任务"""
        self.task_manager.load_all_tasks()


class ProjectManager:
    """
    管理项目支持增删改查
    """
    # 定义项目切换信号
    project_switched = signal('project_switched')
    
    def __init__(self, workspace_root_path: str):
        self.workspace_root_path = workspace_root_path
        self.projects: Dict[str, Project] = {}
        self._load_projects()
    
    def _load_projects(self):
        """加载所有项目"""
        if not os.path.exists(self.workspace_root_path):
            os.makedirs(self.workspace_root_path, exist_ok=True)
            return
        
        for item in os.listdir(self.workspace_root_path):
            project_path = os.path.join(self.workspace_root_path, item)
            if os.path.isdir(project_path):
                project_config_path = os.path.join(project_path, "project.yaml")
                if os.path.exists(project_config_path):
                    try:
                        # 这里我们假设项目目录名就是项目名
                        # 修改为不自动加载项目数据，只在需要时加载
                        project = Project(self.workspace_root_path, project_path, item, load_data=False)
                        self.projects[item] = project
                    except Exception as e:
                        print(f"加载项目 {item} 失败: {e}")
    
    def create_project(self, project_name: str) -> Project:
        """创建新项目"""
        project_path = os.path.join(self.workspace_root_path, project_name)
        
        # 检查项目是否已存在
        if project_name in self.projects:
            raise ValueError(f"项目 {project_name} 已存在")
        
        if os.path.exists(project_path):
            raise ValueError(f"项目路径 {project_path} 已存在")
        
        # 创建项目目录
        os.makedirs(project_path, exist_ok=True)
        
        # 创建项目配置文件
        project_config = {
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "timeline_index": 0,
            "task_index": 0,
            "timeline_position": 0.0,
            "timeline_duration": 0.0,
            "timeline_item_durations": {}
        }
        save_yaml(os.path.join(project_path, "project.yaml"), project_config)
        
        # 创建tasks目录
        os.makedirs(os.path.join(project_path, "tasks"), exist_ok=True)
        
        # 创建timeline目录
        os.makedirs(os.path.join(project_path, "timeline"), exist_ok=True)
        
        # 创建prompts目录
        os.makedirs(os.path.join(project_path, "prompts"), exist_ok=True)
        
        # 创建项目实例
        project = Project(self.workspace_root_path, project_path, project_name)
        self.projects[project_name] = project
        
        return project
    
    def get_project(self, project_name: str) -> Project:
        """获取项目"""
        return self.projects.get(project_name)
    
    def list_projects(self) -> List[str]:
        """列出所有项目"""
        return list(self.projects.keys())
    
    def delete_project(self, project_name: str) -> bool:
        """删除项目"""
        if project_name not in self.projects:
            return False
        
        project = self.projects[project_name]
        project_path = project.project_path
        
        # 从内存中移除
        del self.projects[project_name]
        
        # 删除项目目录（注意：这是一个危险操作，实际项目中应该考虑移到回收站）
        try:
            import shutil
            shutil.rmtree(project_path)
            return True
        except Exception as e:
            print(f"删除项目 {project_name} 失败: {e}")
            return False
    
    def update_project(self, project_name: str, new_config: Dict[str, Any]) -> bool:
        """更新项目配置"""
        if project_name not in self.projects:
            return False
        
        project = self.projects[project_name]
        for key, value in new_config.items():
            project.update_config(key, value)
        
        return True
    
    def switch_project(self, project_name: str):
        """切换项目并发送信号"""
        if project_name in self.projects:
            # 加载项目数据（如果尚未加载）
            project = self.projects[project_name]
            project.load_all_tasks()
            # 发送项目切换信号
            self.project_switched.send(project_name)
            return project
        return None
