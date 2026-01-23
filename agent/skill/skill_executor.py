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
    to enable skill-to-tool integration. Scripts are executed through a wrapper that
    provides the necessary context and arguments to the skill functions.
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
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill with the given context and arguments using ToolService.

        Args:
            skill: The Skill object to execute
            context: SkillContext containing workspace, project, etc.
            args: Arguments to pass to the skill function
            script_name: Optional specific script to execute (uses first by default)

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


        # Prepare the execution context for the script
        # For complex objects, we'll pass minimal representations
        workspace_repr = f'"{getattr(context.workspace, "workspace_path", "")}"' if context.workspace else 'None'
        project_repr = f'"{getattr(context.project, "project_path", "")}"' if context.project else 'None'

        wrapper_script = f'''
# Prepare the skill execution context
# Note: We'll pass basic context values, but complex objects need special handling
context_dict = {{
    "workspace_path": {workspace_repr},
    "project_path": {project_repr},
    "screenplay_manager": {repr(getattr(context, 'screenplay_manager', None))},
    "llm_service": {repr(getattr(context, 'llm_service', None))},
    "additional_context": {repr(getattr(context, 'additional_context', {}))}
}}

# Prepare arguments
skill_args = {repr(args or {})}

# Execute the skill script with the context
with open("{script_path}", 'r', encoding='utf-8') as f:
    script_content = f.read()

# Execute the skill script in a namespace that includes the context
script_namespace = {{
    "__builtins__": __builtins__,
    "context_dict": context_dict,
    "skill_args": skill_args,
    "execute_tool": execute_tool  # Make sure execute_tool is available
}}

# Execute the skill script in the namespace
exec(script_content, script_namespace)

# Call the main function of the skill with context and args
# This assumes the skill script has an 'execute' function
if 'execute' in script_namespace:
    result = script_namespace['execute'](context_dict, **skill_args)
elif 'execute_in_context' in script_namespace:
    result = script_namespace['execute_in_context'](context_dict, **skill_args)
else:
    # Try to find a function matching the skill name
    skill_fn_name = "{skill.name.replace("-", "_")}"
    if skill_fn_name in script_namespace:
        result = script_namespace[skill_fn_name](**skill_args)
    else:
        # If no standard function found, return an error
        result = {{
            "success": False,
            "error": "no_entry_point",
            "message": f"No execute function found in skill '{{skill.name}}'. "
                      f"Expected 'execute(context, **kwargs)' or '{{skill_fn_name}}(...)' function."
        }}
'''

        # Create a temporary script file for the wrapper
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapper_script)
            wrapper_script_path = f.name

        try:
            # Execute the wrapper script using ToolService's execute_script
            result = self.tool_service.execute_script(wrapper_script_path)
        finally:
            # Clean up the temporary wrapper file
            os.remove(wrapper_script_path)
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