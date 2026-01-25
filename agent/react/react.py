import asyncio
import json
import re
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional
from pathlib import Path

from agent.llm.llm_service import LlmService
from agent.prompt.prompt_service import prompt_service

from .types import ReactEvent, ReactEventType, ReactStatus, CheckpointData
from .storage import ReactStorage


class React:
    """
    A generic ReAct processor that handles the ReAct (Reasoning and Acting) loop.
    It can be configured with a base prompt template and a tool calling function.
    """
    
    def __init__(
        self,
        project_name: str,
        react_type: str,
        build_prompt_function: Optional[Callable[[str], str]] = None,
        react_tool_call_function: Callable[[str, Dict[str, Any]], Any] = None,
        *,
        workspace = None,
        llm_service = None,
        max_steps: int = 20,
    ):
        """
        Initialize the React processor.

        Args:
            project_name: Name of the project (used for identification and storage)
            react_type: Type of ReAct process (used for identification and storage)
            build_prompt_function: Optional function to build the prompt dynamically
            react_tool_call_function: Async function to call tools (tool_name, tool_args) -> result
            workspace: Workspace instance to use for the React process
            llm_service: LlmService instance to use for LLM calls
            max_steps: Maximum number of ReAct steps to perform
        """
        self.project_name = project_name
        self.react_type = react_type
        self.build_prompt_function = build_prompt_function
        self.react_tool_call_function = react_tool_call_function
        self.workspace = workspace
        self.llm_service = llm_service
        self.max_steps = max_steps

        # Determine workspace root from workspace if available, otherwise default
        if workspace and hasattr(workspace, 'workspace_dir'):
            self.workspace_root = workspace.workspace_dir
        else:
            self.workspace_root = "workspace"

        # Initialize storage
        self.storage = ReactStorage(
            project_name=project_name,
            react_type=react_type,
            workspace_root=self.workspace_root
        )

        # Initialize state variables
        self.run_id: str = ""
        self.step_id: int = 0
        self.status: str = ReactStatus.IDLE
        self.messages: List[Dict[str, str]] = []
        self.pending_user_messages: List[str] = []
        self._in_react_loop: bool = False  # Flag to track if we're currently in a react step loop
        self._pending_start_fresh: bool = False  # Flag to track if next queued message should start fresh

        # Attempt to load existing checkpoint
        checkpoint = self.storage.load_checkpoint()
        if checkpoint and checkpoint.status == ReactStatus.RUNNING:
            self.run_id = checkpoint.run_id
            self.step_id = checkpoint.step_id
            self.status = checkpoint.status
            self.messages = checkpoint.messages
            # Restore pending messages
            self.pending_user_messages = list(checkpoint.pending_user_messages)
        else:
            # Initialize a new run
            self.run_id = ""
            self.step_id = 0
            self.status = ReactStatus.IDLE
            self.messages = []
            self.pending_user_messages = []
    
    def _create_event(self, event_type: str, payload: Dict[str, Any]) -> ReactEvent:
        """
        Create a ReactEvent with current context.
        """
        return ReactEvent(
            event_type=event_type,
            project_name=self.project_name,
            react_type=self.react_type,
            run_id=self.run_id,
            step_id=self.step_id,
            payload=payload
        )
    
    def _update_checkpoint(self):
        """
        Update the checkpoint with current state.
        """
        checkpoint_data = CheckpointData(
            run_id=self.run_id,
            step_id=self.step_id,
            status=self.status,
            messages=self.messages,
            pending_user_messages=self.pending_user_messages,
            last_tool_calls=[],  # Will be updated during execution
            last_tool_results=[]  # Will be updated during execution
        )
        self.storage.save_checkpoint(checkpoint_data)

    def _drain_pending_messages(self) -> List[str]:
        """
        Drain all pending user messages from the list.
        """
        messages = self.pending_user_messages[:]
        self.pending_user_messages.clear()
        return messages

    async def resume(self) -> AsyncGenerator[ReactEvent, None]:
        """
        Resume the ReAct process from the last checkpoint.

        Yields:
            ReactEvent: Events during the ReAct process
        """
        # Load the checkpoint if not already loaded
        checkpoint = self.storage.load_checkpoint()
        if not checkpoint:
            yield self._create_event(ReactEventType.ERROR, {
                "error": "No checkpoint found to resume from",
                "details": "Cannot resume ReAct process without a saved checkpoint"
            })
            return

        # Restore state from checkpoint
        self.run_id = checkpoint.run_id
        self.step_id = checkpoint.step_id
        self.status = checkpoint.status
        self.messages = checkpoint.messages
        self.pending_user_messages = list(checkpoint.pending_user_messages)
        # Reset the loop flag when resuming (will be set when we enter the loop)
        self._in_react_loop = False

        # Continue the ReAct process from where it left off
        remaining_steps = self.max_steps - self.step_id

        # Set flag to indicate we're entering the react loop
        self._in_react_loop = True
        self._update_checkpoint()

        try:
            for step in range(remaining_steps):
                current_step = self.step_id + step
                self.step_id = current_step
                self._update_checkpoint()  # Update checkpoint at the beginning of each step

                # Yield thinking event
                yield self._create_event(ReactEventType.LLM_THINKING, {
                    "message": f"Resuming step {current_step + 1}/{self.max_steps}",
                    "step": current_step + 1,
                    "total_steps": self.max_steps
                })

                # Before calling LLM, drain any new pending messages that arrived during the loop
                new_pending = self._drain_pending_messages()
                if new_pending:
                    # Add new pending messages to the conversation history
                    for msg in new_pending:
                        self.messages.append({"role": "user", "content": msg})

                # Call LLM to get response
                try:
                    response_text = await self._call_llm(self.messages)

                    # Yield LLM output event
                    yield self._create_event(ReactEventType.LLM_OUTPUT, {
                        "content": response_text
                    })

                    # Parse the response to determine next action
                    action = self._parse_action(response_text)

                    if action["type"] == "tool":
                        # Yield tool start event
                        yield self._create_event(ReactEventType.TOOL_START, {
                            "tool_name": action["tool_name"],
                            "tool_args": action["tool_args"]
                        })

                        # Execute the tool
                        try:
                            tool_result = await self.react_tool_call_function(
                                action["tool_name"],
                                action["tool_args"]
                            )

                            # Yield tool end event
                            yield self._create_event(ReactEventType.TOOL_END, {
                                "tool_name": action["tool_name"],
                                "ok": True,
                                "result": tool_result
                            })

                            # Add assistant response and tool result to messages
                            self.messages.append({"role": "assistant", "content": response_text})
                            self.messages.append({"role": "user", "content": f"Observation: {tool_result}"})

                        except Exception as e:
                            # Yield tool end event with error
                            yield self._create_event(ReactEventType.TOOL_END, {
                                "tool_name": action["tool_name"],
                                "ok": False,
                                "error": str(e)
                            })

                            # Add assistant response and error to messages
                            self.messages.append({"role": "assistant", "content": response_text})
                            self.messages.append({"role": "user", "content": f"Error: {str(e)}"})

                    elif action["type"] == "final":
                        # Yield final event
                        yield self._create_event(ReactEventType.FINAL, {
                            "final_response": action["final"],
                            "stop_reason": "final_action",
                            "summary": "ReAct process completed successfully"
                        })

                        self.status = ReactStatus.FINAL
                        self._update_checkpoint()
                        break  # Exit the loop

                except Exception as e:
                    # Yield error event
                    yield self._create_event(ReactEventType.ERROR, {
                        "error": str(e),
                        "details": repr(e)
                    })

                    self.status = ReactStatus.FAILED
                    self._update_checkpoint()
                    raise e

            # If we reach max steps without a final action
            if self.status != ReactStatus.FINAL:
                yield self._create_event(ReactEventType.FINAL, {
                    "final_response": "Reached maximum steps without completion",
                    "stop_reason": "max_steps_reached",
                    "summary": f"ReAct process stopped after {self.max_steps} steps"
                })
                self.status = ReactStatus.FINAL
                self._update_checkpoint()

        finally:
            # Set flag to indicate we're exiting the react loop
            self._in_react_loop = False
            self._update_checkpoint()

        # After the react loop ends, check if there are pending messages
        # If so, automatically start a new react loop
        while self.pending_user_messages:
            # Get the next pending message
            next_message = self.pending_user_messages.pop(0)
            # Check if we should start fresh for this message
            should_start_fresh = self._pending_start_fresh
            self._pending_start_fresh = False  # Reset the flag
            # Process it in a new react loop
            async for event in self.chat_stream(next_message):
                yield event
    
    async def chat_stream(self, user_message: str) -> AsyncGenerator[ReactEvent, None]:
        """
        Trigger or continue the ReAct process with a user message.

        Args:
            user_message: Message from the user

        Yields:
            ReactEvent: Events during the ReAct process
        """
        # If we're already in a react loop, add the message to the waiting queue
        if self._in_react_loop:
            self.pending_user_messages.append(user_message)
            # Always mark to start fresh for the next message when in a loop
            self._pending_start_fresh = True
            return  # Exit early, the message will be processed in the current loop or after it ends

        # Always start fresh - reset the state and initialize
        # Generate a new run ID for this fresh run
        self.run_id = f"run_{int(time.time()*1000000)}_{self.project_name}_{self.react_type}"  # Use microseconds to ensure uniqueness
        self.step_id = 0
        self.status = ReactStatus.RUNNING

        # Add user message to pending list first
        self.pending_user_messages.append(user_message)

        # Process all pending messages
        pending_messages = self._drain_pending_messages()

        # Build initial system prompt using the first pending user message
        first_user_message = pending_messages[0] if pending_messages else user_message
        system_prompt = self._build_system_prompt(first_user_message)
        self.messages = [{"role": "system", "content": system_prompt}]

        # Add all pending messages to the conversation history
        for msg in pending_messages:
            self.messages.append({"role": "user", "content": msg})

        # Set flag to indicate we're entering the react loop
        self._in_react_loop = True
        self._update_checkpoint()

        try:
            # Perform ReAct loop
            for step in range(self.max_steps):
                self.step_id = step
                self._update_checkpoint()  # Update checkpoint at the beginning of each step

                # Before calling LLM, drain any new pending messages that arrived during the loop
                new_pending = self._drain_pending_messages()
                if new_pending:
                    # Add new pending messages to the conversation history
                    for msg in new_pending:
                        self.messages.append({"role": "user", "content": msg})

                # Yield thinking event
                yield self._create_event(ReactEventType.LLM_THINKING, {
                    "message": f"Processing step {step + 1}/{self.max_steps}",
                    "step": step + 1,
                    "total_steps": self.max_steps
                })

                # Call LLM to get response
                try:
                    response_text = await self._call_llm(self.messages)

                    # Yield LLM output event
                    yield self._create_event(ReactEventType.LLM_OUTPUT, {
                        "content": response_text
                    })

                    # Parse the response to determine next action
                    action = self._parse_action(response_text)

                    if action["type"] == "tool":
                        # Yield tool start event
                        yield self._create_event(ReactEventType.TOOL_START, {
                            "tool_name": action["tool_name"],
                            "tool_args": action["tool_args"]
                        })

                        # Execute the tool
                        try:
                            tool_result = await self.react_tool_call_function(
                                action["tool_name"],
                                action["tool_args"]
                            )

                            # Yield tool end event
                            yield self._create_event(ReactEventType.TOOL_END, {
                                "tool_name": action["tool_name"],
                                "ok": True,
                                "result": tool_result
                            })

                            # Add assistant response and tool result to messages
                            self.messages.append({"role": "assistant", "content": response_text})
                            self.messages.append({"role": "user", "content": f"Observation: {tool_result}"})

                        except Exception as e:
                            # Yield tool end event with error
                            yield self._create_event(ReactEventType.TOOL_END, {
                                "tool_name": action["tool_name"],
                                "ok": False,
                                "error": str(e)
                            })

                            # Add assistant response and error to messages
                            self.messages.append({"role": "assistant", "content": response_text})
                            self.messages.append({"role": "user", "content": f"Error: {str(e)}"})

                    elif action["type"] == "final":
                        # Yield final event
                        yield self._create_event(ReactEventType.FINAL, {
                            "final_response": action["final"],
                            "stop_reason": "final_action",
                            "summary": "ReAct process completed successfully"
                        })
                        self.status = ReactStatus.FINAL
                        self._update_checkpoint()
                        break  # Exit the loop

                except Exception as e:
                    # Yield error event
                    yield self._create_event(ReactEventType.ERROR, {
                        "error": str(e),
                        "details": repr(e)
                    })
                    self.status = ReactStatus.FAILED
                    self._update_checkpoint()
                    raise e

            # If we reach max steps without a final action
            if self.status != ReactStatus.FINAL:
                yield self._create_event(ReactEventType.FINAL, {
                    "final_response": "Reached maximum steps without completion",
                    "stop_reason": "max_steps_reached",
                    "summary": f"ReAct process stopped after {self.max_steps} steps"
                })
                self.status = ReactStatus.FINAL
                self._update_checkpoint()

        finally:
            # Set flag to indicate we're exiting the react loop
            self._in_react_loop = False
            self._update_checkpoint()

        # After the react loop ends, check if there are pending messages
        # If so, automatically start a new react loop
        while self.pending_user_messages:
            # Get the next pending message
            next_message = self.pending_user_messages.pop(0)
            # Check if we should start fresh for this message
            should_start_fresh = self._pending_start_fresh
            self._pending_start_fresh = False  # Reset the flag
            # Process it in a new react loop - always start fresh
            async for event in self.chat_stream(next_message):
                yield event
    
    def _build_system_prompt(self, user_input: str = "") -> str:
        """
        Build the system prompt using the build_prompt_function if available,
        otherwise using the base template for backward compatibility.
        """
        # Use the build_prompt_function if provided
        if self.build_prompt_function:
            return self.build_prompt_function(user_input)

        # For backward compatibility, try to render the prompt using the prompt service
        # This assumes we still have a base_prompt_template-like mechanism
        rendered_prompt = prompt_service.render_prompt(
            name="react_base",  # Default template name
            title="ReAct Agent",
            agent_name=self.react_type,
            project_name=self.project_name
        )

        # If the prompt service didn't work, use the template directly
        if rendered_prompt is None:
            # For now, just return a basic ReAct prompt
            return f"""You are a ReAct-style agent. Follow the ReAct (Reasoning and Acting) framework to solve problems.

Your response should be in JSON format with one of these structures:
- For tool use: {{"type": "tool", "tool_name": "...", "tool_args": {{...}}}}
- For final response: {{"type": "final", "final": "..."}}"""

        return rendered_prompt
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call the LLM with the given messages.
        """
        # Use the provided llm_service if available, otherwise create a new one
        llm_service = self.llm_service
        # For testing purposes, we'll return a mock response if no API key is configured
        try:
            # Use the sync completion method in a thread executor to avoid async conflicts
            import asyncio
            loop = asyncio.get_event_loop()

            # Use the model and temperature from the LLM service's configuration (which comes from global settings)
            model_to_use = self.llm_service.default_model if self.llm_service.default_model else "qwen-plus"
            temperature_to_use = self.llm_service.temperature if hasattr(self.llm_service, 'temperature') else 0.7

            response = await loop.run_in_executor(
                None,
                lambda: self.llm_service.completion(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature_to_use,
                    stream=False,
                )
            )

            # Extract the content from the response
            # Handle both dictionary responses and LiteLLM ModelResponse objects
            if hasattr(response, 'choices') and response.choices:
                # This is a ModelResponse object from LiteLLM
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        return choice.message.content or ""
                    elif isinstance(choice.message, dict):
                        return choice.message.get("content", "")
                elif hasattr(choice, 'text'):
                    return choice.text or ""
            return ""
        except Exception as e:
            raise e
    
    def _parse_action(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response to determine the next action.
        """
        # First, try to extract JSON from the response
        payload = self._extract_json_payload(response_text)
        
        if payload:
            # Validate the payload structure
            action_type = payload.get("type") or payload.get("action")
            
            if action_type == "tool":
                return {
                    "type": "tool",
                    "tool_name": payload.get("tool_name") or payload.get("name"),
                    "tool_args": payload.get("tool_args") or payload.get("arguments") or payload.get("input") or {}
                }
            elif action_type == "final":
                return {
                    "type": "final",
                    "final": payload.get("final") or payload.get("response") or response_text
                }
        
        # If no valid JSON action found, treat as final response
        return {
            "type": "final",
            "final": response_text
        }
    
    def _extract_json_payload(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON payload from text response.
        """
        # Look for JSON in code blocks
        json_block_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_block_match:
            candidate = json_block_match.group(1)
            return self._safe_json_load(candidate)

        # Look for standalone JSON objects
        candidate = text.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            payload = self._safe_json_load(candidate)
            if payload is not None:
                return payload

        # Find balanced JSON object in text
        candidate = self._find_balanced_json(text)
        if candidate:
            return self._safe_json_load(candidate)
        
        return None
    
    def _safe_json_load(self, candidate: str) -> Optional[Dict[str, Any]]:
        """
        Safely load JSON from string.
        """
        try:
            payload = json.loads(candidate)
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None
    
    def _find_balanced_json(self, text: str) -> Optional[str]:
        """
        Find a balanced JSON object in text.
        """
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