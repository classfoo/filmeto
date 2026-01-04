"""Agent tools for Filmeto operations."""

from typing import Any, Dict, List, Optional, Callable
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class FilmetoToolInput(BaseModel):
    """Base input schema for Filmeto tools."""
    pass


class FilmetoBaseTool(BaseTool):
    """Base tool for Filmeto agent operations."""
    
    workspace: Any = Field(default=None, exclude=True)
    project: Any = Field(default=None, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, workspace=None, project=None, **kwargs):
        super().__init__(**kwargs)
        self.workspace = workspace
        self.project = project


# ============================================================================
# Project Information Tools
# ============================================================================

class GetProjectInfoInput(BaseModel):
    """Input for getting project information."""
    pass


class GetProjectInfoTool(FilmetoBaseTool):
    """Tool to get current project information."""
    
    name: str = "get_project_info"
    description: str = "Get information about the current project including name, timeline, and resources."
    args_schema: type[BaseModel] = GetProjectInfoInput
    
    def _run(self) -> str:
        """Get project information."""
        if not self.project:
            return "No project is currently active."
        
        config = self.project.get_config()
        timeline_index = config.get('timeline_index', 0)
        timeline_position = config.get('timeline_position', 0.0)
        timeline_duration = config.get('timeline_duration', 0.0)
        
        info = f"""Current Project Information:
- Project Name: {self.project.project_name}
- Timeline Index: {timeline_index}
- Timeline Position: {timeline_position:.2f}s
- Timeline Duration: {timeline_duration:.2f}s
- Project Path: {self.project.project_path}
"""
        return info


# ============================================================================
# Character Management Tools
# ============================================================================

class ListCharactersInput(BaseModel):
    """Input for listing characters."""
    pass


class ListCharactersTool(FilmetoBaseTool):
    """Tool to list all characters in the project."""
    
    name: str = "list_characters"
    description: str = "List all characters available in the current project."
    args_schema: type[BaseModel] = ListCharactersInput
    
    def _run(self) -> str:
        """List all characters."""
        if not self.project:
            return "No project is currently active."
        
        character_manager = self.project.get_character_manager()
        characters = character_manager.list_characters()
        
        if not characters:
            return "No characters found in the project."
        
        result = "Characters in project:\n"
        for char in characters:
            result += f"- {char['name']} (ID: {char['character_id']})\n"
            if char.get('description'):
                result += f"  Description: {char['description']}\n"
        
        return result


class GetCharacterInfoInput(BaseModel):
    """Input for getting character information."""
    character_id: str = Field(description="The ID of the character to get information about")


class GetCharacterInfoTool(FilmetoBaseTool):
    """Tool to get detailed information about a specific character."""
    
    name: str = "get_character_info"
    description: str = "Get detailed information about a specific character by ID."
    args_schema: type[BaseModel] = GetCharacterInfoInput
    
    def _run(self, character_id: str) -> str:
        """Get character information."""
        if not self.project:
            return "No project is currently active."
        
        character_manager = self.project.get_character_manager()
        character = character_manager.get_character(character_id)
        
        if not character:
            return f"Character with ID '{character_id}' not found."
        
        info = f"""Character Information:
- Name: {character.name}
- ID: {character.character_id}
- Description: {character.description or 'N/A'}
- Created: {character.created_at}
- Updated: {character.updated_at}
"""
        
        if character.reference_images:
            info += f"- Reference Images: {len(character.reference_images)}\n"
        
        if character.metadata:
            info += "\nMetadata:\n"
            for key, value in character.metadata.items():
                info += f"  - {key}: {value}\n"
        
        return info


# ============================================================================
# Resource Management Tools
# ============================================================================

class ListResourcesInput(BaseModel):
    """Input for listing resources."""
    resource_type: Optional[str] = Field(
        default=None,
        description="Filter by resource type: 'image', 'video', 'audio', or None for all"
    )


class ListResourcesTool(FilmetoBaseTool):
    """Tool to list resources in the project."""
    
    name: str = "list_resources"
    description: str = "List all resources (images, videos, audio) in the current project."
    args_schema: type[BaseModel] = ListResourcesInput
    
    def _run(self, resource_type: Optional[str] = None) -> str:
        """List resources."""
        if not self.project:
            return "No project is currently active."
        
        resource_manager = self.project.get_resource_manager()
        resources = resource_manager.list_resources()
        
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        
        if not resources:
            type_str = f" of type '{resource_type}'" if resource_type else ""
            return f"No resources{type_str} found in the project."
        
        result = f"Resources in project{' (' + resource_type + ')' if resource_type else ''}:\n"
        for res in resources:
            result += f"- {res.name} ({res.resource_type})\n"
            result += f"  ID: {res.resource_id}\n"
            result += f"  Path: {res.file_path}\n"
            if res.source_type:
                result += f"  Source: {res.source_type}\n"
        
        return result


# ============================================================================
# Timeline Tools
# ============================================================================

class GetTimelineInfoInput(BaseModel):
    """Input for getting timeline information."""
    pass


class GetTimelineInfoTool(FilmetoBaseTool):
    """Tool to get timeline information."""
    
    name: str = "get_timeline_info"
    description: str = "Get information about the current timeline state."
    args_schema: type[BaseModel] = GetTimelineInfoInput
    
    def _run(self) -> str:
        """Get timeline information."""
        if not self.project:
            return "No project is currently active."
        
        timeline = self.project.get_timeline()
        position = self.project.get_timeline_position()
        duration = self.project.get_timeline_duration()
        
        info = f"""Timeline Information:
- Current Position: {position:.2f}s
- Total Duration: {duration:.2f}s
- Timeline Index: {self.project.get_timeline_index()}
"""
        return info


# ============================================================================
# Task Management Tools
# ============================================================================

class CreateTaskInput(BaseModel):
    """Input for creating a task."""
    tool: str = Field(description="The tool to use (e.g., 'text2img', 'img2video')")
    prompt: str = Field(description="The prompt for the task")
    model: Optional[str] = Field(default=None, description="The model to use")
    additional_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional parameters for the task"
    )


class CreateTaskTool(FilmetoBaseTool):
    """Tool to create and submit a new task."""
    
    name: str = "create_task"
    description: str = "Create and submit a new AI generation task (text2img, img2video, etc.)."
    args_schema: type[BaseModel] = CreateTaskInput
    
    def _run(
        self,
        tool: str,
        prompt: str,
        model: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a task."""
        if not self.project:
            return "No project is currently active."
        
        params = {
            'tool': tool,
            'prompt': prompt
        }
        
        if model:
            params['model'] = model
        
        if additional_params:
            params.update(additional_params)
        
        try:
            self.project.submit_task(params)
            return f"Task created successfully with tool '{tool}' and prompt: {prompt[:100]}..."
        except Exception as e:
            return f"Error creating task: {str(e)}"


# ============================================================================
# Tool Registry
# ============================================================================

class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self, workspace=None, project=None):
        """Initialize tool registry."""
        self.workspace = workspace
        self.project = project
        self._tools: Dict[str, FilmetoBaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        default_tools = [
            GetProjectInfoTool,
            ListCharactersTool,
            GetCharacterInfoTool,
            ListResourcesTool,
            GetTimelineInfoTool,
            CreateTaskTool,
        ]
        
        for tool_class in default_tools:
            tool = tool_class(workspace=self.workspace, project=self.project)
            self._tools[tool.name] = tool
    
    def register_tool(self, tool: FilmetoBaseTool):
        """Register a custom tool."""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[FilmetoBaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[FilmetoBaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())
    
    def update_context(self, workspace=None, project=None):
        """Update workspace and project context for all tools."""
        if workspace is not None:
            self.workspace = workspace
        if project is not None:
            self.project = project
        
        # Update all tools
        for tool in self._tools.values():
            if workspace is not None:
                tool.workspace = workspace
            if project is not None:
                tool.project = project

