from typing import Any, Dict, Optional, TYPE_CHECKING, AsyncGenerator
from ..base_tool import BaseTool, ToolMetadata, ToolParameter

if TYPE_CHECKING:
    from ...tool_context import ToolContext


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
                return_description="返回代码的执行结果（流式输出）"
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
                return_description="Returns the execution result from the generated code (streamed)"
            )

    async def execute_async(self, parameters: Dict[str, Any], context: Optional["ToolContext"] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute dynamically generated Python code using ToolService.execute_script_content.

        Args:
            parameters: Parameters including code and args
            context: ToolContext containing workspace and project info

        Yields:
            Dict with progress updates or final result
        """
        from ..tool_service import ToolService

        code = parameters.get("code")
        args = parameters.get("args", {})

        if not code:
            yield {"error": "code is required"}
            return

        tool_service = ToolService()

        # Build argv from args
        argv = []
        for key, value in args.items():
            argv.extend([f"--{key}", str(value)])

        try:
            # Yield progress before execution
            yield {"progress": "Executing generated code..."}

            # execute_script_content now returns the result directly (not an async generator)
            result = await tool_service.execute_script_content(
                code,
                argv,
                context,
                project_name=context.project_name if context else "",
                react_type="",
                run_id="",
                step_id=0,
            )

            # Yield the final result
            yield {"result": result}

        except Exception as e:
            yield {"error": f"Error executing generated code: {str(e)}"}

    def execute(self, parameters: Dict[str, Any], context: Optional["ToolContext"] = None) -> Any:
        """
        Synchronous entry point that returns the async generator.
        """
        return self.execute_async(parameters, context)
