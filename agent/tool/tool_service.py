import ast
import sys
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
    
    def execute_script(self, script_code: str) -> Any:
        """
        Execute a script that can call various tools.
        
        Args:
            script_code: String containing the script code to execute
            
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
        
        # Execute the script
        try:
            # Parse the script to check for safety (basic validation)
            ast.parse(script_code)
            
            # Execute the script with access to execute_tool function
            exec(script_code, script_globals)
            
            # Return the result if it's stored in a variable named 'result'
            if 'result' in script_globals:
                return script_globals['result']
            else:
                # If no explicit result, return None or the last expression result
                return None
        except SyntaxError as e:
            raise ValueError(f"Syntax error in script: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error executing script: {str(e)}")
    
    def set_context(self, context: Dict[str, Any]):
        """Set the context that will be passed to tools."""
        self.context.update(context)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())