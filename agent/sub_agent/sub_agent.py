import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import yaml

from agent.llm.llm_service import LlmService
from agent.plan.models import PlanTask, TaskStatus
from agent.plan.service import PlanService
from agent.skill.skill_service import SkillService, Skill
from agent.soul.soul_service import SoulService


@dataclass
class SubAgentConfig:
    name: str
    description: str = ""
    soul: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    prompt: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.4
    max_steps: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)
    config_path: Optional[str] = None

    @classmethod
    def from_markdown(cls, file_path: str) -> "SubAgentConfig":
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

        return cls(
            name=name,
            description=description,
            soul=soul,
            skills=skills,
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_steps=max_steps,
            metadata=metadata,
            config_path=file_path,
        )


@dataclass
class SubAgentAction:
    action_type: str
    response: Optional[str] = None
    skill: Optional[str] = None
    script: Optional[str] = None
    args: Optional[Any] = None
    plan_id: Optional[str] = None
    plan_update: Optional[Dict[str, Any]] = None
    raw: Optional[str] = None


class SubAgent:
    """
    A ReAct-style sub-agent driven by LLM and skill execution.
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
        self.config = SubAgentConfig.from_markdown(config_path)
        self.workspace = workspace
        self.project = project
        self.project_id = _resolve_project_id(project)
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
        plan_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        if not self.llm_service.validate_config():
            error_message = "LLM service is not configured."
            if on_token:
                on_token(error_message)
            yield error_message
            if on_complete:
                on_complete(error_message)
            return

        system_prompt = self._build_system_prompt(plan_id=plan_id)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})

        final_response = None
        for _ in range(self.config.max_steps):
            response_text = await self._complete(messages)
            action = self._parse_action(response_text)

            if action.action_type == "skill":
                observation = self._execute_skill(action)
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                continue

            if action.action_type == "plan_update":
                observation = self._apply_plan_update(action, plan_id=plan_id)
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
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

    def _build_soul_service(self, project: Optional[Any]) -> SoulService:
        system_souls_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "soul", "system"
        )
        project_souls_dir = None
        if project and hasattr(project, "project_path"):
            project_souls_dir = os.path.join(project.project_path, "agent", "souls")
        if not project_souls_dir:
            project_souls_dir = os.path.join(os.path.dirname(__file__), "empty_souls")
        return SoulService(system_souls_dir=system_souls_dir, user_souls_dir=project_souls_dir)

    def _build_system_prompt(self, plan_id: Optional[str] = None) -> str:
        prompt_sections = [
            "You are a ReAct-style sub-agent.",
            f"Sub-agent name: {self.config.name}.",
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
        soul = self.soul_service.get_soul_by_name(self.config.soul)
        if not soul:
            return f"Soul '{self.config.soul}' not found."
        if soul.knowledge:
            return soul.knowledge
        return f"Soul '{self.config.soul}' has no prompt content."

    def _format_skills_prompt(self) -> str:
        if not self.config.skills:
            return "Available skills: none."

        details = []
        missing = []
        for name in self.config.skills:
            skill = self.skill_service.get_skill(name)
            if not skill:
                missing.append(name)
                continue
            details.append(_format_skill_entry(skill))

        skills_section = "Available skills:\n" + "\n".join(details) if details else "Available skills: none."
        if missing:
            skills_section += "\nMissing skill definitions: " + ", ".join(missing)
        return skills_section

    async def _complete(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = await self.llm_service.acompletion(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                stream=False,
            )
            return _extract_response_content(response)
        except Exception as exc:
            return f"Error calling LLM: {exc}"

    def _parse_action(self, response_text: str) -> SubAgentAction:
        payload = _extract_json_payload(response_text)
        if not payload:
            return SubAgentAction(action_type="final", response=response_text, raw=response_text)

        action_type = payload.get("type") or payload.get("action") or "final"
        action_type = str(action_type).strip().lower()
        if action_type not in {"final", "skill", "plan_update"}:
            action_type = "final"

        return SubAgentAction(
            action_type=action_type,
            response=payload.get("response") or payload.get("final"),
            skill=payload.get("skill") or payload.get("tool"),
            script=payload.get("script"),
            args=payload.get("args") or payload.get("arguments") or payload.get("input"),
            plan_id=payload.get("plan_id"),
            plan_update=payload.get("plan_update") or payload.get("plan") or payload.get("changes"),
            raw=response_text,
        )

    def _execute_skill(self, action: SubAgentAction) -> str:
        if not action.skill:
            return "No skill specified in action."
        skill = self.skill_service.get_skill(action.skill)
        if not skill:
            return f"Skill '{action.skill}' not found."
        if not skill.scripts:
            return skill.knowledge or f"Skill '{action.skill}' has no executable scripts."

        script_name = action.script or os.path.basename(skill.scripts[0])
        args = _normalize_skill_args(action.args)
        result = self.skill_service.execute_skill_script(action.skill, script_name, *args)
        return result if result is not None else f"Skill '{action.skill}' execution returned no output."

    def _apply_plan_update(self, action: SubAgentAction, plan_id: Optional[str]) -> str:
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
    description = skill.description or ""
    knowledge = skill.knowledge or ""
    return f"- {skill.name}: {description}\n  {knowledge}"


def _normalize_skill_args(args: Any) -> List[str]:
    if args is None:
        return []
    if isinstance(args, list):
        return [str(item) for item in args]
    if isinstance(args, dict):
        return _dict_to_cli_args(args)
    if isinstance(args, str):
        return [args]
    return [str(args)]


def _dict_to_cli_args(values: Dict[str, Any]) -> List[str]:
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
        agent_role=data.get("agent_role", "sub_agent"),
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


_ACTION_INSTRUCTIONS = (
    "Respond ONLY with a JSON object. Use one of the following action types:\n"
    '- {"type":"skill","skill":"skill_name","args":{...}} to call a skill.\n'
    '- {"type":"plan_update","plan_id":"plan_id","plan_update":{...}} to update a plan.\n'
    '- {"type":"final","response":"your final response"} when done.\n'
    "Do not include additional commentary outside the JSON."
)
