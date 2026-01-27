"""
Skill Chat Module

Provides ReAct-based streaming execution for skills.
Handles tool calling, prompt building, and script execution for skill chat operations.
"""
import os
from typing import AsyncGenerator, Any, Dict, List, Optional

from agent.skill.skill_models import Skill


class SkillChat:
    """
    Handles ReAct-based streaming execution for skills.

    This class manages the chat-style execution of skills using the ReAct framework,
    allowing skills to use tools and execute scripts dynamically.
    """

    def __init__(self, skill_service):
        """
        Initialize the SkillChat handler.

        Args:
            skill_service: The SkillService instance for executing scripts
        """
        self.skill_service = skill_service

    async def chat_stream(
        self,
        skill: Skill,
        user_message: Optional[str] = None,
        workspace: Any = None,
        project: Any = None,
        args: Optional[Dict[str, Any]] = None,
        llm_service: Any = None,
        max_steps: int = 10,
    ) -> AsyncGenerator[Any, None]:
        """通过 React 流式执行 skill

        Args:
            skill: The Skill object to execute
            user_message: Optional user message/question
            workspace: Any object (optional)
            project: Any object (optional)
            args: Arguments to pass to the skill
            llm_service: Optional LLM service
            max_steps: Maximum number of ReAct steps

        Yields:
            ReactEvent objects for skill execution progress
        """
        from agent.react import React, ReactEvent

        if llm_service is None:
            from agent.llm.llm_service import LlmService
            llm_service = LlmService(workspace)

        available_tools = self._get_available_tools_for_skill(workspace, skill)

        def build_prompt_function(user_question: str) -> str:
            return self._build_skill_react_prompt(
                skill, user_question, available_tools, args
            )

        async def tool_call_function(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
            # Handle the tool names specified in skill_react.md prompt
            if tool_name == "execute_existing_script":
                # Execute a pre-defined script from the skill
                return await self._execute_existing_script(
                    skill, tool_args.get("script_name"), tool_args.get("args", {}),
                    workspace, project, llm_service
                )
            elif tool_name == "execute_generated_script":
                # Execute dynamically generated code
                return await self._execute_generated_script(tool_args, workspace)
            else:
                # Fallback: check if skill has scripts and route accordingly
                if skill.scripts:
                    return await self._execute_existing_script(
                        skill, tool_name, tool_args, workspace, project, llm_service
                    )
                else:
                    return await self._execute_generated_script(tool_args, workspace)

        project_name = getattr(project, 'project_name', 'default_project') if project else 'default_project'
        react_instance = React(
            workspace=workspace,
            project_name=project_name,
            react_type=f"skill_{skill.name}",
            build_prompt_function=build_prompt_function,
            tool_call_function=tool_call_function,
            llm_service=llm_service,
            max_steps=max_steps,
        )

        async for event in react_instance.chat_stream(user_message or skill.description):
            yield event

    def _get_available_tools_for_skill(self, workspace, skill: Skill = None) -> List[Dict]:
        """Get available tools for skill execution.

        Args:
            workspace: Any object (optional)
            skill: The Skill object (optional) to determine available execution tools

        Returns:
            List of available tool dictionaries with name and description
        """
        from agent.tool.tool_service import ToolService
        tool_service = ToolService()
        tools = []

        # Add system tools from ToolService
        for n in tool_service.get_available_tools():
            tools.append({'name': n, 'description': f'Tool: {n}'})

        # Add skill-specific execution tools based on the prompt template
        if skill:
            if skill.scripts:
                # Skill has pre-defined scripts
                tools.append({
                    'name': 'execute_existing_script',
                    'description': 'Execute a pre-defined script from this skill. Use script_name to specify which script.'
                })
            else:
                # Skill requires code generation
                tools.append({
                    'name': 'execute_generated_script',
                    'description': 'Execute dynamically generated Python code. Provide the code in the "code" parameter and optional arguments in "args".'
                })

        return tools

    def _build_skill_react_prompt(self, skill, user_question, available_tools, args) -> str:
        """Build the skill-specific ReAct prompt.

        Args:
            skill: The Skill object
            user_question: The user's question/task
            available_tools: List of available tools
            args: Arguments for the skill

        Returns:
            The rendered prompt string
        """
        from agent.prompt.prompt_service import prompt_service
        return prompt_service.render_prompt(
            name="skill_react",
            skill={
                'name': skill.name,
                'description': skill.description,
                'knowledge': skill.knowledge,
                'parameters': [
                    {
                        'name': p.name,
                        'type': p.param_type,
                        'required': p.required,
                        'default': p.default,
                        'description': p.description
                    } for p in skill.parameters
                ],
                'has_scripts': bool(skill.scripts),
                'script_names': [os.path.basename(s) for s in (skill.scripts or [])],
            },
            user_question=user_question or skill.description,
            available_tools=available_tools,
            args=args or {},
            action_instructions=prompt_service.get_prompt_template("react_action_instructions")
        )

    async def _execute_existing_script(
        self,
        skill: Skill,
        tool_name: str,
        tool_args: Dict[str, Any],
        workspace: Any,
        project: Any,
        llm_service: Any
    ) -> Dict[str, Any]:
        """Execute an existing script for a skill.

        Args:
            skill: The Skill object
            tool_name: Name of the tool/script to execute
            tool_args: Arguments for the script
            workspace: Any object
            project: Any object
            llm_service: LLM service

        Returns:
            Dictionary with execution result
        """
        result = self._execute_skill_script(skill, tool_args, tool_name, project)
        return {"success": True, "result": result}

    async def _execute_generated_script(
        self,
        code_with_args: Dict[str, Any],
        workspace: Any
    ) -> Dict[str, Any]:
        """Execute a dynamically generated script.

        Args:
            code_with_args: Dictionary containing 'code' and optional 'args'
            workspace: Any object

        Returns:
            Dictionary with execution result
        """
        from agent.tool.tool_service import ToolService
        code = code_with_args.get('code', '')
        args = code_with_args.get('args', {})
        tool_service = ToolService()
        try:
            result = tool_service.execute_script_content(code, self._dict_to_argv(args))
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _dict_to_argv(self, args_dict: Dict[str, Any]) -> List[str]:
        """Convert a dictionary to CLI argument list.

        Args:
            args_dict: Dictionary of arguments

        Returns:
            List of command-line arguments in --key value format
        """
        argv = []
        for key, value in args_dict.items():
            argv.extend([f"--{key}", str(value)])
        return argv

    def _find_script_path(self, skill: Skill, script_name: Optional[str] = None) -> Optional[str]:
        """Find the script path for a skill.

        Args:
            skill: The Skill object
            script_name: Optional specific script to execute (uses first by default)

        Returns:
            Script path if found, None otherwise
        """
        if not skill.scripts:
            return None

        if script_name:
            for script in skill.scripts:
                if os.path.basename(script) == script_name or script.endswith(script_name):
                    return script
        else:
            # Use the first script by default
            return skill.scripts[0]

        return None

    def _build_argv_from_args(
        self,
        args: Optional[Dict[str, Any]],
        project: Any = None
    ) -> List[str]:
        """Build argv from arguments dictionary.

        Args:
            args: Arguments dictionary
            project: Optional project object for context

        Returns:
            List of command-line arguments
        """
        argv = []

        # Add project path if available
        if project and hasattr(project, 'project_path'):
            argv.extend(["--project-path", project.project_path])

        if not args:
            return argv

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

        return argv

    def _execute_skill_script(
        self,
        skill: Skill,
        args: Optional[Dict[str, Any]] = None,
        script_name: Optional[str] = None,
        project: Any = None,
        argv: Optional[list] = None
    ) -> str:
        """Execute a skill script directly using ToolService.

        Args:
            skill: The Skill object to execute
            args: Arguments to pass to the skill function
            script_name: Optional specific script to execute (uses first by default)
            project: Optional project for context
            argv: Optional command-line arguments to pass to the script

        Returns:
            String with execution result
        """
        script_path = self._find_script_path(skill, script_name)
        if not script_path or not os.path.exists(script_path):
            return f"Error: Script not found for skill '{skill.name}'."

        # Prepare argv for the script execution if not provided
        if argv is None:
            argv = self._build_argv_from_args(args, project)

        try:
            from agent.tool.tool_service import ToolService
            tool_service = ToolService()
            output = tool_service.execute_script(script_path, argv)
            return str(output) if output is not None else ""
        except Exception as e:
            return f"Error executing skill script: {str(e)}"
