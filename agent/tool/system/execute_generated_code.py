from typing import Any, Dict
from ..base_tool import BaseTool, ToolMetadata, ToolParameter


class ExecuteGeneratedCodeTool(BaseTool):
    """
    Tool to execute dynamically generated Python code.
    """

    def __init__(self):
        super().__init__(
            name="execute_generated_code",
            description="Execute dynamically generated Python code"
        )

    def metadata(self, lang: str = "en_US") -> ToolMetadata:
        """Get metadata for the execute_generated_code tool."""
        if lang == "zh_CN":
            return ToolMetadata(
                name=self.name,
                description="执行动态生成的 Python 代码",
                parameters=[
                    ToolParameter(
                        name="code",
                        description="要执行的 Python 代码",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="args",
                        description="传递给代码的参数",
                        param_type="object",
                        required=False,
                        default={}
                    ),
                ],
                return_description="返回代码的执行结果"
            )
        else:
            return ToolMetadata(
                name=self.name,
                description="Execute dynamically generated Python code",
                parameters=[
                    ToolParameter(
                        name="code",
                        description="Python code to execute",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="args",
                        description="Arguments to pass to the code",
                        param_type="object",
                        required=False,
                        default={}
                    ),
                ],
                return_description="Returns the execution result from the generated code"
            )

    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Any:
        """
        Execute dynamically generated Python code using ToolService.

        Args:
            parameters: Parameters including code and args
            context: Context containing workspace and project info

        Returns:
            Execution result from the generated code
        """
        from ..tool_service import ToolService

        code = parameters.get("code")
        args = parameters.get("args", {})

        if not code:
            return "Error: code is required"

        tool_service = ToolService()

        # Set context if provided
        if context:
            tool_service.set_context(context)

        # Build argv from args
        argv = []
        for key, value in args.items():
            argv.extend([f"--{key}", str(value)])

        try:
            result = tool_service.execute_script_content(code, argv)
            return str(result) if result is not None else ""
        except Exception as e:
            return f"Error executing generated code: {str(e)}"
