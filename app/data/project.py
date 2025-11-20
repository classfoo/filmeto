import os.path
import os
from typing import List, Dict, Any
from datetime import datetime

from blinker import signal

from app.data.task import TaskManager, TaskResult
from app.data.timeline import Timeline
from app.data.drawing import Drawing
from utils.yaml_utils import load_yaml, save_yaml


class Project():

    def __init__(self, workspace, project_path:str, project_name:str, load_data:bool = True):
        self.workspace = workspace
        self.project_path = project_path
        self.project_name = project_name
        self.config = load_yaml(os.path.join(self.project_path, "project.yaml"))
        self.tasks_path = os.path.join(self.project_path,"tasks")
        self.task_manager = TaskManager(self.workspace, self, self.tasks_path)
        self.timeline =  Timeline(self.workspace, self, os.path.join(self.project_path, 'timeline'))
        self.drawing = Drawing(self.workspace, self)
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

    def get_timeline(self):
        return self.timeline

    def get_timeline_index(self):
        return self.config['timeline_index']
    
    def get_timeline_position(self) -> float:
        """获取时间线当前播放位置（秒）"""
        return self.config.get('timeline_position', 0.0)
    
    def set_timeline_position(self, position: float):
        """设置时间线当前播放位置（秒）"""
        self.update_config('timeline_position', position)
    
    def get_timeline_duration(self) -> float:
        """获取时间线总时长（秒）"""
        return self.config.get('timeline_duration', 0.0)
    
    def set_timeline_duration(self, duration: float):
        """设置时间线总时长（秒）"""
        self.update_config('timeline_duration', duration)

    def get_config(self):
        return self.config

    def update_config(self, key,value):
        self.config[key]=value
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
            "timeline_duration": 0.0
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
