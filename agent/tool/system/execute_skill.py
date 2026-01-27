from typing import Any, Dict, Optional
from ..base_tool import BaseTool, ToolMetadata, ToolParameter


class ExecuteSkillTool(BaseTool):
    """
    Tool to execute a skill through SkillService.
    This is a bridge tool that allows React to execute skills.
    """

    def __init__(self, skill_service=None):
        super().__init__(
            name="execute_skill",
            description="Execute a skill with given parameters"
        )
        self.skill_service = skill_service

    def metadata(self, lang: str = "en_US") -> ToolMetadata:
        """Get metadata for the execute_skill tool."""
        if lang == "zh_CN":
            return ToolMetadata(
                name=self.name,
                description="执行一个 skill",
                parameters=[
                    ToolParameter(
                        name="skill_name",
                        description="skill 名称",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="message",
                        description="用户消息",
                        param_type="string",
                        required=False
                    ),
                    ToolParameter(
                        name="args",
                        description="传递给 skill 的参数",
                        param_type="object",
                        required=False,
                        default={}
                    ),
                ],
                return_description="返回 skill 的执行结果"
            )
        else:
            return ToolMetadata(
                name=self.name,
                description="Execute a skill with given parameters",
                parameters=[
                    ToolParameter(
                        name="skill_name",
                        description="Name of the skill to execute",
                        param_type="string",
                        required=True
                    ),
                    ToolParameter(
                        name="message",
                        description="User message for the skill",
                        param_type="string",
                        required=False
                    ),
                    ToolParameter(
                        name="args",
                        description="Arguments to pass to the skill",
                        param_type="object",
                        required=False,
                        default={}
                    ),
                ],
                return_description="Returns the execution result from the skill"
            )

    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Any:
        """
        Execute a skill using SkillService.

        Args:
            parameters: Parameters including skill_name, message, and args
            context: Context containing workspace, project, llm_service, skill_service, etc.

        Returns:
            Execution result from the skill
        """
        # Prefer skill_service from context over constructor
        skill_service = None
        if context and "skill_service" in context:
            skill_service = context["skill_service"]
        elif self.skill_service:
            skill_service = self.skill_service

        if not skill_service:
            return "Error: SkillService not available"

        skill_name = parameters.get("skill_name")
        message = parameters.get("message")
        args = parameters.get("args", {})

        if not skill_name:
            return "Error: skill_name is required"

        skill = self.skill_service.get_skill(skill_name)
        if not skill:
            return f"Error: Skill '{skill_name}' not found"

        # Note: This is a simplified synchronous execution
        # For full async support, the tool system would need async support
        try:
            # Execute the skill script directly
            if skill.scripts:
                import os
                script_path = skill.scripts[0]  # Use first script
                if not os.path.exists(script_path):
                    return f"Error: Script not found at {script_path}"

                from ..tool_service import ToolService
                tool_service = ToolService()
                if context:
                    tool_service.set_context(context)

                # Build argv from args
                argv = []
                for key, value in args.items():
                    argv.extend([f"--{key}", str(value)])

                result = tool_service.execute_script(script_path, argv)
                return str(result) if result is not None else ""
            else:
                return f"Error: Skill '{skill_name}' has no executable scripts"
        except Exception as e:
            return f"Error executing skill: {str(e)}"

    def set_skill_service(self, skill_service):
        """Set the skill service for this tool."""
        self.skill_service = skill_service
