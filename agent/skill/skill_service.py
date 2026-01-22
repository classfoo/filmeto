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

    This service handles:
    - Reading skills using md_with_meta_utils for SKILL.md files
    - Creating new skills using create_skill with md_with_meta_utils
    - Updating existing skills using update_skill with md_with_meta_utils
    - Deleting skills using delete_skill
    - Managing skill lifecycle
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
            # Use md_with_meta_utils to read the SKILL.md file
            from utils.md_with_meta_utils import read_md_with_meta
            meta_dict, knowledge = read_md_with_meta(skill_md_path)
            
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

    async def execute_skill_in_context(
        self,
        skill: Skill,
        workspace: Any = None,
        project: Any = None,
        args: Optional[Dict[str, Any]] = None,
        script_name: Optional[str] = None,
        llm_service: Any = None
    ) -> Dict[str, Any]:
        """
        Execute a skill in-context with the provided workspace and project.

        This method processes the skill's knowledge section to determine execution strategy:
        1. If the skill has executable scripts, first call the LLM with knowledge to get script execution details,
           then execute the script with any updated arguments from the LLM
        2. If the skill has no scripts, use the knowledge prompt to generate output via LLM

        Args:
            skill: The Skill object to execute (contains knowledge, scripts, parameters, etc.)
            workspace: Workspace object (optional)
            project: Project object (optional)
            args: Arguments to pass to the skill
            script_name: Optional specific script to execute
            llm_service: Optional LLM service for knowledge-based execution

        Returns:
            Dict with execution result
        """
        from agent.skill.skill_executor import SkillExecutor, SkillContext

        if skill is None:
            return {
                "success": False,
                "error": "skill_not_provided",
                "message": "No skill object was provided."
            }

        # Create the skill context with additional context from knowledge
        context = SkillContext(
            workspace=workspace,
            project=project,
            llm_service=llm_service,
            additional_context={
                "skill_knowledge": skill.knowledge,
                "skill_description": skill.description,
                "skill_reference": skill.reference,
                "skill_examples": skill.examples
            }
        )

        # Determine execution strategy based on skill configuration
        if skill.scripts:
            # Strategy 1: First call the LLM with knowledge to get script execution details
            llm_result = await self._execute_skill_from_knowledge(skill, context, args, llm_service)

            # Check if the LLM provided script execution details
            if llm_result.get("success") and llm_result.get("output_type") == "llm_generated":
                # Extract the script execution details from the LLM response
                script_execution_details = llm_result.get("output", "")

                # Attempt to parse the LLM response to extract updated arguments
                # This could involve looking for JSON-formatted arguments in the response
                updated_args = self._parse_llm_response_for_args(script_execution_details, args)

                # Then execute the script with the updated arguments
                executor = SkillExecutor()
                result = executor.execute_skill(skill, context, updated_args, script_name)
            else:
                # If LLM didn't provide execution details, proceed with direct script execution
                executor = SkillExecutor()
                result = executor.execute_skill(skill, context, args, script_name)
        else:
            # Strategy 2: Use knowledge prompt to generate output via LLM
            result = await self._execute_skill_from_knowledge(skill, context, args, llm_service)

        return result

    async def _execute_skill_from_knowledge(
        self,
        skill: Skill,
        context: Any,
        args: Optional[Dict[str, Any]] = None,
        llm_service: Any = None
    ) -> Dict[str, Any]:
        """
        Execute a skill using its knowledge section as a prompt for LLM generation.

        This is used when a skill has no executable scripts but has knowledge/prompt content
        that describes how to perform the task.

        Args:
            skill: The Skill object containing knowledge/prompt
            context: SkillContext for execution
            args: Arguments to pass to the skill
            llm_service: LLM service for generating output

        Returns:
            Dict with execution result
        """
        if not skill.knowledge:
            return {
                "success": False,
                "error": "no_knowledge",
                "message": f"Skill '{skill.name}' has no knowledge content or scripts to execute."
            }

        # If no LLM service is provided, return the knowledge as guidance
        if llm_service is None:
            return {
                "success": True,
                "output_type": "knowledge_guidance",
                "knowledge": skill.knowledge,
                "description": skill.description,
                "parameters": skill.get_parameters_prompt(),
                "message": f"Skill '{skill.name}' provides the following guidance:\n\n{skill.knowledge}"
            }

        # Build prompt from skill knowledge and arguments
        prompt_parts = [
            f"You are executing the skill: {skill.name}",
            f"Description: {skill.description}",
            "",
            "## Skill Knowledge",
            skill.knowledge,
        ]

        if skill.reference:
            prompt_parts.extend(["", "## Reference", skill.reference])

        if skill.examples:
            prompt_parts.extend(["", "## Examples", skill.examples])

        if args:
            prompt_parts.extend([
                "",
                "## Input Arguments",
                json.dumps(args, indent=2, ensure_ascii=False)
            ])

        prompt = "\n".join(prompt_parts)

        try:
            # Use LLM service to generate output based on knowledge prompt
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Please execute the skill based on the knowledge and provided arguments."}
            ]

            # Use the sync completion method in a thread executor to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: llm_service.completion(
                    messages=messages,
                    temperature=0.4,
                    stream=False
                )
            )

            # Extract response content
            output = self._extract_llm_response(response)

            return {
                "success": True,
                "output_type": "llm_generated",
                "output": output,
                "message": f"Skill '{skill.name}' executed successfully via LLM."
            }

        except Exception as e:
            return {
                "success": False,
                "error": "llm_execution_error",
                "message": f"Error executing skill '{skill.name}' via LLM: {str(e)}"
            }

    def _parse_llm_response_for_args(self, response_text: str, original_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the LLM response to extract updated arguments for script execution.

        This method looks for JSON-formatted arguments in the LLM response and merges
        them with the original arguments. It handles complex nested JSON structures
        and attempts to repair malformed JSON.

        Args:
            response_text: The text response from the LLM
            original_args: The original arguments passed to the skill

        Returns:
            Updated arguments dictionary
        """
        import re
        import json
        from json import JSONDecodeError

        # First, try to find JSON within triple backticks (common in LLM responses)
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        code_block_matches = re.findall(code_block_pattern, response_text, re.DOTALL)

        for match in code_block_matches:
            try:
                parsed_json = json.loads(match)
                # If it's a dictionary with potential arguments, use it
                if isinstance(parsed_json, dict):
                    # Check if this is a skill call format and extract args if needed
                    if 'type' in parsed_json and parsed_json.get('type') == 'skill' and 'args' in parsed_json:
                        # Extract the args from the skill call format
                        skill_args = parsed_json.get('args', {})
                        # Merge with original args, giving priority to the LLM's suggestions
                        updated_args = {**original_args, **skill_args}
                        return updated_args
                    else:
                        # Merge with original args, giving priority to the LLM's suggestions
                        updated_args = {**original_args, **parsed_json}
                        return updated_args
            except JSONDecodeError:
                # If this match isn't valid JSON, continue to the next one
                continue

        # If no JSON in code blocks, try to find JSON objects in the response
        # Use a more sophisticated pattern to match nested JSON structures
        json_pattern = r'\{(?:[^{}]|(?R))*\}'

        # Since Python's re module doesn't support recursive patterns, we'll use a stack-based approach
        # to find balanced JSON objects
        json_objects = self._find_json_objects(response_text)

        for json_str in json_objects:
            try:
                parsed_json = json.loads(json_str)
                # If it's a dictionary with potential arguments, use it
                if isinstance(parsed_json, dict):
                    # Check if this is a skill call format and extract args if needed
                    if 'type' in parsed_json and parsed_json.get('type') == 'skill' and 'args' in parsed_json:
                        # Extract the args from the skill call format
                        skill_args = parsed_json.get('args', {})
                        # Merge with original args, giving priority to the LLM's suggestions
                        updated_args = {**original_args, **skill_args}
                        return updated_args
                    else:
                        # Merge with original args, giving priority to the LLM's suggestions
                        updated_args = {**original_args, **parsed_json}
                        return updated_args
            except JSONDecodeError:
                # Try to repair common JSON issues
                try:
                    repaired_json = self._repair_json(json_str)
                    parsed_json = json.loads(repaired_json)
                    # If it's a dictionary with potential arguments, use it
                    if isinstance(parsed_json, dict):
                        # Check if this is a skill call format and extract args if needed
                        if 'type' in parsed_json and parsed_json.get('type') == 'skill' and 'args' in parsed_json:
                            # Extract the args from the skill call format
                            skill_args = parsed_json.get('args', {})
                            # Merge with original args, giving priority to the LLM's suggestions
                            updated_args = {**original_args, **skill_args}
                            return updated_args
                        else:
                            # Merge with original args, giving priority to the LLM's suggestions
                            updated_args = {**original_args, **parsed_json}
                            return updated_args
                except JSONDecodeError:
                    # If this match isn't valid JSON even after repair, continue to the next one
                    continue

        # If no valid JSON arguments were found, return the original args
        return original_args

    def _find_json_objects(self, text: str) -> list:
        """
        Find all top-level JSON objects in a text string.

        Args:
            text: The input text

        Returns:
            List of JSON strings found in the text
        """
        json_strings = []
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    json_str = text[start_idx:i+1]
                    json_strings.append(json_str)
                    start_idx = -1

        return json_strings

    def _repair_json(self, json_str: str) -> str:
        """
        Attempt to repair common JSON formatting issues.

        Args:
            json_str: The potentially malformed JSON string

        Returns:
            Repaired JSON string
        """
        import re

        # Remove trailing commas before closing braces/brackets
        repaired = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Fix unquoted keys (this is a simplified approach)
        # More complex repair would require a proper parser
        repaired = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired)

        # Fix single quotes to double quotes (be careful not to replace quotes inside strings)
        # This is a simplified approach - a full solution would require more sophisticated parsing
        lines = repaired.split('\n')
        repaired_lines = []
        for line in lines:
            # Simple pattern to replace unescaped single quotes around values
            # This is a heuristic and may not work in all cases
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key_part = parts[0]
                    value_part = parts[1]

                    # Handle value part - replace single quotes with double quotes carefully
                    # Only replace if it looks like a string value that's not properly quoted
                    if value_part.strip().startswith("'") and value_part.strip().endswith("'"):
                        value_part = '"' + value_part.strip()[1:-1] + '"'
                        line = key_part + ':' + value_part
            repaired_lines.append(line)

        repaired = '\n'.join(repaired_lines)

        return repaired

    def _extract_llm_response(self, response: Any) -> str:
        """Extract content from LLM response."""
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                choice = choices[0]
                message = choice.get("message") if isinstance(choice, dict) else None
                if message and isinstance(message, dict):
                    return message.get("content", "")
                return choice.get("text", "")
            return ""
        choices = getattr(response, "choices", None)
        if choices:
            choice = choices[0]
            message = getattr(choice, "message", None)
            if message and hasattr(message, "content"):
                return message.content
            content = getattr(choice, "text", None)
            return content or ""
        return str(response)

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

    def create_skill(self, skill: Skill) -> bool:
        """
        Create a new skill using md_with_meta_utils to write the SKILL.md file.

        Args:
            skill: Skill object to create

        Returns:
            True if creation was successful, False otherwise
        """
        from utils.md_with_meta_utils import write_md_with_meta

        # Create the skill directory if it doesn't exist
        skill_dir = os.path.join(self.custom_skills_path or self.system_skills_path, skill.name)
        os.makedirs(skill_dir, exist_ok=True)

        # Prepare metadata for the skill
        metadata = {
            'name': skill.name,
            'description': skill.description,
            'parameters': [
                {
                    'name': param.name,
                    'type': param.param_type,
                    'required': param.required,
                    'default': param.default,
                    'description': param.description
                }
                for param in skill.parameters
            ]
        }

        # Write the SKILL.md file using md_with_meta_utils
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        try:
            write_md_with_meta(skill_md_path, metadata, skill.knowledge)

            # Save optional files if they exist
            if skill.reference:
                ref_path = os.path.join(skill_dir, "reference.md")
                with open(ref_path, 'w', encoding='utf-8') as f:
                    f.write(skill.reference)

            if skill.examples:
                example_path = os.path.join(skill_dir, "example.md")
                with open(example_path, 'w', encoding='utf-8') as f:
                    f.write(skill.examples)

            # Reload skills to include the new one
            self.refresh_skills()
            return True
        except Exception as e:
            print(f"Error creating skill {skill.name}: {e}")
            return False

    def update_skill(self, skill_name: str, updated_skill: Skill) -> bool:
        """
        Update an existing skill using md_with_meta_utils to update the SKILL.md file.

        Args:
            skill_name: Name of the skill to update
            updated_skill: Updated Skill object

        Returns:
            True if update was successful, False otherwise
        """
        from utils.md_with_meta_utils import update_md_with_meta

        # Find the existing skill directory
        skill_dir = None
        for dir_path in [self.system_skills_path, self.custom_skills_path]:
            if dir_path and os.path.exists(dir_path):
                candidate_path = os.path.join(dir_path, skill_name)
                if os.path.exists(candidate_path):
                    skill_dir = candidate_path
                    break

        if not skill_dir:
            print(f"Skill directory not found for {skill_name}")
            return False

        skill_md_path = os.path.join(skill_dir, "SKILL.md")

        if not os.path.exists(skill_md_path):
            print(f"SKILL.md not found for {skill_name}")
            return False

        # Prepare metadata for the updated skill
        metadata = {
            'name': updated_skill.name,
            'description': updated_skill.description,
            'parameters': [
                {
                    'name': param.name,
                    'type': param.param_type,
                    'required': param.required,
                    'default': param.default,
                    'description': param.description
                }
                for param in updated_skill.parameters
            ]
        }

        try:
            # Update the SKILL.md file using md_with_meta_utils
            success = update_md_with_meta(skill_md_path, metadata, updated_skill.knowledge)

            if success:
                # Update optional files if they exist
                if updated_skill.reference:
                    ref_path = os.path.join(skill_dir, "reference.md")
                    with open(ref_path, 'w', encoding='utf-8') as f:
                        f.write(updated_skill.reference)

                if updated_skill.examples:
                    example_path = os.path.join(skill_dir, "example.md")
                    with open(example_path, 'w', encoding='utf-8') as f:
                        f.write(updated_skill.examples)

                # Reload skills to include the updated one
                self.refresh_skills()

            return success
        except Exception as e:
            print(f"Error updating skill {skill_name}: {e}")
            return False

    def delete_skill(self, skill_name: str) -> bool:
        """
        Delete a skill by removing its directory.

        Args:
            skill_name: Name of the skill to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        import shutil

        # Find the skill directory
        skill_dir = None
        for dir_path in [self.system_skills_path, self.custom_skills_path]:
            if dir_path and os.path.exists(dir_path):
                candidate_path = os.path.join(dir_path, skill_name)
                if os.path.exists(candidate_path):
                    skill_dir = candidate_path
                    break

        if not skill_dir:
            print(f"Skill directory not found for {skill_name}")
            return False

        try:
            # Remove the entire skill directory
            shutil.rmtree(skill_dir)

            # Remove from internal cache and reload
            if skill_name in self.skills:
                del self.skills[skill_name]

            return True
        except Exception as e:
            print(f"Error deleting skill {skill_name}: {e}")
            return False