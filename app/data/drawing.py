"""
Drawing configuration model that stores the current drawing tool and its settings.
This class synchronizes with the UI drawing tools to maintain consistent state.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import yaml


@dataclass
class Drawing:
    """
    Represents the complete drawing configuration including the currently selected tool
    and its associated settings.
    """
    # The currently selected drawing tool ID (e.g., 'pen', 'brush', 'eraser', etc.)
    current_tool: str = 'pen'
    
    # Settings for each tool (tool_id -> settings mapping)
    tool_settings: Dict[str, Dict[str, Any]] = None

    def __init__(self,workspace, project):
        self.workspace = workspace
        self.project = project
        project_config = project.get_config()
        data = project_config.get('drawing', self.default_drawing_config())
        self.current_tool = data.get('current_tool', 'pen')
        self.tool_settings = data.get('tool_settings', {})

    def update_tool_setting(self, tool_id: str, setting_name: str, value: Any) -> None:
        """
        Update a specific setting value for a tool.
        
        Args:
            tool_id: The ID of the tool (e.g., 'pen', 'brush', 'eraser')
            setting_name: Name of the setting (e.g., 'size', 'color', 'opacity')
            value: The new value for the setting
        """
        if tool_id not in self.tool_settings:
            self.tool_settings[tool_id] = {}
        self.tool_settings[tool_id][setting_name] = value
    
    def get_tool_setting(self, tool_id: str, setting_name: str, default_value: Any = None) -> Any:
        """
        Get a specific setting value for a tool.
        
        Args:
            tool_id: The ID of the tool (e.g., 'pen', 'brush', 'eraser')
            setting_name: Name of the setting (e.g., 'size', 'color', 'opacity')
            default_value: Default value to return if setting doesn't exist
            
        Returns:
            The setting value or default_value if not found
        """
        return self.tool_settings.get(tool_id, {}).get(setting_name, default_value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the drawing config to a dictionary for serialization."""
        return asdict(self)
    
    def to_yaml(self):
        """Convert current_tool and tool_settings to YAML format."""
        data = {
            'current_tool': self.current_tool,
            'tool_settings': self.tool_settings
        }
        return data

    def update(self, drawing:'Drawing'):
        self.current_tool = drawing.current_tool
        self.tool_settings = drawing.tool_settings
        self.project.update_config('drawing', self.to_yaml())

    def default_drawing_config(self):
        """
        Create a default drawing configuration with sensible starting values.

        Returns:
            DrawingConfig with default values
        """
        return {
            'current_tool':'pen',
            'tool_settings':{
                'adjust': {},
                'brush': {
                    'color': '#000000',
                    'line_style': 'solid',
                    'opacity': '100',
                    'size': '5'
                },
                'eraser': {
                    'size': '20'
                },
                'move': {},
                'pen': {
                    'color': '#000000',
                    'size': '2'
                },
                'select': {},
                'shape': {
                    'line_style': 'solid',
                    'shape': 'rectangle',
                    'stroke_color': '#000000',
                    'stroke_size': '2'
                },
                'text': {
                    'font_size': '14',
                    'text_color': '#000000'
                },
                'zoom': {}
            }
        }