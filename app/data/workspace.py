import asyncio
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.data.project import Project
from app.data.task import TaskManager, TaskResult
from utils.yaml_utils import load_yaml, save_yaml


class PromptTemplate:
    """Data model for prompt templates"""
    
    def __init__(self, id: str, icon: str, text: str, created_at: str, usage_count: int = 0):
        self.id = id
        self.icon = icon
        self.text = text
        self.created_at = created_at
        self.usage_count = usage_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'icon': self.icon,
            'text': self.text,
            'created_at': self.created_at,
            'usage_count': self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        return cls(
            id=data.get('id', ''),
            icon=data.get('icon', ''),
            text=data.get('text', ''),
            created_at=data.get('created_at', ''),
            usage_count=data.get('usage_count', 0)
        )


class PromptManager:
    """Manages prompt templates for the workspace"""
    
    def __init__(self, prompts_dir: str):
        self.prompts_dir = prompts_dir
        self._templates_cache: Optional[List[PromptTemplate]] = None
        self._ensure_prompts_directory()
    
    def _ensure_prompts_directory(self):
        """Create prompts directory if it doesn't exist"""
        Path(self.prompts_dir).mkdir(parents=True, exist_ok=True)
    
    def load_templates(self) -> List[PromptTemplate]:
        """Load all templates from storage"""
        templates = []
        prompts_path = Path(self.prompts_dir)
        
        if not prompts_path.exists():
            return templates
        
        for yaml_file in prompts_path.glob('template_*.yaml'):
            try:
                data = load_yaml(str(yaml_file))
                if data and self._validate_template_data(data):
                    template = PromptTemplate.from_dict(data)
                    templates.append(template)
            except Exception as e:
                print(f"Error loading template {yaml_file}: {e}")
        
        # Sort by usage_count (descending) then created_at (descending)
        templates.sort(key=lambda t: (-t.usage_count, t.created_at), reverse=False)
        
        self._templates_cache = templates
        return templates
    
    def _validate_template_data(self, data: Dict[str, Any]) -> bool:
        """Validate required fields in template data"""
        required_fields = ['id', 'icon', 'text', 'created_at']
        return all(field in data for field in required_fields)
    
    def add_template(self, icon_path: str, text: str) -> bool:
        """Add new template with deduplication"""
        # Load existing templates if not cached
        if self._templates_cache is None:
            self.load_templates()
        
        # Check for duplicates (exact text match)
        for template in self._templates_cache:
            if template.text == text:
                print(f"Template with text '{text}' already exists")
                return False
        
        # Generate new template
        template_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        template = PromptTemplate(
            id=template_id,
            icon=icon_path,
            text=text,
            created_at=created_at,
            usage_count=0
        )
        
        # Save to file
        file_path = os.path.join(self.prompts_dir, f'template_{template_id}.yaml')
        save_yaml(file_path, template.to_dict())
        
        # Update cache
        self._templates_cache.append(template)
        
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """Remove template from storage"""
        file_path = os.path.join(self.prompts_dir, f'template_{template_id}.yaml')
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # Update cache
                if self._templates_cache:
                    self._templates_cache = [t for t in self._templates_cache if t.id != template_id]
                
                return True
        except Exception as e:
            print(f"Error deleting template {template_id}: {e}")
        
        return False
    
    def search_templates(self, query: str) -> List[PromptTemplate]:
        """Filter templates by text match (case-insensitive)"""
        if self._templates_cache is None:
            self.load_templates()
        
        if not query:
            return self._templates_cache
        
        query_lower = query.lower()
        return [t for t in self._templates_cache if query_lower in t.text.lower()]
    
    def increment_usage(self, template_id: str):
        """Increment usage count for a template"""
        file_path = os.path.join(self.prompts_dir, f'template_{template_id}.yaml')
        
        try:
            if os.path.exists(file_path):
                data = load_yaml(file_path)
                if data:
                    data['usage_count'] = data.get('usage_count', 0) + 1
                    save_yaml(file_path, data)
                    
                    # Update cache
                    if self._templates_cache:
                        for template in self._templates_cache:
                            if template.id == template_id:
                                template.usage_count += 1
                                break
        except Exception as e:
            print(f"Error incrementing usage for template {template_id}: {e}")


class Workspace():

    def __init__(self, workspace_path:str,project_name:str):
        self.workspace_path = workspace_path
        self.project_name = project_name
        self.project_path = os.path.join(self.workspace_path,self.project_name)
        self.project = Project(self, self.project_path, self.project_name)
        
        # Initialize PromptManager
        prompts_dir = os.path.join(self.project_path, 'prompts')
        self.prompt_manager = PromptManager(prompts_dir)
        return

    def get_project(self):
        return self.project
    
    def get_prompt_manager(self) -> PromptManager:
        """Get the prompt manager instance"""
        return self.prompt_manager

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

    def submit_task(self,params):
        print(params)
        self.project.submit_task(params)

    def on_task_finished(self,result:TaskResult):
        self.project.on_task_finished(result)


