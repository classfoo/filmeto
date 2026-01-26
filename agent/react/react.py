import asyncio
import inspect
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from agent.llm.llm_service import LlmService

from .types import (
    ReactEvent,
    ReactEventType,
    ReactStatus,
    CheckpointData,
    ReactAction,
    ToolAction,
    FinalAction,
    ErrorAction,
    ReactActionParser,
    ActionType,
    YamlFormatSpec,
    YamlStreamParser,
)
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

        if workspace and hasattr(workspace, "get_path"):
            self.workspace_root = workspace.get_path()
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
        """Non-streaming LLM call (kept for backward compatibility)."""
        if not self.llm_service.validate_config():
            return '{"type": "final", "final": "LLM service is not configured."}'

        model_to_use = self.llm_service.default_model or "qwen-plus"
        temperature_to_use = getattr(self.llm_service, "temperature", 0.7)
        response = await self.llm_service.acompletion(
            model=model_to_use,
            messages=messages,
            temperature=temperature_to_use,
            stream=False,
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

    async def _call_llm_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Streaming LLM call that yields text chunks.

        Yields:
            str: Text chunks from the LLM stream
        """
        if not self.llm_service.validate_config():
            yield '{"type": "final", "final": "LLM service is not configured."}'
            return

        model_to_use = self.llm_service.default_model or "qwen-plus"
        temperature_to_use = getattr(self.llm_service, "temperature", 0.7)

        try:
            response_stream = await self.llm_service.acompletion(
                model=model_to_use,
                messages=messages,
                temperature=temperature_to_use,
                stream=True,
            )

            # Handle different streaming response formats
            if hasattr(response_stream, '__aiter__'):
                async for chunk in response_stream:
                    content = self._extract_content_from_chunk(chunk)
                    if content:
                        yield content
            elif isinstance(response_stream, dict):
                # Fallback for non-streaming response
                content = self._extract_content_from_chunk(response_stream)
                if content:
                    yield content
        except Exception as e:
            # On error, yield an error response
            yield f'{{"type": "final", "final": "LLM call failed: {str(e)}"}}'

    def _extract_content_from_chunk(self, chunk: Any) -> str:
        """
        Extract content from a streaming chunk.

        Args:
            chunk: A chunk from the LLM stream

        Returns:
            str: Extracted content text
        """
        if not chunk:
            return ""

        # Handle OpenAI-style chunks
        if isinstance(chunk, dict):
            choices = chunk.get("choices", [])
            if choices:
                choice = choices[0]
                if isinstance(choice, dict):
                    delta = choice.get("delta", {})
                    if isinstance(delta, dict):
                        return delta.get("content", "")
                # Handle direct content in choice
                if hasattr(choice, "content"):
                    return choice.content
            # Direct content in chunk
            if "content" in chunk:
                return chunk.get("content", "")

        # Handle object-style chunks (like pydantic models)
        if hasattr(chunk, "choices") and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, "delta") and choice.delta:
                if hasattr(choice.delta, "content"):
                    return choice.delta.content or ""
            if hasattr(choice, "content"):
                return choice.content or ""

        # Handle direct content attribute
        if hasattr(chunk, "content"):
            return chunk.content or ""

        return ""

    def _parse_action(self, response_text: str) -> ReactAction:
        """
        Parse LLM response into a ReactAction.

        Uses ReactActionParser for YAML parsing.
        """
        return ReactActionParser.parse(response_text)

    def _create_action_from_stream_data(
        self,
        action_data: Dict[str, Any],
        collected_thinking: str,
        raw_response: str
    ) -> Optional[ReactAction]:
        """Create a ReactAction from parsed YAML stream data."""
        try:
            action_type = action_data.get("type", "")

            if action_type == ActionType.TOOL:
                return ToolAction(
                    tool_name=action_data.get("tool_name", ""),
                    tool_args=action_data.get("tool_args", {}),
                    thinking=collected_thinking or action_data.get("thinking")
                )
            elif action_type == ActionType.FINAL:
                return FinalAction(
                    final=action_data.get("final", ""),
                    thinking=collected_thinking or action_data.get("thinking"),
                    stop_reason=action_data.get("stop_reason", "final_action")
                )
            elif action_type == ActionType.ERROR:
                return ErrorAction(
                    error=action_data.get("error", ""),
                    thinking=collected_thinking or action_data.get("thinking"),
                    raw_response=raw_response
                )
        except Exception:
            pass
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

                # Stream LLM response with YAML format
                yaml_parser = YamlStreamParser()
                full_response = ""
                collected_thinking = ""
                action_from_stream = None

                # Emit stream start event
                yield self._create_event(ReactEventType.LLM_STREAM_START, {
                    "step": step + 1,
                    "total_steps": self.max_steps,
                })

                # Process streaming chunks
                async for chunk in self._call_llm_stream(self.messages):
                    full_response += chunk
                    parse_result = yaml_parser.feed(chunk)

                    # Emit thinking stream events
                    if parse_result.has_thinking():
                        if parse_result.thinking_complete:
                            collected_thinking = yaml_parser.get_thinking()
                        yield self._create_event(ReactEventType.LLM_THINKING_STREAM, {
                            "content": parse_result.thinking_delta,
                            "complete": parse_result.thinking_complete,
                        })

                    # Emit content stream events (action data)
                    if parse_result.has_content():
                        yield self._create_event(ReactEventType.LLM_CONTENT_STREAM, {
                            "content": parse_result.content_delta,
                        })

                    # Check if action is complete from stream
                    if parse_result.action_complete and parse_result.action_data:
                        action_from_stream = cls._create_action_from_stream_data(
                            parse_result.action_data,
                            collected_thinking,
                            full_response
                        )

                # Finalize parser
                final_result = yaml_parser.finalize()
                if final_result.has_content():
                    yield self._create_event(ReactEventType.LLM_CONTENT_STREAM, {
                        "content": final_result.content_delta,
                    })

                if not action_from_stream and final_result.action_complete and final_result.action_data:
                    action_from_stream = cls._create_action_from_stream_data(
                        final_result.action_data,
                        collected_thinking,
                        full_response
                    )

                # Emit stream end event
                yield self._create_event(ReactEventType.LLM_STREAM_END, {
                    "complete": True,
                })

                # Parse action from the full response (or use action from stream)
                action = action_from_stream or self._parse_action(full_response)

                # If thinking was extracted from stream, use it; otherwise use action's thinking
                if collected_thinking:
                    thinking = collected_thinking
                else:
                    thinking = ReactActionParser.get_thinking_message(action, step + 1, self.max_steps)

                # Emit thinking event with collected thinking
                yield self._create_event(ReactEventType.LLM_THINKING, {
                    "message": thinking,
                    "step": step + 1,
                    "total_steps": self.max_steps,
                })

                # Emit full output event for backward compatibility
                yield self._create_event(ReactEventType.LLM_OUTPUT, {
                    "content": full_response,
                })

                if action.is_tool():
                    assert isinstance(action, ToolAction), f"Expected ToolAction, got {type(action)}"
                    yield self._create_event(ReactEventType.TOOL_START, action.to_start_payload())
                    try:
                        tool_result = None
                        async for item in self._execute_tool(action.tool_name, action.tool_args):
                            if "progress" in item:
                                yield self._create_event(ReactEventType.TOOL_PROGRESS, action.to_progress_payload(item["progress"]))
                            if "result" in item:
                                tool_result = item["result"]
                        yield self._create_event(ReactEventType.TOOL_END, action.to_end_payload(result=tool_result, ok=True))
                        self.messages.append({"role": "assistant", "content": full_response})
                        self.messages.append({"role": "user", "content": f"Observation: {tool_result}"})
                    except Exception as exc:
                        yield self._create_event(ReactEventType.TOOL_END, action.to_end_payload(ok=False, error=str(exc)))
                        self.messages.append({"role": "assistant", "content": full_response})
                        self.messages.append({"role": "user", "content": f"Error: {str(exc)}"})
                    continue

                if action.is_final():
                    assert isinstance(action, FinalAction), f"Expected FinalAction, got {type(action)}"
                    self.status = ReactStatus.FINAL
                    self._update_checkpoint()
                    yield self._create_event(ReactEventType.FINAL, action.to_final_payload())
                    break

            if self.status != ReactStatus.FINAL:
                max_steps_action = ReactActionParser.create_final_action(
                    final="Reached maximum steps without completion",
                    stop_reason=ReactActionParser.get_max_steps_stop_reason()
                )
                self.status = ReactStatus.FINAL
                self._update_checkpoint()
                yield self._create_event(ReactEventType.FINAL, max_steps_action.to_final_payload())
        except Exception as exc:
            self.status = ReactStatus.FAILED
            self._update_checkpoint()
            yield self._create_event(ReactEventType.ERROR, {
                "error": ReactActionParser.get_error_summary(exc),
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
