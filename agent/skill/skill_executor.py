"""
Skill Executor Module

Provides in-context execution of skill scripts with proper workspace and project context.
This allows skills to access the main application's Python interfaces and resources.
"""
import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agent.skill.skill_service import Skill


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
    
    This class loads skill scripts as Python modules and executes them with
    a SkillContext object, allowing skills to access the main application's
    Python interfaces without needing subprocess calls.
    """

    def __init__(self):
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
        Execute a skill with the given context and arguments.
        
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

        try:
            # Load and execute the skill module
            result = self._execute_python_skill(script_path, skill, context, args or {})
            return result
        except Exception as e:
            return {
                "success": False,
                "error": "execution_error",
                "message": f"Error executing skill '{skill.name}': {str(e)}"
            }

    def _execute_python_skill(
        self,
        script_path: str,
        skill: Skill,
        context: SkillContext,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a Python skill script in-context.
        
        The skill script should have one of:
        - execute(context, **kwargs) function
        - A main function matching the skill name (e.g., write_screenplay_outline)
        """
        # Create a unique module name based on the script path
        module_name = f"skill_{skill.name}_{os.path.basename(script_path).replace('.py', '')}"
        
        # Load the module if not already loaded
        if module_name not in self._loaded_modules:
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None or spec.loader is None:
                return {
                    "success": False,
                    "error": "load_error",
                    "message": f"Could not load skill module from '{script_path}'."
                }
            
            module = importlib.util.module_from_spec(spec)
            
            # Add the module's directory to sys.path temporarily for imports
            script_dir = os.path.dirname(script_path)
            original_path = sys.path.copy()
            
            # Add project root to path for imports
            project_root = str(Path(script_path).parents[4])
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            try:
                spec.loader.exec_module(module)
                self._loaded_modules[module_name] = module
            finally:
                # Restore original path
                sys.path = original_path
        
        module = self._loaded_modules[module_name]

        # Try to find and execute the appropriate function
        # Priority: execute() -> skill_name function -> main_function_name
        
        # 1. Try execute(context, **kwargs)
        if hasattr(module, 'execute'):
            execute_fn = getattr(module, 'execute')
            result = execute_fn(context, **args)
            return self._normalize_result(result)

        # 2. Try execute_in_context(context, **kwargs) - new standard function name
        if hasattr(module, 'execute_in_context'):
            execute_fn = getattr(module, 'execute_in_context')
            result = execute_fn(context, **args)
            return self._normalize_result(result)

        # 3. Try skill name as function (e.g., write_screenplay_outline)
        skill_fn_name = skill.name.replace('-', '_')
        if hasattr(module, skill_fn_name):
            skill_fn = getattr(module, skill_fn_name)
            # Call with context and args
            result = self._call_with_context(skill_fn, context, args)
            return self._normalize_result(result)

        # 4. Try common function names based on the script name
        script_basename = os.path.basename(script_path).replace('.py', '')
        if hasattr(module, script_basename):
            fn = getattr(module, script_basename)
            result = self._call_with_context(fn, context, args)
            return self._normalize_result(result)

        # 5. Fallback: look for any callable that looks like a main entry point
        for attr_name in ['run', 'process', 'handle']:
            if hasattr(module, attr_name):
                fn = getattr(module, attr_name)
                if callable(fn):
                    result = self._call_with_context(fn, context, args)
                    return self._normalize_result(result)

        return {
            "success": False,
            "error": "no_entry_point",
            "message": f"No execute function found in skill '{skill.name}'. "
                      f"Expected 'execute(context, **kwargs)' or '{skill_fn_name}(...)' function."
        }

    def _call_with_context(
        self,
        fn: Callable,
        context: SkillContext,
        args: Dict[str, Any]
    ) -> Any:
        """
        Call a function with context, adapting to its signature.
        
        Handles functions that:
        - Accept (context, **kwargs)
        - Accept specific named arguments
        - Accept project_path and other standard arguments
        """
        import inspect
        
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        
        # Prepare call arguments
        call_args = dict(args)
        
        # Add context-derived arguments if the function expects them
        if 'context' in params:
            call_args['context'] = context
        if 'project_path' in params and 'project_path' not in call_args:
            call_args['project_path'] = context.get_project_path()
        if 'workspace' in params and 'workspace' not in call_args:
            call_args['workspace'] = context.workspace
        if 'project' in params and 'project' not in call_args:
            call_args['project'] = context.project
        if 'screenplay_manager' in params and 'screenplay_manager' not in call_args:
            call_args['screenplay_manager'] = context.screenplay_manager

        # Filter to only include parameters the function accepts
        filtered_args = {}
        for param_name, param in sig.parameters.items():
            if param_name in call_args:
                filtered_args[param_name] = call_args[param_name]
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                # Function accepts **kwargs, pass all remaining args
                for k, v in call_args.items():
                    if k not in filtered_args:
                        filtered_args[k] = v
                break

        return fn(**filtered_args)

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
        self._loaded_modules.clear()


# Global executor instance
_executor_instance: Optional[SkillExecutor] = None


def get_skill_executor() -> SkillExecutor:
    """Get the global SkillExecutor instance."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SkillExecutor()
    return _executor_instance
