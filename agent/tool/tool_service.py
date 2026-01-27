import ast
import sys
import runpy
import io
import contextlib
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List
from .base_tool import BaseTool, ToolMetadata


class ToolService:
    """
    Service to manage and execute tools.
    Provides interfaces for executing scripts and individual tools.
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.context: Dict[str, Any] = {}
        self._register_system_tools()

    def _register_system_tools(self):
        """Register all system tools from the system module."""
        try:
            from .system import __all__ as system_tools
            import importlib

            # Dynamically register all system tools
            for tool_class_name in system_tools:
                # Import the tool class dynamically
                module = importlib.import_module('.system', package=__package__)
                tool_class = getattr(module, tool_class_name)

                # Create an instance and register it
                tool_instance = tool_class()
                self.register_tool(tool_instance)
        except ImportError:
            # If system tools are not available, continue without registering them
            pass

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

    @contextmanager
    def _sys_argv_manager(self, new_argv: list):
        """Context manager to temporarily modify sys.argv."""
        import sys
        original_argv = sys.argv[:]
        sys.argv = new_argv if new_argv is not None else ['']
        try:
            yield
        finally:
            sys.argv[:] = original_argv

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
    
    def execute_script(self, script_path: str, argv: list = None) -> Any:
        """
        Execute a script that can call various tools.

        Args:
            script_path: Absolute path to the script file to execute
            argv: Optional list of command-line arguments to pass to the script

        Returns:
            Result of the script execution (captured stdout)
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

        # Execute the script using runpy.run_path with the context managers
        try:
            # Capture stdout during script execution
            captured_output = io.StringIO()

            with self._sys_path_manager(str(project_root)), self._sys_argv_manager(argv), \
                 contextlib.redirect_stdout(captured_output):
                # Run the script with the prepared globals
                runpy.run_path(script_path, init_globals=script_globals, run_name="__main__")

            # Get the captured output
            output = captured_output.getvalue()

            # Return the captured output (strip trailing newline if present)
            return output.rstrip() if output else None
        except SyntaxError as e:
            raise ValueError(f"Syntax error in script: {str(e)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Script file not found: {script_path}")
        except Exception as e:
            raise RuntimeError(f"Error executing script: {str(e)}")

    def execute_script_content(self, script_content: str, argv: list = None) -> Any:
        """
        Execute a Python script from content string.

        Supports executing dynamically generated Python code.

        Args:
            script_content: Python code as string
            argv: Optional list of command-line arguments to pass to the script

        Returns:
            Result of the script execution (captured stdout)
        """
        import tempfile
        import os

        # Define execute_tool function for the script
        def script_execute_tool(tool_name: str, parameters: Dict[str, Any]):
            return self.execute_tool(tool_name, parameters)

        script_globals = {
            '__builtins__': __builtins__,
            'execute_tool': script_execute_tool,
        }

        # Create temp file and execute
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_script_path = f.name
            f.write(script_content)

        try:
            captured_output = io.StringIO()
            project_root = self._find_project_root(Path.cwd())

            with self._sys_path_manager(str(project_root)), self._sys_argv_manager(argv), \
                 contextlib.redirect_stdout(captured_output):
                runpy.run_path(temp_script_path, init_globals=script_globals, run_name="__main__")

            output = captured_output.getvalue()
            return output.rstrip() if output else None

        except SyntaxError as e:
            raise ValueError(f"Syntax error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Execution error: {str(e)}")
        finally:
            try:
                os.unlink(temp_script_path)
            except OSError:
                pass

    def set_context(self, context: Dict[str, Any]):
        """Set the context that will be passed to tools."""
        self.context.update(context)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())

    def get_tool_metadata(self, tool_name: str, lang: str = "en_US") -> ToolMetadata:
        """
        Get metadata for a specific tool.

        Args:
            tool_name: Name of the tool
            lang: Language code for localized metadata (e.g., "en_US", "zh_CN")

        Returns:
            ToolMetadata object containing the tool's metadata

        Raises:
            ValueError: If tool is not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        return tool.metadata(lang)

    def get_all_tools_metadata(self, lang: str = "en_US") -> List[ToolMetadata]:
        """
        Get metadata for all available tools.

        Args:
            lang: Language code for localized metadata (e.g., "en_US", "zh_CN")

        Returns:
            List of ToolMetadata objects for all available tools
        """
        return [tool.metadata(lang) for tool in self.tools.values()]

    def get_tools_metadata_by_names(self, tool_names: List[str], lang: str = "en_US") -> List[ToolMetadata]:
        """
        Get metadata for tools by their names.

        Args:
            tool_names: List of tool names to get metadata for
            lang: Language code for localized metadata (e.g., "en_US", "zh_CN")

        Returns:
            List of ToolMetadata objects for the specified tools

        Raises:
            ValueError: If any tool is not found
        """
        metadata_list = []
        for tool_name in tool_names:
            if tool_name not in self.tools:
                raise ValueError(f"Tool '{tool_name}' not found")
            tool = self.tools[tool_name]
            metadata_list.append(tool.metadata(lang))
        return metadata_list