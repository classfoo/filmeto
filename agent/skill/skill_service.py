"""
Skill Service Module

Implements the SkillService class to manage skills following the Claude skill specification.
Skills are organized as directories containing a SKILL.md file with metadata and knowledge,
plus optional reference.md, example.md, and scripts/ directory.
"""
import os
import re
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import json


@dataclass
class SkillParameter:
    """Represents a parameter for a skill."""
    name: str
    param_type: str
    required: bool = False
    default: Any = None
    description: str = ""


@dataclass
class Skill:
    """
    Represents a skill with its metadata and content.
    """
    name: str
    description: str
    knowledge: str  # The detailed description part of SKILL.md
    skill_path: str
    reference: Optional[str] = None
    examples: Optional[str] = None
    scripts: Optional[List[str]] = None
    parameters: List[SkillParameter] = field(default_factory=list)

    def get_parameters_prompt(self) -> str:
        """Generate a prompt description of the skill's parameters."""
        if not self.parameters:
            return "No parameters required."
        
        lines = ["Parameters:"]
        for param in self.parameters:
            req = "(required)" if param.required else "(optional)"
            default_str = f", default: {param.default}" if param.default is not None else ""
            lines.append(f"  - {param.name} ({param.param_type}) {req}{default_str}: {param.description}")
        return "\n".join(lines)

    def get_example_call(self) -> str:
        """Generate an example JSON call for this skill."""
        args = {}
        for param in self.parameters:
            if param.required:
                if param.param_type == "string":
                    args[param.name] = f"<{param.name}>"
                elif param.param_type == "integer":
                    args[param.name] = 0
                elif param.param_type == "array":
                    args[param.name] = []
                elif param.param_type == "boolean":
                    args[param.name] = True
                else:
                    args[param.name] = f"<{param.name}>"
        
        return json.dumps({
            "type": "skill",
            "skill": self.name,
            "args": args
        }, indent=2)


class SkillService:
    """
    Service class that manages skills following the Claude skill specification.
    
    Skills are organized as directories containing:
    - SKILL.md: Contains metadata (between --- markers) and knowledge
    - reference.md: Optional reference documentation
    - example.md: Optional usage examples
    - scripts/: Optional directory with executable scripts
    """
    
    def __init__(self, workspace=None):
        """
        Initialize the SkillService.

        Args:
            workspace: Optional Workspace object where custom skills may be located
        """
        self.workspace = workspace
        self.system_skills_path = os.path.join(os.path.dirname(__file__), "system")
        self.custom_skills_path = os.path.join(workspace.workspace_path, "skills") if workspace and hasattr(workspace, 'workspace_path') else None

        # Dictionary to store loaded skills by name
        self.skills: Dict[str, Skill] = {}

        # Load all skills
        self.load_skills()
    
    def load_skills(self):
        """
        Load all skills from system and workspace directories.
        """
        # Load system skills
        self._load_skills_from_directory(self.system_skills_path, "system")
        
        # Load custom skills from workspace if available
        if self.custom_skills_path and os.path.exists(self.custom_skills_path):
            self._load_skills_from_directory(self.custom_skills_path, "custom")
    
    def _load_skills_from_directory(self, directory_path: str, skill_type: str):
        """
        Load skills from a specific directory.
        
        Args:
            directory_path: Path to directory containing skill subdirectories
            skill_type: Type of skills being loaded ('system' or 'custom')
        """
        if not os.path.exists(directory_path):
            return
        
        for skill_dir_name in os.listdir(directory_path):
            skill_path = os.path.join(directory_path, skill_dir_name)
            
            # Check if it's a directory
            if os.path.isdir(skill_path):
                skill = self._load_skill_from_directory(skill_path)
                
                if skill:
                    # If custom skill has same name as system skill, custom takes precedence
                    self.skills[skill.name] = skill
                    print(f"Loaded {skill_type} skill: {skill.name}")
    
    def _load_skill_from_directory(self, skill_path: str) -> Optional[Skill]:
        """
        Load a single skill from its directory.
        
        Args:
            skill_path: Path to the skill directory
            
        Returns:
            Skill object if successfully loaded, None otherwise
        """
        skill_md_path = os.path.join(skill_path, "SKILL.md")
        
        if not os.path.exists(skill_md_path):
            print(f"Warning: SKILL.md not found in {skill_path}")
            return None
        
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata and knowledge from SKILL.md
            meta_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
            
            if not meta_match:
                print(f"Warning: Invalid SKILL.md format in {skill_path}")
                return None
            
            meta_str = meta_match.group(1)
            knowledge = meta_match.group(2).strip()
            
            # Parse metadata using YAML for better support
            try:
                meta_dict = yaml.safe_load(meta_str) or {}
            except yaml.YAMLError:
                # Fallback to simple line parsing
                meta_dict = {}
                for line in meta_str.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        meta_dict[key.strip()] = value.strip()
            
            # Extract required fields
            name = meta_dict.get('name')
            description = meta_dict.get('description')
            
            if not name or not description:
                print(f"Warning: Missing name or description in SKILL.md for {skill_path}")
                return None
            
            # Parse parameters if present
            parameters = []
            params_data = meta_dict.get('parameters', [])
            if isinstance(params_data, list):
                for param_info in params_data:
                    if isinstance(param_info, dict):
                        param = SkillParameter(
                            name=param_info.get('name', ''),
                            param_type=param_info.get('type', 'string'),
                            required=param_info.get('required', False),
                            default=param_info.get('default'),
                            description=param_info.get('description', '')
                        )
                        parameters.append(param)
            
            # Look for optional files
            reference_path = os.path.join(skill_path, "reference.md")
            reference = None
            if os.path.exists(reference_path):
                with open(reference_path, 'r', encoding='utf-8') as f:
                    reference = f.read()
            
            example_path = os.path.join(skill_path, "example.md")
            examples = None
            if os.path.exists(example_path):
                with open(example_path, 'r', encoding='utf-8') as f:
                    examples = f.read()
            
            # Look for scripts
            scripts_dir = os.path.join(skill_path, "scripts")
            scripts = []
            if os.path.exists(scripts_dir) and os.path.isdir(scripts_dir):
                for script_file in os.listdir(scripts_dir):
                    script_path = os.path.join(scripts_dir, script_file)
                    if os.path.isfile(script_path) and script_file.endswith('.py'):
                        scripts.append(script_path)
            
            # Create and return the skill object
            skill = Skill(
                name=name,
                description=description,
                knowledge=knowledge,
                skill_path=skill_path,
                reference=reference,
                examples=examples,
                scripts=scripts,
                parameters=parameters
            )
            
            return skill
            
        except Exception as e:
            print(f"Error loading skill from {skill_path}: {e}")
            return None
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by its name.
        
        Args:
            name: Name of the skill to retrieve
            
        Returns:
            Skill object if found, None otherwise
        """
        return self.skills.get(name)
    
    def get_all_skills(self) -> List[Skill]:
        """
        Get all loaded skills.
        
        Returns:
            List of all Skill objects
        """
        return list(self.skills.values())
    
    def get_skill_names(self) -> List[str]:
        """
        Get names of all loaded skills.
        
        Returns:
            List of skill names
        """
        return list(self.skills.keys())
    
    def execute_skill_script(self, skill_name: str, script_name: str, *args) -> Optional[str]:
        """
        Execute a script associated with a skill using subprocess (legacy method).
        
        Args:
            skill_name: Name of the skill
            script_name: Name of the script to execute
            *args: Arguments to pass to the script
            
        Returns:
            Output of the script execution or None if error
        """
        skill = self.get_skill(skill_name)
        if not skill:
            print(f"Skill '{skill_name}' not found")
            return None
        
        if not skill.scripts:
            print(f"No scripts found for skill '{skill_name}'")
            return None
        
        # Find the requested script
        script_path = None
        for script in skill.scripts:
            if os.path.basename(script) == script_name:
                script_path = script
                break
        
        if not script_path:
            print(f"Script '{script_name}' not found for skill '{skill_name}'")
            return None
        
        try:
            # Execute the script with the provided arguments
            cmd = [script_path] + list(args)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error executing script '{script_path}': {e}")
            return f"Error: {e}"
        except Exception as e:
            print(f"Unexpected error executing script '{script_path}': {e}")
            return f"Error: {e}"

    def execute_skill_in_context(
        self,
        skill_name: str,
        workspace: Any = None,
        project: Any = None,
        args: Optional[Dict[str, Any]] = None,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill in-context with the provided workspace and project.
        
        This method uses the SkillExecutor to run skill scripts directly
        in the Python environment with access to workspace/project objects.
        
        Args:
            skill_name: Name of the skill to execute
            workspace: Workspace object (optional)
            project: Project object (optional)
            args: Arguments to pass to the skill
            script_name: Optional specific script to execute
            
        Returns:
            Dict with execution result
        """
        from agent.skill.skill_executor import SkillExecutor, SkillContext
        
        skill = self.get_skill(skill_name)
        if not skill:
            return {
                "success": False,
                "error": "skill_not_found",
                "message": f"Skill '{skill_name}' not found."
            }
        
        # Create the skill context
        context = SkillContext(
            workspace=workspace,
            project=project
        )
        
        # Use the executor
        executor = SkillExecutor()
        result = executor.execute_skill(skill, context, args, script_name)
        
        return result

    def get_skill_prompt_info(self, skill_name: str) -> str:
        """
        Get formatted information about a skill for use in prompts.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Formatted string describing the skill
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found."
        
        lines = [
            f"### Skill: {skill.name}",
            f"Description: {skill.description}",
            "",
            skill.get_parameters_prompt(),
            "",
            "Example call:",
            "```json",
            skill.get_example_call(),
            "```",
        ]
        
        if skill.knowledge:
            lines.extend(["", "Details:", skill.knowledge[:500] + "..." if len(skill.knowledge) > 500 else skill.knowledge])
        
        return "\n".join(lines)
    
    def refresh_skills(self):
        """
        Refresh the list of skills by reloading from directories.
        """
        self.skills.clear()
        self.load_skills()