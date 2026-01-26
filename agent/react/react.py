import asyncio
import inspect
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from agent.llm.llm_service import LlmService

logger = logging.getLogger(__name__)

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
        checkpoint_interval: int = 1,
    ):
        self.workspace = workspace
        self.project_name = project_name
        self.react_type = react_type
        self.build_prompt_function = build_prompt_function
        self.tool_call_function = tool_call_function
        self.llm_service = llm_service or LlmService(workspace)
        self.max_steps = max_steps
        self.checkpoint_interval = checkpoint_interval

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
        self._loop_lock = asyncio.Lock()
        self._steps_since_checkpoint: int = 0

        # Metrics
        self._total_llm_calls: int = 0
        self._total_tool_calls: int = 0
        self._llm_duration_ms: float = 0.0
        self._tool_duration_ms: float = 0.0

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
        """Save checkpoint state to storage."""
        checkpoint_data = CheckpointData(
            run_id=self.run_id,
            step_id=self.step_id,
            status=self.status,
            messages=self.messages,
            pending_user_messages=self.pending_user_messages,
            last_tool_calls=[],
            last_tool_results=[],
        )
        try:
            self.storage.save_checkpoint(checkpoint_data)
        except (IOError, OSError) as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _maybe_update_checkpoint(self) -> None:
        """Update checkpoint only if enough steps have passed."""
        self._steps_since_checkpoint += 1
        if self._steps_since_checkpoint >= self.checkpoint_interval:
            self._update_checkpoint()
            self._steps_since_checkpoint = 0

    def _drain_pending_messages(self) -> List[str]:
        messages = self.pending_user_messages[:]
        self.pending_user_messages.clear()
        return messages

    def _start_new_run(self) -> None:
        self.run_id = f"run_{uuid.uuid4().hex[:16]}_{self.project_name}_{self.react_type}"
        self.step_id = 0
        self.status = ReactStatus.RUNNING
        self._steps_since_checkpoint = 0

        # Reset metrics for new run
        self._total_llm_calls = 0
        self._total_tool_calls = 0
        self._llm_duration_ms = 0.0
        self._tool_duration_ms = 0.0

        system_prompt = self.build_prompt_function()
        self.messages = [{"role": "system", "content": system_prompt}]

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call LLM service with timing and metrics tracking."""
        if not self.llm_service.validate_config():
            logger.warning("LLM service is not configured")
            return '{"type": "final", "final": "LLM service is not configured."}'

        loop = asyncio.get_event_loop()
        model_to_use = self.llm_service.default_model or "qwen-plus"
        temperature_to_use = getattr(self.llm_service, "temperature", 0.7)

        start_time = time.time()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_service.completion(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature_to_use,
                    stream=False,
                ),
            )
            duration_ms = (time.time() - start_time) * 1000
            self._total_llm_calls += 1
            self._llm_duration_ms += duration_ms
            logger.debug(f"LLM call completed in {duration_ms:.2f}ms")

            if isinstance(response, dict):
                choices = response.get("choices", [])
                if choices:
                    choice = choices[0]
                    message = choice.get("message") if isinstance(choice, dict) else None
                    if message and isinstance(message, dict):
                        return message.get("content", "")
                    return choice.get("text", "")
            return ""
        except Exception as exc:
            logger.error(f"LLM call failed: {exc}", exc_info=True)
            return f'{{"type": "final", "final": "LLM call failed: {str(exc)}"}}'

    def _parse_action(self, response_text: str) -> ReactAction:
        """
        Parse LLM response into a ReactAction.

        Uses ReactActionParser for robust parsing with multiple fallback strategies.
        """
        return ReactActionParser.parse(response_text)

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute tool with timing and metrics tracking."""
        start_time = time.time()
        try:
            result = self.tool_call_function(tool_name, tool_args)
            if inspect.isawaitable(result):
                result = await result

            if inspect.isasyncgen(result) or hasattr(result, "__aiter__"):
                last_item = None
                async for item in result:
                    last_item = item
                    yield {"progress": item}
                duration_ms = (time.time() - start_time) * 1000
                self._total_tool_calls += 1
                self._tool_duration_ms += duration_ms
                logger.debug(f"Tool '{tool_name}' completed in {duration_ms:.2f}ms (stream)")
                yield {"result": last_item}
                return

            duration_ms = (time.time() - start_time) * 1000
            self._total_tool_calls += 1
            self._tool_duration_ms += duration_ms
            logger.debug(f"Tool '{tool_name}' completed in {duration_ms:.2f}ms")
            yield {"result": result}
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Tool '{tool_name}' failed after {duration_ms:.2f}ms: {exc}", exc_info=True)
            yield {"error": str(exc)}

    async def chat_stream(self, user_message: Optional[str]) -> AsyncGenerator[ReactEvent, None]:
        """Main ReAct loop with thread safety and iterative pending message processing."""
        async with self._loop_lock:
            if self._in_react_loop:
                # If loop is already running, queue the message and return
                if user_message:
                    self.pending_user_messages.append(user_message)
                    self._maybe_update_checkpoint()
                return

            # Start new run if needed
            if not self.run_id or self.status in {ReactStatus.IDLE, ReactStatus.FINAL, ReactStatus.FAILED}:
                self._start_new_run()

            # Add initial user message
            if user_message:
                self.pending_user_messages.append(user_message)

            # Add all pending messages to conversation
            pending_messages = self._drain_pending_messages()
            for msg in pending_messages:
                self.messages.append({"role": "user", "content": msg})

            self._in_react_loop = True
            self._maybe_update_checkpoint()

        try:
            # Main ReAct loop - iteratively process all messages
            while True:
                # Process messages until we reach a terminal state
                for step in range(self.step_id, self.max_steps):
                    self.step_id = step
                    self._maybe_update_checkpoint()

                    # Check for new pending messages (added while we're processing)
                    new_pending = self._drain_pending_messages()
                    for msg in new_pending:
                        self.messages.append({"role": "user", "content": msg})

                    response_text = await self._call_llm(self.messages)
                    action = self._parse_action(response_text)
                    thinking = ReactActionParser.get_thinking_message(action, step + 1, self.max_steps)
                    yield self._create_event(ReactEventType.LLM_THINKING, {
                        "message": thinking,
                        "step": step + 1,
                        "total_steps": self.max_steps,
                    })

                    yield self._create_event(ReactEventType.LLM_OUTPUT, {
                        "content": response_text,
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
                                if "error" in item:
                                    tool_result = item["error"]
                                    break
                            if tool_result is None:
                                tool_result = "Tool execution completed"
                            yield self._create_event(ReactEventType.TOOL_END, action.to_end_payload(result=tool_result, ok=True))
                            self.messages.append({"role": "assistant", "content": response_text})
                            self.messages.append({"role": "user", "content": f"Observation: {tool_result}"})
                        except Exception as exc:
                            logger.error(f"Tool execution error: {exc}", exc_info=True)
                            yield self._create_event(ReactEventType.TOOL_END, action.to_end_payload(ok=False, error=str(exc)))
                            self.messages.append({"role": "assistant", "content": response_text})
                            self.messages.append({"role": "user", "content": f"Error: {str(exc)}"})
                        continue

                    if action.is_final():
                        assert isinstance(action, FinalAction), f"Expected FinalAction, got {type(action)}"
                        self.status = ReactStatus.FINAL
                        self._update_checkpoint()
                        yield self._create_event(ReactEventType.FINAL, action.to_final_payload())
                        break

                # Check if we've reached max steps
                if self.status != ReactStatus.FINAL:
                    max_steps_action = ReactActionParser.create_final_action(
                        final="Reached maximum steps without completion",
                        stop_reason=ReactActionParser.get_max_steps_stop_reason()
                    )
                    self.status = ReactStatus.FINAL
                    self._update_checkpoint()
                    yield self._create_event(ReactEventType.FINAL, max_steps_action.to_final_payload())

                # Check if there are more messages to process (iterative, not recursive!)
                async with self._loop_lock:
                    if not self.pending_user_messages:
                        break
                    # Prepare for next iteration
                    self._start_new_run()
                    pending_messages = self._drain_pending_messages()
                    for msg in pending_messages:
                        self.messages.append({"role": "user", "content": msg})
                    self._in_react_loop = True
                    self._maybe_update_checkpoint()

        except Exception as exc:
            logger.error(f"React loop error: {exc}", exc_info=True)
            self.status = ReactStatus.FAILED
            self._update_checkpoint()
            yield self._create_event(ReactEventType.ERROR, {
                "error": ReactActionParser.get_error_summary(exc),
                "details": repr(exc),
            })
        finally:
            async with self._loop_lock:
                self._in_react_loop = False
                self._update_checkpoint()

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

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        async with self._loop_lock:
            self._in_react_loop = False
        # Reset status to idle for clean state
        if self.status in {ReactStatus.RUNNING, ReactStatus.WAITING}:
            self.status = ReactStatus.IDLE
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for this React instance."""
        return {
            "run_id": self.run_id,
            "step_id": self.step_id,
            "status": self.status,
            "total_llm_calls": self._total_llm_calls,
            "total_tool_calls": self._total_tool_calls,
            "llm_duration_ms": round(self._llm_duration_ms, 2),
            "tool_duration_ms": round(self._tool_duration_ms, 2),
            "pending_messages": len(self.pending_user_messages),
            "message_count": len(self.messages),
        }
