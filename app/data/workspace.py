import asyncio
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path

from app.data.project import Project, ProjectManager
from app.data.task import TaskResult
from app.data.prompt import PromptManager, PromptTemplate
from app.data.settings import Settings
from utils.yaml_utils import load_yaml, save_yaml


class Workspace():

    def __init__(self, workspace_path: str, project_name: str):
        self.workspace_path = workspace_path
        self.project_name = project_name
        self.project_path = os.path.join(self.workspace_path, self.project_name)
        self.project = Project(self, self.project_path, self.project_name, load_data=True)

        # 初始化ProjectManager
        self.project_manager = ProjectManager(workspace_path)

        # Initialize PromptManager
        prompts_dir = os.path.join(self.project_path, 'prompts')
        self.prompt_manager = PromptManager(prompts_dir)

        # Initialize Settings
        self.settings = Settings(workspace_path)

        # Initialize Plugins once for the entire workspace
        from app.plugins.plugins import Plugins
        self.plugins = Plugins(self)
        return

    def get_project(self):
        return self.project

    def get_project_manager(self):
        return self.project_manager

    def get_prompt_manager(self) -> PromptManager:
        """Get the prompt manager instance"""
        return self.prompt_manager
    
    def get_settings(self) -> Settings:
        """Get the settings instance"""
        return self.settings

    async def start(self):
        await self.project.start()

    def connect_task_create(self, func):
        self.project.connect_task_create(func)

    def connect_task_execute(self, func):
        self.project.connect_task_execute(func)

    def connect_task_progress(self, func):
        self.project.connect_task_progress(func)

    def connect_task_finished(self, func):
        self.project.connect_task_finished(func)

    def connect_timeline_switch(self, func):
        self.project.connect_timeline_switch(func)

    def connect_layer_changed(self, func):
        self.project.connect_layer_changed(func)

    def connect_project_switched(self, func: Callable):
        self.project_manager.project_switched.connect(func)

    def connect_timeline_position(self, func: Callable):
        self.project.connect_timeline_position(func)

    def submit_task(self,params):
        print(params)
        self.project.submit_task(params)

    def on_task_finished(self,result:TaskResult):
        self.project.on_task_finished(result)

    def switch_project(self, project_name: str):
        """切换到指定项目"""
        # 更新项目路径和名称
        self.project_name = project_name
        self.project_path = os.path.join(self.workspace_path, project_name)
        
        # 创建新项目实例（不自动加载数据）
        new_project = Project(self, self.project_path, project_name, load_data=False)
        
        # 替换当前项目
        self.project = new_project
        
        # 更新PromptManager
        prompts_dir = os.path.join(self.project_path, 'prompts')
        self.prompt_manager = PromptManager(prompts_dir)
        
        # 使用ProjectManager切换项目并发送信号
        # 注意：必须在更新完所有状态后再发送信号，确保监听者能获取到正确的项目状态
        switched_project = self.project_manager.switch_project(project_name)
        
        print(f"切换到项目: {project_name}")
        return self.project

    def get_current_timeline_item(self):
        return self.project.get_timeline().get_current_item()
