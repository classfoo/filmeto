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
        from agent.tool.tool_service import ToolService

        if llm_service is None:
            from agent.llm.llm_service import LlmService
            llm_service = LlmService(workspace)

        # Build available tool names based on skill type
        tool_service = ToolService()
        available_tool_names = list(tool_service.get_available_tools())

        # Add skill-specific tools based on whether skill has scripts
        if skill.scripts:
            available_tool_names.append("execute_skill_script")
        else:
            available_tool_names.append("execute_generated_code")

        def build_prompt_function(user_question: str) -> str:
            return self._build_skill_react_prompt(
                skill, user_question, available_tool_names, args
            )

        project_name = getattr(project, 'project_name', 'default_project') if project else 'default_project'
        react_instance = React(
            workspace=workspace,
            project_name=project_name,
            react_type=f"skill_{skill.name}",
            build_prompt_function=build_prompt_function,
            available_tool_names=available_tool_names,
            llm_service=llm_service,
            max_steps=max_steps,
        )

        # Set context for tool execution - include skill path for script execution
        if skill.scripts:
            skill_path = os.path.dirname(skill.scripts[0]) if skill.scripts else ""
            react_instance.tool_service.set_context({
                "skill": skill,
                "skill_path": skill_path,
                "workspace": workspace,
                "project": project,
                "llm_service": llm_service,
            })
        else:
            react_instance.tool_service.set_context({
                "skill": skill,
                "workspace": workspace,
                "project": project,
                "llm_service": llm_service,
            })

        async for event in react_instance.chat_stream(user_message or skill.description):
            yield event

    def _build_skill_react_prompt(self, skill, user_question, available_tool_names, args) -> str:
        """Build the skill-specific ReAct prompt.

        Args:
            skill: The Skill object
            user_question: The user's question/task
            available_tool_names: List of available tool names
            args: Arguments for the skill

        Returns:
            The rendered prompt string
        """
        from agent.prompt.prompt_service import prompt_service
        from agent.tool.tool_service import ToolService

        tool_service = ToolService()
        available_tools = [
            tool_service.get_tool_metadata(name)
            for name in available_tool_names
        ]

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
        )
