"""
Skill Executor Module

Provides in-context execution of skill scripts with proper workspace and project context.
This allows skills to access the main application's Python interfaces and resources.
"""
import importlib.util
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agent.skill.skill_service import Skill, SkillParameter
from agent.tool.tool_service import ToolService


@dataclass
class SkillContext:
    """
    Context object passed to skill execution functions.
    Provides access to workspace, project, and other resources.
    """
    workspace: Optional[Any] = None
    project: Optional[Any] = None
    screenplay_manager: Optional[Any] = None
    llm_service: Optional[Any] = None
    additional_context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # Auto-initialize screenplay_manager from project if available
        if self.screenplay_manager is None and self.project is not None:
            if hasattr(self.project, 'screenplay_manager'):
                self.screenplay_manager = self.project.screenplay_manager

        if self.additional_context is None:
            self.additional_context = {}

    def get_project_path(self) -> Optional[str]:
        """Get the project path from the context."""
        if self.project is not None:
            if hasattr(self.project, 'project_path'):
                return self.project.project_path
        return None

    def get_skill_knowledge(self) -> Optional[str]:
        """Get the skill knowledge from the additional context."""
        if self.additional_context:
            return self.additional_context.get("skill_knowledge")
        return None

    def get_skill_description(self) -> Optional[str]:
        """Get the skill description from the additional context."""
        if self.additional_context:
            return self.additional_context.get("skill_description")
        return None

    def get_skill_reference(self) -> Optional[str]:
        """Get the skill reference from the additional context."""
        if self.additional_context:
            return self.additional_context.get("skill_reference")
        return None

    def get_skill_examples(self) -> Optional[str]:
        """Get the skill examples from the additional context."""
        if self.additional_context:
            return self.additional_context.get("skill_examples")
        return None


class SkillExecutor:
    """
    Executes skill scripts in-context with proper workspace and project access.

    This class executes skill scripts exclusively using ToolService's execute_script method
    to enable skill-to-tool integration. Scripts are executed directly with parameters
    passed through the argv argument rather than using a wrapper script.
    """

    def __init__(self):
        # Initialize ToolService for script execution
        self.tool_service = ToolService()
        # We no longer cache modules since we're using ToolService
        self._loaded_modules: Dict[str, Any] = {}
        self._module_functions: Dict[str, Callable] = {}

    def execute_skill(
        self,
        skill: Skill,
        context: SkillContext,
        args: Optional[Dict[str, Any]] = None,
        script_name: Optional[str] = None,
        argv: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill with the given context and arguments using ToolService.

        Args:
            skill: The Skill object to execute
            context: SkillContext containing workspace, project, etc.
            args: Arguments to pass to the skill function
            script_name: Optional specific script to execute (uses first by default)
            argv: Optional command-line arguments to pass to the script

        Returns:
            Dict with execution result, including success status and output
        """
        if not skill.scripts:
            return {
                "success": False,
                "error": "no_scripts",
                "message": f"Skill '{skill.name}' has no executable scripts."
            }

        # Find the script to execute
        script_path = None
        if script_name:
            for script in skill.scripts:
                if os.path.basename(script) == script_name or script.endswith(script_name):
                    script_path = script
                    break
        else:
            # Use the first script by default
            script_path = skill.scripts[0]

        if not script_path or not os.path.exists(script_path):
            return {
                "success": False,
                "error": "script_not_found",
                "message": f"Script not found for skill '{skill.name}'."
            }

        # Prepare argv for the script execution if not provided
        if argv is None:
            # Convert args to command-line arguments format
            # argv[0] should be the script name when executed directly, but ToolService handles this
            argv = []

            # Add context information as arguments
            if context.project and hasattr(context.project, 'project_path'):
                argv.extend(["--project-path", context.project.project_path])

            # Add skill arguments
            if args:
                # Separate positional and named arguments
                positional_args = []
                named_args = []

                for key, value in args.items():
                    # Handle positional arguments (like plan_name in create_execution_plan)
                    if key in ['plan_name']:  # Common positional arguments
                        positional_args.append(str(value))
                    else:
                        named_args.extend([f"--{key.replace('_', '-')}", str(value)])

                # Add positional arguments first, then named arguments
                argv.extend(positional_args)
                argv.extend(named_args)

        try:
            # Execute the script directly using ToolService's execute_script with argv
            output = self.tool_service.execute_script(script_path, argv)

            # Process the output
            if output:
                # Parse the JSON output to get the actual result
                lines = output.strip().split('\n')
                # Find the last line that looks like JSON (the result we expect to be printed)
                json_line = None
                for line in reversed(lines):
                    line = line.strip()
                    if line.startswith('[') or line.startswith('{'):
                        json_line = line
                        break
                if json_line:
                    import json
                    result = json.loads(json_line)
                else:
                    # If no JSON found, return the raw output
                    result = {"success": True, "output": output}
            else:
                # If no output, return a default success result
                result = {"success": True, "message": "Skill executed successfully."}
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "message": f"Error executing skill script: {str(e)}"
            }

        return self._normalize_result(result)

    def _normalize_result(self, result: Any) -> Dict[str, Any]:
        """Normalize the skill execution result to a standard format."""
        if isinstance(result, dict):
            if 'success' not in result:
                result['success'] = True
            return result
        elif isinstance(result, str):
            return {
                "success": True,
                "output": result,
                "message": result
            }
        elif result is None:
            return {
                "success": True,
                "message": "Skill executed successfully."
            }
        else:
            return {
                "success": True,
                "output": result,
                "message": str(result)
            }

    def clear_cache(self):
        """Clear cached modules to force reload on next execution."""
        # Since we no longer cache modules, this is kept for API compatibility
        pass


# Global executor instance
_executor_instance: Optional[SkillExecutor] = None


def get_skill_executor() -> SkillExecutor:
    """Get the global SkillExecutor instance."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SkillExecutor()
    return _executor_instance