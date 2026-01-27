import os
from typing import Any, Dict, Optional, TYPE_CHECKING
from ..base_tool import BaseTool, ToolMetadata, ToolParameter

if TYPE_CHECKING:
    from ...tool_context import ToolContext

class ExecuteSkillScriptTool(BaseTool):
    """
    Tool to execute a pre-defined script from a skill.
    """

    def __init__(self):
        super().__init__(
            name="execute_skill_script",
            description="Execute a pre-defined script from a skill"
        )

    def metadata(self, lang: str = "en_US") -> ToolMetadata:
        """Get metadata for the execute_skill_script tool."""
        if lang == "zh_CN":
            return ToolMetadata(
                name=self.name,
                description="执行 skill 中预定义的脚本",
                parameters=[
                    ToolParameter(
                        name="skill_path",
                        description="skill 目录路径",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="script_name",
                        description="要执行的脚本名称",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="args",
                        description="传递给脚本的参数",
                        param_type="object",
                        required=False,
                        default={}
                    ),
                ],
                return_description="返回脚本的执行结果"
            )
        else:
            return ToolMetadata(
                name=self.name,
                description="Execute a pre-defined script from a skill",
                parameters=[
                    ToolParameter(
                        name="skill_path",
                        description="Path to the skill directory",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="script_name",
                        description="Name of the script to execute",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="args",
                        description="Arguments to pass to the script",
                        param_type="object",
                        required=False,
                        default={}
                    ),
                ],
                return_description="Returns the execution result from the script"
            )

    def execute(self, parameters: Dict[str, Any], context: Optional["ToolContext"] = None) -> Any:
        """
        Execute a skill script using ToolService.

        Args:
            parameters: Parameters including skill_path, script_name, and args
            context: ToolContext containing workspace and project info

        Returns:
            Execution result from the script
        """
        from ..tool_service import ToolService

        skill_path = parameters.get("skill_path")
        script_name = parameters.get("script_name")
        args = parameters.get("args", {})

        if not skill_path or not script_name:
            return "Error: skill_path and script_name are required"

        tool_service = ToolService()

        # Find the script path
        full_script_path = os.path.join(skill_path, script_name)
        if not os.path.exists(full_script_path):
            # Try to find in scripts directory
            scripts_dir = os.path.join(skill_path, "scripts")
            full_script_path = os.path.join(scripts_dir, script_name)

        if not os.path.exists(full_script_path):
            return f"Error: Script not found at {full_script_path}"

        # Build argv from args
        argv = []
        for key, value in args.items():
            argv.extend([f"--{key}", str(value)])

        try:
            result = tool_service.execute_script(full_script_path, argv, context)
            return str(result) if result is not None else ""
        except Exception as e:
            return f"Error executing skill script: {str(e)}"
