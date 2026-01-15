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
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json


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


class SkillService:
    """
    Service class that manages skills following the Claude skill specification.
    
    Skills are organized as directories containing:
    - SKILL.md: Contains metadata (between --- markers) and knowledge
    - reference.md: Optional reference documentation
    - example.md: Optional usage examples
    - scripts/: Optional directory with executable scripts
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        """
        Initialize the SkillService.
        
        Args:
            workspace_path: Optional path to workspace where custom skills may be located
        """
        self.workspace_path = workspace_path
        self.system_skills_path = os.path.join(os.path.dirname(__file__), "system")
        self.custom_skills_path = os.path.join(workspace_path, "skills") if workspace_path else None
        
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
            
            # Parse metadata
            meta_lines = meta_str.strip().split('\n')
            meta_dict = {}
            for line in meta_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    meta_dict[key.strip()] = value.strip()
            
            # Extract required fields
            name = meta_dict.get('name')
            description = meta_dict.get('description')
            
            if not name or not description:
                print(f"Warning: Missing name or description in SKILL.md for {skill_path}")
                return None
            
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
                    if os.path.isfile(script_path):
                        scripts.append(script_path)
            
            # Create and return the skill object
            skill = Skill(
                name=name,
                description=description,
                knowledge=knowledge,
                skill_path=skill_path,
                reference=reference,
                examples=examples,
                scripts=scripts
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
        Execute a script associated with a skill.
        
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
    
    def refresh_skills(self):
        """
        Refresh the list of skills by reloading from directories.
        """
        self.skills.clear()
        self.load_skills()