import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import yaml

from agent.chat.agent_chat_message import AgentMessage, StructureContent
from agent.chat.agent_chat_signals import AgentChatSignals
from agent.chat.agent_chat_types import ContentType, MessageType
from agent.llm.llm_service import LlmService
from agent.plan.models import PlanTask, TaskStatus
from agent.plan.service import PlanService
from agent.skill.skill_service import SkillService, Skill
from agent.soul import soul_service as soul_service_instance, SoulService
from agent.prompt.prompt_service import prompt_service

# Import the new React module
from agent.react.react import React
from agent.react.types import ReactEvent, ReactEventType
from agent.react.react_service import react_service


@dataclass
class CrewMemberConfig:
    name: str
    description: str = ""
    soul: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    prompt: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.4
    max_steps: int = 5
    color: str = "#4a90e2"  # Default color for the agent's icon
    icon: str = "🤖"  # Default icon for the agent
    metadata: Dict[str, Any] = field(default_factory=dict)
    config_path: Optional[str] = None

    @classmethod
    def from_markdown(cls, file_path: str) -> "CrewMemberConfig":
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        metadata, prompt = _parse_frontmatter(content)
        name = metadata.get("name") or os.path.splitext(os.path.basename(file_path))[0]
        description = metadata.get("description", "")
        soul = metadata.get("soul")
        skills = _normalize_list(metadata.get("skills", []))
        model = metadata.get("model", "gpt-4o-mini")
        temperature = float(metadata.get("temperature", 0.4))
        max_steps = int(metadata.get("max_steps", 5))
        color = metadata.get("color", "#4a90e2")  # Get color from metadata, default to blue
        icon = metadata.get("icon", "🤖")  # Get icon from metadata, default to robot

        return cls(
            name=name,
            description=description,
            soul=soul,
            skills=skills,
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_steps=max_steps,
            color=color,
            icon=icon,
            metadata=metadata,
            config_path=file_path,
        )


@dataclass
class CrewMemberAction:
    action_type: str
    response: Optional[str] = None
    skill: Optional[str] = None
    script: Optional[str] = None
    args: Optional[Any] = None
    plan_id: Optional[str] = None
    plan_update: Optional[Dict[str, Any]] = None
    thinking: Optional[str] = None
    raw: Optional[str] = None


class CrewMember:
    """
    A ReAct-style crew member driven by LLM and skill execution.
    """

    def __init__(
        self,
        config_path: str,
        workspace: Optional[Any] = None,
        project: Optional[Any] = None,
        llm_service: Optional[LlmService] = None,
        skill_service: Optional[SkillService] = None,
        soul_service: Optional[SoulService] = None,
        plan_service: Optional[PlanService] = None,
    ):
        self.config = CrewMemberConfig.from_markdown(config_path)
        self.workspace = workspace
        self.project = project
        self.project_name = _resolve_project_name(project) or getattr(project, 'project_name', 'default_project')
        self.llm_service = llm_service or LlmService(workspace)
        self.skill_service = skill_service or SkillService(workspace)
        self.plan_service = plan_service or PlanService()
        # Set the workspace if available to ensure proper plan storage location
        if workspace:
            self.plan_service.set_workspace(workspace)
        self.soul_service = soul_service or self._build_soul_service(project)
        self.conversation_history: List[Dict[str, str]] = []
        self.signals = AgentChatSignals()

    async def chat_stream(
        self,
        message: str,
        on_token: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        plan_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        # Create a React instance to handle the ReAct loop
        async def tool_call_function(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
            # Map the skill execution to the new React module
            if tool_name == "skill":
                # Extract skill name and args from tool_args
                skill_name = tool_args.get("skill_name") or tool_args.get("name")
                skill_args = tool_args.get("args") or tool_args.get("arguments") or {}

                if skill_name:
                    action = CrewMemberAction(
                        action_type="skill",
                        skill=skill_name,
                        args=skill_args
                    )
                    result = await self._execute_skill_with_structured_content(
                        action,
                        message_id=getattr(self, "_current_message_id", None),
                    )
                    return {"result": result}

            # If it's not a skill, return an error
            return {"error": f"Unknown tool: {tool_name}"}

        # Define a build_prompt_function that uses the crew member's _build_user_prompt method
        def build_prompt_function(user_input: str) -> str:
            return self._build_user_prompt(user_input, plan_id=plan_id)

        # Get or create the React instance using the ReactService for reuse
        react_instance = react_service.get_or_create_react(
            project_name=self.project_name,
            react_type=self.config.name,  # Use crew member name as react type
            build_prompt_function=build_prompt_function,  # Use the dynamic prompt builder
            react_tool_call_function=tool_call_function,
            workspace=self.workspace,
            llm_service=self.llm_service,
            max_steps=self.config.max_steps
        )

        # Stream the events from the React instance
        final_response = ""
        async for event in react_instance.chat_stream(message):
            # Handle different event types
            if event.event_type == ReactEventType.LLM_THINKING:
                # Send thinking event to UI
                thinking_structure = StructureContent(
                    content_type=ContentType.THINKING,
                    data=event.payload.get("message", ""),
                    title="Thinking Process",
                    description="Agent's thought process",
                )
                mid = getattr(self, "_current_message_id", None)
                meta = {"session_id": getattr(self, "_session_id", "unknown")}
                if mid:
                    meta["message_id"] = mid
                msg = AgentMessage(
                    message_type=MessageType.THINKING,
                    sender_id=self.config.name,
                    sender_name=self.config.name,
                    metadata=meta,
                    structured_content=[thinking_structure],
                    message_id=mid or None,
                )
                if mid:
                    msg.message_id = mid
                await self.signals.send_agent_message(msg)

            elif event.event_type == ReactEventType.TOOL_START:
                # Send tool start event to UI
                tool_start = StructureContent(
                    content_type=ContentType.SKILL,
                    data={
                        "status": "starting",
                        "skill_name": event.payload.get("tool_name", ""),
                        "message": f"Starting skill: {event.payload.get('tool_name', '')}",
                    },
                    title=f"Skill: {event.payload.get('tool_name', '')}",
                    description="Skill execution starting",
                )
                meta = {"session_id": getattr(self, "_session_id", "unknown")}
                msg = AgentMessage(
                    message_type=MessageType.SYSTEM,
                    sender_id=self.config.name,
                    sender_name=self.config.name,
                    metadata=meta,
                    structured_content=[tool_start],
                )
                await self.signals.send_agent_message(msg)

            elif event.event_type == ReactEventType.TOOL_END:
                # Send tool end event to UI
                success = event.payload.get("ok", False)
                result_message = event.payload.get("result", "") if success else event.payload.get("error", "")
                skill_end = StructureContent(
                    content_type=ContentType.SKILL,
                    data={
                        "status": "completed",
                        "skill_name": event.payload.get("tool_name", ""),
                        "message": result_message,
                        "result": result_message,
                        "success": success,
                    },
                    title=f"Skill: {event.payload.get('tool_name', '')}",
                    description="Skill execution completed",
                )
                meta = {"session_id": getattr(self, "_session_id", "unknown")}
                msg = AgentMessage(
                    message_type=MessageType.SYSTEM,
                    sender_id=self.config.name,
                    sender_name=self.config.name,
                    metadata=meta,
                    structured_content=[skill_end],
                )
                await self.signals.send_agent_message(msg)

            elif event.event_type == ReactEventType.LLM_OUTPUT:
                # Send LLM output to UI
                content = event.payload.get("content", "")
                if on_token:
                    on_token(content)
                yield content

            elif event.event_type == ReactEventType.FINAL:
                # Capture final response
                final_response = event.payload.get("final_response", "")
                break

            elif event.event_type == ReactEventType.ERROR:
                # Handle error
                error_message = event.payload.get("error", "Unknown error occurred")
                if on_token:
                    on_token(error_message)
                yield error_message
                break

        # Add the conversation to history
        self.conversation_history.append({"role": "user", "content": message})
        if final_response:
            self.conversation_history.append({"role": "assistant", "content": final_response})

        if on_complete:
            on_complete(final_response)

    def _build_user_prompt(self, user_question: str, plan_id: Optional[str] = None) -> str:
        """Build a user prompt that embeds the user's question into the react_base template."""
        soul_content = self._get_formatted_soul_prompt()

        # Prepare skills as structured data for the template
        skills_list = self._get_skills_as_structured_list()

        # Add the user's question to the context info
        context_info_parts = []
        if plan_id:
            context_info_parts.append(f"Active plan id: {plan_id}.")
        elif self.project_name:
            context_info_parts.append(f"Project name: {self.project_name}.")

        # Add the user's question to the context
        context_info_parts.append(f"User's question: {user_question}")
        context_info = " ".join(context_info_parts)

        user_prompt = prompt_service.render_prompt(
            name="react_base",
            title="crew member",
            agent_name=self.config.name,
            role_description=f"Role description: {self.config.description}" if self.config.description else "",
            soul_profile=soul_content,
            available_skills=self._format_skills_prompt(),  # Fallback for backward compatibility
            skills_list=skills_list,
            context_info=context_info,
            action_instructions=prompt_service.get_prompt_template("react_action_instructions")
        )

        # If the base prompt template is not available, fall back to the original method
        if user_prompt is None:
            prompt_sections = [
                "You are a ReAct-style crew member.",
                f"Crew member name: {self.config.name}.",
            ]
            if self.config.description:
                prompt_sections.append(f"Role description: {self.config.description}")
            if self.config.prompt:
                prompt_sections.append(self.config.prompt.strip())

            if soul_content.strip():
                prompt_sections.append("Soul profile:")
                prompt_sections.append(soul_content)

            skills_prompt = self._format_skills_prompt()
            prompt_sections.append(skills_prompt)

            # Include context info with user question
            prompt_sections.append(context_info)

            # Use the prompt template instead of the hardcoded constant
            action_instructions = prompt_service.get_prompt_template("react_action_instructions")
            prompt_sections.append(action_instructions)
            user_prompt = "\n\n".join(section for section in prompt_sections if section)

        return user_prompt

    def _build_soul_service(self, project: Optional[Any]) -> 'SoulService':
        # Return the singleton instance
        # The singleton is configured elsewhere with the workspace
        return soul_service_instance

    def _build_system_prompt(self, plan_id: Optional[str] = None) -> str:
        # Use the prompt service to get the base ReAct template
        soul_content = self._get_formatted_soul_prompt()

        # Prepare skills as structured data for the template
        skills_list = self._get_skills_as_structured_list()

        base_prompt = prompt_service.render_prompt(
            name="react_base",
            title="crew member",
            agent_name=self.config.name,
            role_description=f"Role description: {self.config.description}" if self.config.description else "",
            soul_profile=soul_content,
            available_skills=self._format_skills_prompt(),  # Fallback for backward compatibility
            skills_list=skills_list,
            context_info=f"Active plan id: {plan_id}." if plan_id else f"Project name: {self.project_name}." if self.project_name else "",
            action_instructions=prompt_service.get_prompt_template("react_action_instructions")
        )

        # If the base prompt template is not available, fall back to the original method
        if base_prompt is None:
            prompt_sections = [
                "You are a ReAct-style crew member.",
                f"Crew member name: {self.config.name}.",
            ]
            if self.config.description:
                prompt_sections.append(f"Role description: {self.config.description}")
            if self.config.prompt:
                prompt_sections.append(self.config.prompt.strip())

            if soul_content.strip():
                prompt_sections.append("Soul profile:")
                prompt_sections.append(soul_content)

            skills_prompt = self._format_skills_prompt()
            prompt_sections.append(skills_prompt)

            if plan_id:
                prompt_sections.append(f"Active plan id: {plan_id}.")
            elif self.project_name:
                prompt_sections.append(f"Project name: {self.project_name}.")

            # Use the prompt template instead of the hardcoded constant
            action_instructions = prompt_service.get_prompt_template("react_action_instructions")
            prompt_sections.append(action_instructions)
            return "\n\n".join(section for section in prompt_sections if section)

        return base_prompt

    def _get_skills_as_structured_list(self) -> list:
        """Get skills as a structured list for advanced templating."""
        if not self.config.skills:
            # If no skills are configured for this crew member, fall back to all available skills
            return self._get_all_available_skills_as_structured_list()

        skills_list = []
        for name in self.config.skills:
            skill = self.skill_service.get_skill(name)
            if not skill:
                continue  # Skip unavailable skills

            # Extract usage criteria from knowledge if available
            usage_criteria = ""
            if skill.knowledge:
                knowledge_lines = skill.knowledge.split('\n')
                for line in knowledge_lines[:10]:  # Check first 10 lines for use cases
                    line_lower = line.lower().strip()
                    if any(keyword in line_lower for keyword in ['when', 'use', 'should', 'can', 'capability', 'feature']):
                        if any(char in line for char in ['-', '*', '•']):
                            usage_criteria = line.strip(' -•*')
                            break
                if not usage_criteria:
                    usage_criteria = skill.description

            skills_list.append({
                'name': skill.name,
                'description': skill.description,
                'usage_criteria': usage_criteria,
                'parameters': [
                    {
                        'name': param.name,
                        'type': param.param_type,
                        'required': param.required,
                        'default': param.default,
                        'description': param.description
                    } for param in skill.parameters
                ],
                'example_call': skill.get_example_call()
                # Exclude knowledge field to keep the prompt concise
            })

        return skills_list

    def _get_all_available_skills_as_structured_list(self) -> list:
        """Get all available skills as a structured list for advanced templating."""
        all_skills = self.skill_service.get_all_skills()

        skills_list = []
        for skill in all_skills:  # all_skills is a list, not a dict
            # Extract usage criteria from knowledge if available
            usage_criteria = ""
            if skill.knowledge:
                knowledge_lines = skill.knowledge.split('\n')
                for line in knowledge_lines[:10]:  # Check first 10 lines for use cases
                    line_lower = line.lower().strip()
                    if any(keyword in line_lower for keyword in ['when', 'use', 'should', 'can', 'capability', 'feature']):
                        if any(char in line for char in ['-', '*', '•']):
                            usage_criteria = line.strip(' -•*')
                            break
                if not usage_criteria:
                    usage_criteria = skill.description

            skills_list.append({
                'name': skill.name,
                'description': skill.description,
                'usage_criteria': usage_criteria,
                'parameters': [
                    {
                        'name': param.name,
                        'type': param.param_type,
                        'required': param.required,
                        'default': param.default,
                        'description': param.description
                    } for param in skill.parameters
                ],
                'example_call': skill.get_example_call()
                # Exclude knowledge field to keep the prompt concise
            })

        return skills_list

    def _get_formatted_soul_prompt(self) -> str:
        """Get formatted soul prompt for use in system prompt."""
        if not self.config.soul:
            return ""
        soul = self.soul_service.get_soul_by_name(self.project_name, self.config.soul)
        if not soul:
            return f"Soul '{self.config.soul}' not found."
        if soul.knowledge:
            return soul.knowledge
        return f"Soul '{self.config.soul}' has no prompt content."

    def _get_soul_prompt(self) -> str:
        if not self.config.soul:
            return ""
        soul = self.soul_service.get_soul_by_name(self.project_name, self.config.soul)
        if not soul:
            return f"Soul '{self.config.soul}' not found."
        if soul.knowledge:
            return soul.knowledge
        return f"Soul '{self.config.soul}' has no prompt content."

    def _format_skills_prompt(self) -> str:
        if not self.config.skills:
            # If no skills are configured for this crew member, fall back to all available skills
            return self._get_all_available_skills_prompt()

        details = []
        missing = []
        for name in self.config.skills:
            skill = self.skill_service.get_skill(name)
            if not skill:
                missing.append(name)
                continue
            details.append(_format_skill_entry_detailed(skill))

        if not details:
            # If none of the configured skills are available, fall back to all available skills
            return self._get_all_available_skills_prompt()
        else:
            skills_section = (
                "## Available Skills\n\n"
                "You have access to the following skills. Review each skill's purpose and parameters to decide when to use it.\n\n"
                + "\n\n".join(details)
            )

        if missing:
            skills_section += f"\n\nNote: The following skills are configured but not available: {', '.join(missing)}"

        return skills_section

    def _get_all_available_skills_prompt(self) -> str:
        """Get a prompt with all available skills in the project as a fallback."""
        all_skills = self.skill_service.get_all_skills()

        if not all_skills:
            return "Available skills: none.\nYou cannot call any skills."

        details = []
        for skill in all_skills:  # all_skills is a list, not a dict
            details.append(_format_skill_entry_detailed(skill))

        if not details:
            return "Available skills: none.\nYou cannot call any skills."

        return (
            "## Available Skills\n\n"
            "You have access to the following skills. Review each skill's purpose and parameters to decide when to use it.\n\n"
            + "\n\n".join(details)
        )

    async def _complete(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Use the sync completion method in a thread executor to avoid async conflicts
            # This prevents the Qt async loop from interfering with LiteLLM's internal async operations
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_service.completion(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    stream=False,
                )
            )
            return _extract_response_content(response)
        except Exception as exc:
            return f"Error calling LLM: {exc}"

    def _parse_action(self, response_text: str) -> CrewMemberAction:
        payload = _extract_json_payload(response_text)
        if not payload:
            return CrewMemberAction(action_type="final", response=response_text, raw=response_text)

        action_type = payload.get("type") or payload.get("action") or "final"
        action_type = str(action_type).strip().lower()
        if action_type not in {"final", "skill"}:
            action_type = "final"

        # Extract thinking if present in the payload
        thinking = payload.get("thinking") or payload.get("thought") or payload.get("reasoning")

        return CrewMemberAction(
            action_type=action_type,
            response=payload.get("response") or payload.get("final"),
            skill=payload.get("skill") or payload.get("tool"),
            script=payload.get("script"),
            args=payload.get("args") or payload.get("arguments") or payload.get("input"),
            thinking=thinking,
            raw=response_text,
        )

    async def _execute_skill(self, action: CrewMemberAction) -> str:
        if not action.skill:
            return "No skill specified in action."
        skill = self.skill_service.get_skill(action.skill)
        if not skill:
            return f"Skill '{action.skill}' not found."

        # Use in-context execution for better integration
        # Pass the skill object directly, allowing knowledge-based execution if no scripts
        args = _normalize_skill_args_dict(action.args)

        result = await self.skill_service.execute_skill_in_context(
            skill=skill,
            workspace=self.workspace,
            project=self.project,
            args=args,
            script_name=action.script,
            llm_service=self.llm_service
        )

        # The result is now a string, so return it directly
        return str(result) if result is not None else f"Skill '{action.skill}' execution returned no output."

    async def _execute_skill_with_structured_content(
        self,
        action: CrewMemberAction,
        on_stream_event: Optional[Callable[[Any], None]] = None,
        message_id: Optional[str] = None
    ) -> str:
        """
        Execute a skill with structured content reporting for the UI.

        Args:
            action: The skill action to execute
            on_stream_event: Callback for stream events
            message_id: The message ID to associate with the skill execution

        Returns:
            The result of the skill execution
        """
        if not action.skill:
            return "No skill specified in action."

        skill = self.skill_service.get_skill(action.skill)
        if not skill:
            return f"Skill '{action.skill}' not found."

        args = _normalize_skill_args_dict(action.args)
        execution_mode = "script" if skill.scripts else "knowledge"
        meta = {"session_id": getattr(self, "_session_id", "unknown")}
        if message_id:
            meta["message_id"] = message_id

        skill_start = StructureContent(
            content_type=ContentType.SKILL,
            data={
                "status": "starting",
                "skill_name": action.skill,
                "message": f"Starting skill: {action.skill}",
            },
            title=f"Skill: {action.skill}",
            description="Skill execution starting",
        )
        kw = {
            "message_type": MessageType.SYSTEM,
            "sender_id": self.config.name,
            "sender_name": self.config.name,
            "metadata": dict(meta),
            "structured_content": [skill_start],
        }
        if message_id:
            kw["message_id"] = message_id
        await self.signals.send_agent_message(AgentMessage(**kw))

        progress_text = f"Executing skill '{action.skill}' via {execution_mode} with args: {list(args.keys())}..."
        skill_progress = StructureContent(
            content_type=ContentType.SKILL,
            data={
                "status": "in_progress",
                "skill_name": action.skill,
                "message": progress_text,
            },
            title=f"Skill: {action.skill}",
            description="Skill execution in progress",
        )
        kw["structured_content"] = [skill_progress]
        await self.signals.send_agent_message(AgentMessage(**kw))

        result = await self.skill_service.execute_skill_in_context(
            skill=skill,
            workspace=self.workspace,
            project=self.project,
            args=args,
            script_name=action.script,
            llm_service=self.llm_service
        )
        result_message = str(result) if result is not None else f"Skill '{action.skill}' execution returned no output."
        success = result.get("success", True) if isinstance(result, dict) else True

        skill_end = StructureContent(
            content_type=ContentType.SKILL,
            data={
                "status": "completed",
                "skill_name": action.skill,
                "message": result_message,
                "result": result_message,
                "success": success,
            },
            title=f"Skill: {action.skill}",
            description="Skill execution completed",
        )
        kw["structured_content"] = [skill_end]
        await self.signals.send_agent_message(AgentMessage(**kw))

        return result_message



def _parse_frontmatter(content: str) -> (Dict[str, Any], str):
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            meta_str = content[3:end_idx].strip()
            try:
                metadata = yaml.safe_load(meta_str) or {}
            except Exception:
                metadata = {}
            prompt = content[end_idx + 3 :].strip()
            return metadata, prompt
    return {}, content.strip()


def _normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def _extract_json_payload(text: str) -> Optional[Dict[str, Any]]:
    json_block_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_block_match:
        candidate = json_block_match.group(1)
        return _safe_json_load(candidate)

    candidate = text.strip()
    if candidate.startswith("{") and candidate.endswith("}"):
        payload = _safe_json_load(candidate)
        if payload is not None:
            return payload

    candidate = _find_balanced_json(text)
    if candidate:
        return _safe_json_load(candidate)
    return None


def _safe_json_load(candidate: str) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(candidate)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _find_balanced_json(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for idx in range(start, len(text)):
        if text[idx] == "{":
            depth += 1
        elif text[idx] == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    return None


def _extract_response_content(response: Any) -> str:
    if isinstance(response, dict):
        choices = response.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message") if isinstance(choice, dict) else None
            if message and isinstance(message, dict):
                return message.get("content", "")
            return choice.get("text", "")
        return ""
    choices = getattr(response, "choices", None)
    if choices:
        choice = choices[0]
        message = getattr(choice, "message", None)
        if message and hasattr(message, "content"):
            return message.content
        content = getattr(choice, "text", None)
        return content or ""
    return str(response)


def _format_skill_entry(skill: Skill) -> str:
    """Legacy simple skill formatting."""
    description = skill.description or ""
    knowledge = skill.knowledge or ""
    return f"- {skill.name}: {description}\n  {knowledge}"


def _format_skill_entry_detailed(skill: Skill) -> str:
    """Format a skill entry with metadata to help the LLM decide whether to use the skill."""
    lines = [
        f"### {skill.name}",
        f"**Description**: {skill.description}",
        "",
    ]

    # Add usage criteria to help LLM decide when to use this skill
    lines.append("**When to use this skill**: This skill should be used when:")
    if skill.knowledge:
        # Extract key capabilities from the knowledge section
        knowledge_lines = skill.knowledge.split('\n')
        # Look for lines that start with bullet points or keywords indicating use cases
        use_case_found = False
        for line in knowledge_lines[:10]:  # Check first 10 lines for use cases
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['when', 'use', 'should', 'can', 'capability', 'feature']):
                if any(char in line for char in ['-', '*', '•']):
                    lines.append(f"  - {line.strip(' -•*')}")
                    use_case_found = True
        if not use_case_found:
            lines.append(f"  - {skill.description}")
    else:
        lines.append(f"  - {skill.description}")
    lines.append("")

    # Add parameters
    if skill.parameters:
        lines.append("**Parameters**:")
        for param in skill.parameters:
            req_str = "required" if param.required else "optional"
            default_str = f", default: {param.default}" if param.default is not None else ""
            lines.append(f"  - `{param.name}` ({param.param_type}, {req_str}{default_str}): {param.description}")
        lines.append("")

    # Add example call
    lines.append("**Example call**:")
    lines.append("```json")
    lines.append(skill.get_example_call())
    lines.append("```")

    # Add knowledge snippet if available
    if skill.knowledge:
        # Extract just the capability section
        knowledge_preview = skill.knowledge[:300]
        if len(skill.knowledge) > 300:
            knowledge_preview += "..."
        lines.append("")
        lines.append(f"**Additional Details**: {knowledge_preview}")

    return "\n".join(lines)


def _normalize_skill_args(args: Any) -> List[str]:
    """Normalize args to list of strings for CLI execution (legacy)."""
    if args is None:
        return []
    if isinstance(args, list):
        return [str(item) for item in args]
    if isinstance(args, dict):
        return _dict_to_cli_args(args)
    if isinstance(args, str):
        return [args]
    return [str(args)]


def _normalize_skill_args_dict(args: Any) -> Dict[str, Any]:
    """Normalize args to dictionary for in-context execution."""
    if args is None:
        return {}
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        # Try to parse as JSON
        try:
            parsed = json.loads(args)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"input": args}
    if isinstance(args, list):
        return {"inputs": args}
    return {"value": args}


def _dict_to_cli_args(values: Dict[str, Any]) -> List[str]:
    """Convert dictionary to CLI arguments (legacy)."""
    cli_args = []
    for key, value in values.items():
        flag = f"--{str(key).replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                cli_args.append(flag)
            continue
        cli_args.extend([flag, str(value)])
    return cli_args


def _coerce_tasks(value: Any) -> Optional[List[PlanTask]]:
    if value is None:
        return None
    if isinstance(value, list):
        tasks = []
        for item in value:
            if isinstance(item, PlanTask):
                tasks.append(item)
            elif isinstance(item, dict):
                tasks.append(_task_from_dict(item))
        return tasks
    return None


def _task_from_dict(data: Dict[str, Any]) -> PlanTask:
    task_id = data.get("id") or data.get("task_id") or os.urandom(4).hex()
    status = data.get("status")
    if isinstance(status, TaskStatus):
        status = status
    elif status:
        try:
            status = TaskStatus(str(status))
        except ValueError:
            status = TaskStatus.CREATED
    else:
        status = TaskStatus.CREATED
    return PlanTask(
        id=task_id,
        name=data.get("name", "Task"),
        description=data.get("description", ""),
        title=data.get("title", "crew"),
        parameters=data.get("parameters", {}),
        needs=data.get("needs", []),
        status=status,
    )


def _resolve_project_name(project: Optional[Any]) -> Optional[str]:
    if project is None:
        return None
    if hasattr(project, "project_name"):
        return project.project_name
    if hasattr(project, "name"):
        return project.name
    if isinstance(project, str):
        return project
    return None
