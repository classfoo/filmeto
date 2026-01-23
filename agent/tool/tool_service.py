import ast
import sys
import runpy
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List
from .base_tool import BaseTool


class ToolService:
    """
    Service to manage and execute tools.
    Provides interfaces for executing scripts and individual tools.
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.context: Dict[str, Any] = {}

    @contextmanager
    def _sys_path_manager(self, project_root: str):
        """Context manager to temporarily add project root to sys.path."""
        original_path = sys.path.copy()
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        try:
            yield
        finally:
            sys.path[:] = original_path

    def _find_project_root(self, start_path: Path) -> Path:
        """
        Find the project root by looking for typical project markers.

        Args:
            start_path: Path to start searching from

        Returns:
            Path to the project root directory
        """
        current_path = start_path.resolve()

        # Common project root indicators
        markers = ['.git', 'setup.py', 'pyproject.toml', 'requirements.txt', 'main.py']

        while current_path.parent != current_path:  # Stop at filesystem root
            if any((current_path / marker).exists() for marker in markers):
                return current_path
            current_path = current_path.parent

        # If no markers found, return the filesystem root
        return start_path.parent
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool with the service."""
        self.tools[tool.name] = tool
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a specific tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Result of the tool execution
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        return tool.execute(parameters, self.context)
    
    def execute_script(self, script_path: str) -> Any:
        """
        Execute a script that can call various tools.

        Args:
            script_path: Absolute path to the script file to execute

        Returns:
            Result of the script execution
        """
        # Define the execute_tool function that will be available in the script
        def script_execute_tool(tool_name: str, parameters: Dict[str, Any]):
            return self.execute_tool(tool_name, parameters)

        # Prepare globals for the script execution
        script_globals = {
            '__builtins__': __builtins__,
            'execute_tool': script_execute_tool,
        }

        # Determine project root directory - look for typical project markers
        script_dir = Path(script_path).parent
        project_root = self._find_project_root(script_dir)

        # Execute the script using runpy.run_path with the context manager
        try:
            with self._sys_path_manager(str(project_root)):
                # Run the script with the prepared globals
                result_namespace = runpy.run_path(script_path, init_globals=script_globals, run_name="__main__")

                # Return the result if it's stored in a variable named 'result'
                if 'result' in result_namespace:
                    return result_namespace['result']
                else:
                    # If no explicit result, return None
                    return None
        except SyntaxError as e:
            raise ValueError(f"Syntax error in script: {str(e)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Script file not found: {script_path}")
        except Exception as e:
            raise RuntimeError(f"Error executing script: {str(e)}")
    
    def set_context(self, context: Dict[str, Any]):
        """Set the context that will be passed to tools."""
        self.context.update(context)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())