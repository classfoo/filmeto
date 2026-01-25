import asyncio
import inspect
import json
import re
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from agent.llm.llm_service import LlmService

from .types import ReactEvent, ReactEventType, ReactStatus, CheckpointData
from .storage import ReactStorage


class React:
    """
    A generic ReAct processor that handles the ReAct (Reasoning and Acting) loop.
    """

    def __init__(
        self,
        *,
        workspace,
        project_name: str,
        react_type: str,
        build_prompt_function: Callable[[], str],
        tool_call_function: Callable[[str, Dict[str, Any]], Any],
        llm_service: Optional[LlmService] = None,
        max_steps: int = 20,
    ):
        self.workspace = workspace
        self.project_name = project_name
        self.react_type = react_type
        self.build_prompt_function = build_prompt_function
        self.tool_call_function = tool_call_function
        self.llm_service = llm_service or LlmService(workspace)
        self.max_steps = max_steps

        if workspace and hasattr(workspace, "workspace_dir"):
            self.workspace_root = workspace.workspace_dir
        else:
            self.workspace_root = "workspace"

        self.storage = ReactStorage(
            project_name=project_name,
            react_type=react_type,
            workspace_root=self.workspace_root,
        )

        self.run_id: str = ""
        self.step_id: int = 0
        self.status: str = ReactStatus.IDLE
        self.messages: List[Dict[str, str]] = []
        self.pending_user_messages: List[str] = []
        self._in_react_loop: bool = False

        checkpoint = self.storage.load_checkpoint()
        if checkpoint and checkpoint.status == ReactStatus.RUNNING:
            self.run_id = checkpoint.run_id
            self.step_id = checkpoint.step_id
            self.status = checkpoint.status
            self.messages = checkpoint.messages
            self.pending_user_messages = list(checkpoint.pending_user_messages)

    def _create_event(self, event_type: str, payload: Dict[str, Any]) -> ReactEvent:
        return ReactEvent(
            event_type=event_type,
            project_name=self.project_name,
            react_type=self.react_type,
            run_id=self.run_id,
            step_id=self.step_id,
            payload=payload,
        )

    def _update_checkpoint(self) -> None:
        checkpoint_data = CheckpointData(
            run_id=self.run_id,
            step_id=self.step_id,
            status=self.status,
            messages=self.messages,
            pending_user_messages=self.pending_user_messages,
            last_tool_calls=[],
            last_tool_results=[],
        )
        self.storage.save_checkpoint(checkpoint_data)

    def _drain_pending_messages(self) -> List[str]:
        messages = self.pending_user_messages[:]
        self.pending_user_messages.clear()
        return messages

    def _start_new_run(self) -> None:
        self.run_id = f"run_{int(time.time() * 1000000)}_{self.project_name}_{self.react_type}"
        self.step_id = 0
        self.status = ReactStatus.RUNNING
        system_prompt = self.build_prompt_function()
        self.messages = [{"role": "system", "content": system_prompt}]

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        if not self.llm_service.validate_config():
            return '{"type": "final", "final": "LLM service is not configured."}'

        loop = asyncio.get_event_loop()
        model_to_use = self.llm_service.default_model or "qwen-plus"
        temperature_to_use = getattr(self.llm_service, "temperature", 0.7)
        response = await loop.run_in_executor(
            None,
            lambda: self.llm_service.completion(
                model=model_to_use,
                messages=messages,
                temperature=temperature_to_use,
                stream=False,
            ),
        )
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                choice = choices[0]
                message = choice.get("message") if isinstance(choice, dict) else None
                if message and isinstance(message, dict):
                    return message.get("content", "")
                return choice.get("text", "")
        return ""

    def _parse_action(self, response_text: str) -> Dict[str, Any]:
        payload = self._extract_json_payload(response_text)
        if payload:
            action_type = payload.get("type") or payload.get("action")
            if action_type == "tool":
                return {
                    "type": "tool",
                    "tool_name": payload.get("tool_name") or payload.get("name"),
                    "tool_args": payload.get("tool_args") or payload.get("arguments") or payload.get("input") or {},
                    "thinking": payload.get("thinking") or payload.get("thought") or payload.get("reasoning"),
                }
            if action_type == "final":
                return {
                    "type": "final",
                    "final": payload.get("final") or payload.get("response") or response_text,
                    "thinking": payload.get("thinking") or payload.get("thought") or payload.get("reasoning"),
                }
        return {
            "type": "final",
            "final": response_text,
            "thinking": None,
        }

    def _extract_json_payload(self, text: str) -> Optional[Dict[str, Any]]:
        json_block_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_block_match:
            candidate = json_block_match.group(1)
            return self._safe_json_load(candidate)

        candidate = text.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            payload = self._safe_json_load(candidate)
            if payload is not None:
                return payload

        candidate = self._find_balanced_json(text)
        if candidate:
            return self._safe_json_load(candidate)
        return None

    def _safe_json_load(self, candidate: str) -> Optional[Dict[str, Any]]:
        try:
            payload = json.loads(candidate)
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    def _find_balanced_json(self, text: str) -> Optional[str]:
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

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        result = self.tool_call_function(tool_name, tool_args)
        if inspect.isawaitable(result):
            result = await result

        if inspect.isasyncgen(result) or hasattr(result, "__aiter__"):
            last_item = None
            async for item in result:
                last_item = item
                yield {"progress": item}
            yield {"result": last_item}
            return

        yield {"result": result}

    async def chat_stream(self, user_message: Optional[str]) -> AsyncGenerator[ReactEvent, None]:
        if self._in_react_loop:
            if user_message:
                self.pending_user_messages.append(user_message)
                self._update_checkpoint()
            return

        if not self.run_id or self.status in {ReactStatus.IDLE, ReactStatus.FINAL, ReactStatus.FAILED}:
            self._start_new_run()

        if user_message:
            self.pending_user_messages.append(user_message)

        pending_messages = self._drain_pending_messages()
        for msg in pending_messages:
            self.messages.append({"role": "user", "content": msg})

        self._in_react_loop = True
        self._update_checkpoint()

        try:
            for step in range(self.step_id, self.max_steps):
                self.step_id = step
                self._update_checkpoint()

                new_pending = self._drain_pending_messages()
                for msg in new_pending:
                    self.messages.append({"role": "user", "content": msg})

                response_text = await self._call_llm(self.messages)
                action = self._parse_action(response_text)
                thinking = action.get("thinking") or f"Processing step {step + 1}/{self.max_steps}"
                yield self._create_event(ReactEventType.LLM_THINKING, {
                    "message": thinking,
                    "step": step + 1,
                    "total_steps": self.max_steps,
                })

                yield self._create_event(ReactEventType.LLM_OUTPUT, {
                    "content": response_text,
                })

                if action["type"] == "tool":
                    yield self._create_event(ReactEventType.TOOL_START, {
                        "tool_name": action["tool_name"],
                        "tool_args": action["tool_args"],
                    })
                    try:
                        tool_result = None
                        async for item in self._execute_tool(action["tool_name"], action["tool_args"]):
                            if "progress" in item:
                                yield self._create_event(ReactEventType.TOOL_PROGRESS, {
                                    "tool_name": action["tool_name"],
                                    "progress": item["progress"],
                                })
                            if "result" in item:
                                tool_result = item["result"]
                        yield self._create_event(ReactEventType.TOOL_END, {
                            "tool_name": action["tool_name"],
                            "ok": True,
                            "result": tool_result,
                        })
                        self.messages.append({"role": "assistant", "content": response_text})
                        self.messages.append({"role": "user", "content": f"Observation: {tool_result}"})
                    except Exception as exc:
                        yield self._create_event(ReactEventType.TOOL_END, {
                            "tool_name": action["tool_name"],
                            "ok": False,
                            "error": str(exc),
                        })
                        self.messages.append({"role": "assistant", "content": response_text})
                        self.messages.append({"role": "user", "content": f"Error: {str(exc)}"})
                    continue

                if action["type"] == "final":
                    self.status = ReactStatus.FINAL
                    self._update_checkpoint()
                    yield self._create_event(ReactEventType.FINAL, {
                        "final_response": action["final"],
                        "stop_reason": "final_action",
                        "summary": "ReAct process completed successfully",
                    })
                    break

            if self.status != ReactStatus.FINAL:
                self.status = ReactStatus.FINAL
                self._update_checkpoint()
                yield self._create_event(ReactEventType.FINAL, {
                    "final_response": "Reached maximum steps without completion",
                    "stop_reason": "max_steps_reached",
                    "summary": f"ReAct process stopped after {self.max_steps} steps",
                })
        except Exception as exc:
            self.status = ReactStatus.FAILED
            self._update_checkpoint()
            yield self._create_event(ReactEventType.ERROR, {
                "error": str(exc),
                "details": repr(exc),
            })
        finally:
            self._in_react_loop = False
            self._update_checkpoint()

        while self.pending_user_messages:
            next_message = self.pending_user_messages.pop(0)
            async for event in self.chat_stream(next_message):
                yield event

    async def resume(self) -> AsyncGenerator[ReactEvent, None]:
        checkpoint = self.storage.load_checkpoint()
        if not checkpoint:
            yield self._create_event(ReactEventType.ERROR, {
                "error": "No checkpoint found to resume from",
                "details": "Cannot resume ReAct process without a saved checkpoint",
            })
            return

        self.run_id = checkpoint.run_id
        self.step_id = checkpoint.step_id
        self.status = checkpoint.status
        self.messages = checkpoint.messages
        self.pending_user_messages = list(checkpoint.pending_user_messages)

        async for event in self.chat_stream(None):
            yield event
