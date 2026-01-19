import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import yaml

from agent.llm.llm_service import LlmService
from agent.plan.models import PlanTask, TaskStatus
from agent.plan.service import PlanService
from agent.skill.skill_service import SkillService, Skill, SkillParameter
from agent.skill.skill_executor import SkillContext, SkillExecutor, get_skill_executor
from agent.soul import soul_service as soul_service_instance, SoulService


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
        self.project_id = _resolve_project_id(project) or getattr(project, 'project_name', 'default_project')
        self.llm_service = llm_service or LlmService(workspace)
        self.skill_service = skill_service or SkillService(workspace)
        self.plan_service = plan_service or PlanService()
        self.soul_service = soul_service or self._build_soul_service(project)
        self.conversation_history: List[Dict[str, str]] = []

    async def chat_stream(
        self,
        message: str,
        on_token: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_stream_event: Optional[Callable[[Any], None]] = None,
        plan_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        if not self.llm_service.validate_config():
            error_message = "LLM service is not configured."
            if on_token:
                on_token(error_message)
            if on_stream_event:
                # Send error event to UI
                from agent.filmeto_agent import StreamEvent
                on_stream_event(StreamEvent("error", {
                    "content": error_message,
                    "sender_name": self.config.name,
                    "session_id": getattr(self, '_session_id', 'unknown')
                }))
            yield error_message
            if on_complete:
                on_complete(error_message)
            return

        system_prompt = self._build_system_prompt(plan_id=plan_id)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})

        # Notify UI that the agent is starting to think/process
        if on_stream_event:
            from agent.filmeto_agent import StreamEvent
            on_stream_event(StreamEvent("agent_thinking", {
                "sender_name": self.config.name,
                "sender_id": self.config.name,
                "message": f"{self.config.name} is processing the request...",
                "session_id": getattr(self, '_session_id', 'unknown')
            }))

        final_response = None
        for step in range(self.config.max_steps):
            # Notify UI that the agent is calling the LLM
            if on_stream_event:
                from agent.filmeto_agent import StreamEvent
                on_stream_event(StreamEvent("llm_call_start", {
                    "sender_name": self.config.name,
                    "sender_id": self.config.name,
                    "step": step + 1,
                    "total_steps": self.config.max_steps,
                    "session_id": getattr(self, '_session_id', 'unknown')
                }))

            response_text = await self._complete(messages)

            # Notify UI that the LLM responded
            if on_stream_event:
                from agent.filmeto_agent import StreamEvent
                on_stream_event(StreamEvent("llm_call_end", {
                    "sender_name": self.config.name,
                    "sender_id": self.config.name,
                    "step": step + 1,
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                    "session_id": getattr(self, '_session_id', 'unknown')
                }))

            action = self._parse_action(response_text)

            if action.action_type == "skill":
                # Execute skill with structured content reporting
                observation = self._execute_skill_with_structured_content(
                    action,
                    on_stream_event=on_stream_event,
                    message_id=getattr(self, '_current_message_id', 'unknown')
                )
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": f"Observation: {observation}"})

                # Notify UI about skill execution
                if on_stream_event:
                    from agent.filmeto_agent import StreamEvent
                    on_stream_event(StreamEvent("skill_execution", {
                        "sender_name": self.config.name,
                        "sender_id": self.config.name,
                        "skill": action.skill,
                        "observation": observation,
                        "session_id": getattr(self, '_session_id', 'unknown')
                    }))
                continue

            if action.action_type == "plan_update":
                observation = self._apply_plan_update(action, plan_id=plan_id)
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": f"Observation: {observation}"})

                # Notify UI about plan update
                if on_stream_event:
                    from agent.filmeto_agent import StreamEvent
                    on_stream_event(StreamEvent("plan_update", {
                        "sender_name": self.config.name,
                        "sender_id": self.config.name,
                        "plan_id": plan_id,
                        "observation": observation,
                        "session_id": getattr(self, '_session_id', 'unknown')
                    }))
                continue

            final_response = action.response or response_text
            break

        if final_response is None:
            final_response = "Reached max steps without a final response."

        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": final_response})

        if on_token:
            on_token(final_response)
        yield final_response
        if on_complete:
            on_complete(final_response)

    def _build_soul_service(self, project: Optional[Any]) -> 'SoulService':
        # Return the singleton instance
        # The singleton is configured elsewhere with the workspace
        return soul_service_instance

    def _build_system_prompt(self, plan_id: Optional[str] = None) -> str:
        prompt_sections = [
            "You are a ReAct-style crew member.",
            f"Crew member name: {self.config.name}.",
        ]
        if self.config.description:
            prompt_sections.append(f"Role description: {self.config.description}")
        if self.config.prompt:
            prompt_sections.append(self.config.prompt.strip())

        soul_prompt = self._get_soul_prompt()
        if soul_prompt:
            prompt_sections.append("Soul profile:")
            prompt_sections.append(soul_prompt)

        skills_prompt = self._format_skills_prompt()
        prompt_sections.append(skills_prompt)

        if plan_id:
            prompt_sections.append(f"Active plan id: {plan_id}.")
        elif self.project_id:
            prompt_sections.append(f"Project id: {self.project_id}.")

        prompt_sections.append(_ACTION_INSTRUCTIONS)
        return "\n\n".join(section for section in prompt_sections if section)

    def _get_soul_prompt(self) -> str:
        if not self.config.soul:
            return ""
        soul = self.soul_service.get_soul_by_name(self.project_id, self.config.soul)
        if not soul:
            return f"Soul '{self.config.soul}' not found."
        if soul.knowledge:
            return soul.knowledge
        return f"Soul '{self.config.soul}' has no prompt content."

    def _format_skills_prompt(self) -> str:
        if not self.config.skills:
            return "Available skills: none.\nYou cannot call any skills."

        details = []
        missing = []
        for name in self.config.skills:
            skill = self.skill_service.get_skill(name)
            if not skill:
                missing.append(name)
                continue
            details.append(_format_skill_entry_detailed(skill))

        if not details:
            skills_section = "Available skills: none.\nYou cannot call any skills."
        else:
            skills_section = (
                "## Available Skills\n\n"
                "You have access to the following skills. Use them by responding with a JSON object.\n\n"
                + "\n\n".join(details)
            )
        
        if missing:
            skills_section += f"\n\nNote: The following skills are configured but not available: {', '.join(missing)}"
        
        return skills_section

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
        if action_type not in {"final", "skill", "plan_update"}:
            action_type = "final"

        return CrewMemberAction(
            action_type=action_type,
            response=payload.get("response") or payload.get("final"),
            skill=payload.get("skill") or payload.get("tool"),
            script=payload.get("script"),
            args=payload.get("args") or payload.get("arguments") or payload.get("input"),
            plan_id=payload.get("plan_id"),
            plan_update=payload.get("plan_update") or payload.get("plan") or payload.get("changes"),
            raw=response_text,
        )

    def _execute_skill(self, action: CrewMemberAction) -> str:
        if not action.skill:
            return "No skill specified in action."
        skill = self.skill_service.get_skill(action.skill)
        if not skill:
            return f"Skill '{action.skill}' not found."
        if not skill.scripts:
            return skill.knowledge or f"Skill '{action.skill}' has no executable scripts."

        # Use in-context execution for better integration
        args = _normalize_skill_args_dict(action.args)
        
        result = self.skill_service.execute_skill_in_context(
            skill_name=action.skill,
            workspace=self.workspace,
            project=self.project,
            args=args,
            script_name=action.script
        )
        
        if isinstance(result, dict):
            if result.get("success"):
                message = result.get("message", "Skill executed successfully.")
                # Include additional details if available
                if "created_scenes" in result:
                    message += f"\nCreated scenes: {result['created_scenes']}"
                if "outline_summary" in result:
                    summary = "\n".join([f"  - {s['scene_id']}: {s['logline']}" for s in result['outline_summary'][:5]])
                    message += f"\nOutline:\n{summary}"
                return message
            else:
                return f"Skill execution failed: {result.get('message', result.get('error', 'Unknown error'))}"
        
        return str(result) if result is not None else f"Skill '{action.skill}' execution returned no output."

    def _execute_skill_with_structured_content(
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
        if not skill.scripts:
            return skill.knowledge or f"Skill '{action.skill}' has no executable scripts."

        # Send start state event
        if on_stream_event:
            from agent.filmeto_agent import StreamEvent
            on_stream_event(StreamEvent("skill_start", {
                "skill_name": action.skill,
                "skill_args": action.args,
                "message_id": message_id,
                "sender_name": self.config.name,
                "session_id": getattr(self, '_session_id', 'unknown')
            }))

        # Use in-context execution for better integration
        args = _normalize_skill_args_dict(action.args)

        # Send progress state event
        if on_stream_event:
            from agent.filmeto_agent import StreamEvent
            on_stream_event(StreamEvent("skill_progress", {
                "skill_name": action.skill,
                "progress_text": f"Executing skill '{action.skill}' with args: {list(args.keys())}...",
                "message_id": message_id,
                "sender_name": self.config.name,
                "session_id": getattr(self, '_session_id', 'unknown')
            }))

        result = self.skill_service.execute_skill_in_context(
            skill_name=action.skill,
            workspace=self.workspace,
            project=self.project,
            args=args,
            script_name=action.script
        )

        # Format the result message
        if isinstance(result, dict):
            if result.get("success"):
                result_message = result.get("message", "Skill executed successfully.")
                # Include additional details if available
                if "created_scenes" in result:
                    result_message += f"\nCreated scenes: {result['created_scenes']}"
                if "outline_summary" in result:
                    summary = "\n".join([f"  - {s['scene_id']}: {s['logline']}" for s in result['outline_summary'][:5]])
                    result_message += f"\nOutline:\n{summary}"
            else:
                result_message = f"Skill execution failed: {result.get('message', result.get('error', 'Unknown error'))}"
        else:
            result_message = str(result) if result is not None else f"Skill '{action.skill}' execution returned no output."

        # Send end state event
        if on_stream_event:
            from agent.filmeto_agent import StreamEvent
            on_stream_event(StreamEvent("skill_end", {
                "skill_name": action.skill,
                "result": result_message,
                "success": result.get("success", True) if isinstance(result, dict) else True,
                "message_id": message_id,
                "sender_name": self.config.name,
                "session_id": getattr(self, '_session_id', 'unknown')
            }))

        return result_message

    def _apply_plan_update(self, action: CrewMemberAction, plan_id: Optional[str]) -> str:
        if not self.project_id:
            return "Project id is missing for plan update."

        target_plan_id = action.plan_id or plan_id
        if not target_plan_id:
            return "Plan id is missing for plan update."

        changes = action.plan_update or {}
        if not isinstance(changes, dict):
            return "Plan update payload must be an object."

        plan_name = changes.get("name")
        description = changes.get("description")
        metadata = changes.get("metadata")
        tasks = changes.get("tasks")
        append_tasks = changes.get("append_tasks")

        updated_plan = self.plan_service.update_plan(
            project_id=self.project_id,
            plan_id=target_plan_id,
            name=plan_name,
            description=description,
            tasks=_coerce_tasks(tasks),
            append_tasks=_coerce_tasks(append_tasks),
            metadata=metadata,
        )
        if updated_plan is None:
            return f"Plan '{target_plan_id}' not found for update."
        return f"Plan '{target_plan_id}' updated."


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
    """Format a skill entry with detailed parameters and examples for the prompt."""
    lines = [
        f"### {skill.name}",
        f"**Description**: {skill.description}",
        "",
    ]
    
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
        lines.append(f"**Details**: {knowledge_preview}")
    
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
        agent_role=data.get("agent_role", "crew"),
        parameters=data.get("parameters", {}),
        needs=data.get("needs", []),
        status=status,
    )


def _resolve_project_id(project: Optional[Any]) -> Optional[str]:
    if project is None:
        return None
    if hasattr(project, "project_id"):
        return project.project_id
    if hasattr(project, "project_name"):
        return project.project_name
    if hasattr(project, "name"):
        return project.name
    if isinstance(project, str):
        return project
    return None


_ACTION_INSTRUCTIONS = """
## Response Format

You MUST respond ONLY with a JSON object. Choose one of these action types:

### 1. Call a Skill
When you need to perform an action using one of your available skills:
```json
{
  "type": "skill",
  "skill": "skill_name",
  "args": {
    "param1": "value1",
    "param2": "value2"
  }
}
```
IMPORTANT: Use the exact parameter names as specified in each skill's parameters section.

### 2. Update a Plan
When you need to update the execution plan:
```json
{
  "type": "plan_update",
  "plan_id": "plan_id",
  "plan_update": {
    "name": "Plan Name",
    "description": "Plan description",
    "tasks": [...]
  }
}
```

### 3. Final Response
When your task is complete and you're ready to report results:
```json
{
  "type": "final",
  "response": "Your complete response message here"
}
```

## Important Rules
- If you have skills available, USE THEM when appropriate. Do not just describe what you would do.
- After calling a skill, you will receive an Observation with the result.
- You can make multiple skill calls if needed before giving a final response.
- If you receive a message that includes @your_name, treat it as your assigned task.
- Do NOT include any text outside the JSON object.
"""