"""
Main agent module for Filmeto application.
Implements the FilmetoAgent class with streaming capabilities.
"""
import json
import logging
import re
import uuid
from typing import AsyncIterator, Dict, List, Optional, Callable, Any
from agent.chat.agent_chat_message import AgentMessage, MessageType
from agent.llm.llm_service import LlmService
from agent.plan.models import Plan, PlanInstance, PlanTask, TaskStatus
from agent.plan.service import PlanService
from agent.sub_agent.sub_agent import SubAgent
from agent.sub_agent.sub_agent_service import SubAgentService

logger = logging.getLogger(__name__)


_MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_-]+)")
_PRODUCER_NAME = "producer"


class AgentRole:
    """Represents an agent with a specific role in the conversation."""
    
    def __init__(self, agent_id: str, name: str, role_description: str, handler_func: Callable):
        self.agent_id = agent_id
        self.name = name
        self.role_description = role_description
        self.handler_func = handler_func
    
    async def handle_message(self, message: AgentMessage) -> AsyncIterator[AgentMessage]:
        """Handle a message and yield responses."""
        async for response in self.handler_func(message):
            yield response


class AgentStreamSession:
    """Represents a streaming session with the agent."""
    
    def __init__(self, session_id: str, initial_message: str):
        self.session_id = session_id
        self.initial_message = initial_message
        self.responses = []
        self.is_active = True


class StreamEvent:
    """Represents an event in the streaming process."""
    
    def __init__(self, event_type: str, data: Any, timestamp: float = None):
        import time
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or time.time()


class FilmetoAgent:
    """
    Class for managing agent capabilities in Filmeto.
    Provides streaming conversation interface and manages multiple agents.
    """

    def __init__(
        self,
        workspace=None,
        project=None,
        model='gpt-4o-mini',
        temperature=0.7,
        streaming=True,
        llm_service: Optional[LlmService] = None,
        sub_agent_service: Optional[SubAgentService] = None,
        plan_service: Optional[PlanService] = None,
    ):
        """Initialize the FilmetoAgent instance."""
        self.workspace = workspace
        self.project = project
        self.model = model
        self.temperature = temperature
        self.streaming = streaming
        self.agents: Dict[str, AgentRole] = {}
        self.conversation_history: List[AgentMessage] = []
        self.ui_callbacks = []
        self.current_session: Optional[AgentStreamSession] = None
        self.llm_service = llm_service or LlmService(workspace)
        self.sub_agent_service = sub_agent_service or SubAgentService()
        self.plan_service = plan_service or PlanService()
        self.sub_agents: Dict[str, SubAgent] = {}
        self._sub_agent_lookup: Dict[str, SubAgent] = {}

        # Initialize the agent
        self._init_agent()
        self._ensure_sub_agents_loaded()
    
    def _init_agent(self):
        """Initialize the agent using LlmService."""
        # Check if the LLM service is properly configured
        if self.llm_service and self.llm_service.validate_config():
            # Agent is properly configured
            pass
        else:
            # Agent not configured due to missing API key or base URL
            pass
    
    def register_agent(self, agent_id: str, name: str, role_description: str, handler_func: Callable):
        """
        Register a new agent with a specific role.

        Args:
            agent_id: Unique identifier for the agent
            name: Display name for the agent
            role_description: Description of the agent's role
            handler_func: Async function that handles messages and yields responses
        """
        self.agents[agent_id] = AgentRole(agent_id, name, role_description, handler_func)

    def get_agent(self, agent_id: str) -> Optional[AgentRole]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[AgentRole]:
        """List all registered agents."""
        return list(self.agents.values())

    def _ensure_sub_agents_loaded(self, refresh: bool = False) -> Dict[str, SubAgent]:
        if not self.project:
            self.sub_agents = {}
            self._sub_agent_lookup = {}
            return {}

        sub_agents = self.sub_agent_service.load_project_sub_agents(self.project, refresh=refresh)
        self.sub_agents = sub_agents
        self._sub_agent_lookup = {name.lower(): agent for name, agent in sub_agents.items()}

        for sub_agent in sub_agents.values():
            self._register_sub_agent(sub_agent)

        return sub_agents

    def _register_sub_agent(self, sub_agent: SubAgent) -> None:
        def make_handler(sub_agent_instance: SubAgent):
            async def handler(message: AgentMessage):
                plan_id = message.metadata.get("plan_id") if message.metadata else None
                # Note: In this context, we don't have direct access to on_stream_event
                # The streaming happens through the main chat_stream method which handles events
                async for token in sub_agent_instance.chat_stream(message.content, plan_id=plan_id):
                    metadata = {"plan_id": plan_id} if plan_id else {}
                    response = AgentMessage(
                        content=token,
                        message_type=MessageType.TEXT,
                        sender_id=sub_agent_instance.config.name,
                        sender_name=sub_agent_instance.config.name.capitalize(),
                        metadata=metadata,
                    )
                    logger.info(f"📤 Sending agent message: id={response.message_id}, sender='{response.sender_id}', content_preview='{token[:50]}{'...' if len(token) > 50 else ''}'")
                    yield response
            return handler

        self.register_agent(
            agent_id=sub_agent.config.name,
            name=sub_agent.config.name.capitalize(),
            role_description=sub_agent.config.description,
            handler_func=make_handler(sub_agent),
        )

    def _extract_mentions(self, content: str) -> List[str]:
        if not content:
            return []
        return [match.group(1) for match in _MENTION_PATTERN.finditer(content)]

    def _resolve_mentioned_sub_agent(self, content: str) -> Optional[SubAgent]:
        for mention in self._extract_mentions(content):
            candidate = mention.lower()
            sub_agent = self._sub_agent_lookup.get(candidate)
            if sub_agent:
                return sub_agent
        return None

    def _resolve_mentioned_agent_role(self, content: str) -> Optional[AgentRole]:
        for mention in self._extract_mentions(content):
            candidate = mention.lower()
            for agent in self.agents.values():
                if agent.agent_id.lower() == candidate or agent.name.lower() == candidate:
                    return agent
        return None

    def _get_producer_sub_agent(self) -> Optional[SubAgent]:
        return self._sub_agent_lookup.get(_PRODUCER_NAME)

    def _resolve_project_id(self) -> Optional[str]:
        project = self.project
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

    def _truncate_text(self, text: str, limit: int = 160) -> str:
        if text is None:
            return ""
        text = text.strip()
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."

    def _build_producer_message(self, user_message: str, plan_id: str, retry: bool = False) -> str:
        available = ", ".join(sorted(self.sub_agents.keys())) or "none"
        header = "The current plan has no tasks. Update it now." if retry else "Create a production plan."
        return "\n".join([
            f"{header}",
            f"User request: {user_message}",
            f"Plan id: {plan_id}",
            f"Available sub-agents: {available}",
            "Use plan_update to set name, description, and tasks.",
            "Each task must include: id, name, description, agent_role, needs, parameters.",
            "After updating the plan, respond with a final summary and next steps.",
        ])

    def _build_task_message(self, task: PlanTask, plan_id: str) -> str:
        parameters = json.dumps(task.parameters or {}, ensure_ascii=True)
        needs = ", ".join(task.needs) if task.needs else "none"
        return "\n".join([
            f"@{task.agent_role}",
            f"Plan id: {plan_id}",
            f"Task id: {task.id}",
            f"Task name: {task.name}",
            f"Task description: {task.description}",
            f"Dependencies: {needs}",
            f"Parameters: {parameters}",
            "Respond with your output. If needed, update the plan with plan_update.",
        ])

    def _create_plan(self, project_id: str, user_message: str) -> Optional[Plan]:
        if not project_id:
            return None
        name = "Producer Plan"
        description = self._truncate_text(user_message)
        metadata = {"source": _PRODUCER_NAME, "request": user_message}
        return self.plan_service.create_plan(
            project_id=project_id,
            name=name,
            description=description,
            tasks=[],
            metadata=metadata,
        )

    def _producer_response_has_error(self, response: Optional[str]) -> bool:
        if not response:
            return False
        lowered = response.lower()
        return "llm service is not configured" in lowered or "error calling llm" in lowered

    def _dependencies_satisfied(self, plan_instance: PlanInstance, task: PlanTask) -> bool:
        if not task.needs:
            return True
        for dependency_id in task.needs:
            dependency = next((t for t in plan_instance.tasks if t.id == dependency_id), None)
            if not dependency or dependency.status != TaskStatus.COMPLETED:
                return False
        return True

    def _get_ready_tasks(self, plan_instance: PlanInstance) -> List[PlanTask]:
        ready = []
        for task in plan_instance.tasks:
            if task.status not in {TaskStatus.CREATED, TaskStatus.READY}:
                continue
            if self._dependencies_satisfied(plan_instance, task):
                ready.append(task)
        return ready

    def _has_incomplete_tasks(self, plan_instance: PlanInstance) -> bool:
        for task in plan_instance.tasks:
            if task.status not in {TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED}:
                return True
        return False

    async def _stream_agent_messages(
        self,
        responses: AsyncIterator[AgentMessage],
        session_id: str,
        on_token: Optional[Callable[[str], None]],
        on_stream_event: Optional[Callable[[StreamEvent], None]],
    ) -> AsyncIterator[str]:
        async for response in responses:
            self.conversation_history.append(response)
            if on_token:
                on_token(response.content)
            if on_stream_event:
                on_stream_event(StreamEvent("agent_response", {
                    "content": response.content,
                    "sender_name": response.sender_name,
                    "message_type": response.message_type.value,
                    "session_id": session_id,
                }))
            yield response.content

    async def _stream_sub_agent(
        self,
        sub_agent: SubAgent,
        message: str,
        plan_id: Optional[str],
        session_id: str,
        on_token: Optional[Callable[[str], None]],
        on_stream_event: Optional[Callable[[StreamEvent], None]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        async def response_iter():
            async for token in sub_agent.chat_stream(message, on_stream_event=on_stream_event, plan_id=plan_id):
                response_metadata = dict(metadata or {})
                if plan_id:
                    response_metadata.setdefault("plan_id", plan_id)
                response = AgentMessage(
                    content=token,
                    message_type=MessageType.TEXT,
                    sender_id=sub_agent.config.name,
                    sender_name=sub_agent.config.name.capitalize(),
                    metadata=response_metadata,
                )
                logger.info(f"📤 Sending agent message: id={response.message_id}, sender='{response.sender_id}', content_preview='{token[:50]}{'...' if len(token) > 50 else ''}'")
                yield response

        async for content in self._stream_agent_messages(
            response_iter(),
            session_id,
            on_token,
            on_stream_event,
        ):
            yield content

    async def _stream_error_message(
        self,
        message: str,
        session_id: str,
        on_token: Optional[Callable[[str], None]],
        on_stream_event: Optional[Callable[[StreamEvent], None]],
    ) -> AsyncIterator[str]:
        error_msg = AgentMessage(
            content=message,
            message_type=MessageType.ERROR,
            sender_id="system",
            sender_name="System",
        )
        logger.info(f"❌ Sending error message: id={error_msg.message_id}, sender='system', content_preview='{message[:50]}{'...' if len(message) > 50 else ''}'")
        self.conversation_history.append(error_msg)
        if on_token:
            on_token(error_msg.content)
        if on_stream_event:
            on_stream_event(StreamEvent("error", {
                "content": error_msg.content,
                "session_id": session_id,
            }))
        yield error_msg.content

    def add_ui_callback(self, callback):
        """Add a UI callback for streaming events."""
        if callback not in self.ui_callbacks:
            self.ui_callbacks.append(callback)

    def remove_ui_callback(self, callback):
        """Remove a UI callback."""
        if callback in self.ui_callbacks:
            self.ui_callbacks.remove(callback)

    def get_current_session(self) -> Optional[AgentStreamSession]:
        """Get the current streaming session."""
        return self.current_session

    async def chat_stream(self, message: str, on_token=None, on_complete=None, on_stream_event=None):
        """
        Stream responses for a chat conversation with the agents.
        
        Args:
            message: The message to process
            on_token: Callback for each token received
            on_complete: Callback when response is complete
            on_stream_event: Callback for stream events
        """
        # Create an AgentMessage from the string
        initial_prompt = AgentMessage(
            content=message,
            message_type=MessageType.TEXT,
            sender_id="user",
            sender_name="User"
        )
        logger.info(f"📥 Created initial prompt message: id={initial_prompt.message_id}, sender='user', content_preview='{message[:50]}{'...' if len(message) > 50 else ''}'")
        
        # Create a new session
        session_id = str(uuid.uuid4())
        self.current_session = AgentStreamSession(session_id, message)
        
        # Add the initial prompt to history
        self.conversation_history.append(initial_prompt)
        
        # Send a stream event for the user message
        if on_stream_event:
            on_stream_event(StreamEvent("user_message", {"content": message, "session_id": session_id}))

        self._ensure_sub_agents_loaded()

        mentioned_sub_agent = self._resolve_mentioned_sub_agent(message)
        if mentioned_sub_agent and mentioned_sub_agent.config.name.lower() != _PRODUCER_NAME:
            async for content in self._stream_sub_agent(
                mentioned_sub_agent,
                message,
                plan_id=None,
                session_id=session_id,
                on_token=on_token,
                on_stream_event=on_stream_event,
            ):
                yield content
            if on_complete:
                on_complete(message)
            return

        producer_agent = self._get_producer_sub_agent()
        if producer_agent:
            async for content in self._handle_producer_flow(
                initial_prompt=initial_prompt,
                producer_agent=producer_agent,
                session_id=session_id,
                on_token=on_token,
                on_stream_event=on_stream_event,
            ):
                yield content
            if on_complete:
                on_complete(message)
            return

        mentioned_agent = self._resolve_mentioned_agent_role(message)
        if mentioned_agent:
            async for content in self._stream_agent_messages(
                mentioned_agent.handle_message(initial_prompt),
                session_id,
                on_token,
                on_stream_event,
            ):
                yield content
            if on_complete:
                on_complete(message)
            return

        responding_agent = await self._select_responding_agent(initial_prompt)
        if responding_agent:
            async for content in self._stream_agent_messages(
                responding_agent.handle_message(initial_prompt),
                session_id,
                on_token,
                on_stream_event,
            ):
                yield content
        else:
            async for content in self._stream_error_message(
                "No suitable agent found to handle this request.",
                session_id,
                on_token,
                on_stream_event,
            ):
                yield content

        # Call on_complete callback if provided
        if on_complete:
            on_complete(message)

    async def _handle_producer_flow(
        self,
        initial_prompt: AgentMessage,
        producer_agent: SubAgent,
        session_id: str,
        on_token: Optional[Callable[[str], None]],
        on_stream_event: Optional[Callable[[StreamEvent], None]],
    ) -> AsyncIterator[str]:
        project_id = self._resolve_project_id()
        if not project_id:
            async for content in self._stream_sub_agent(
                producer_agent,
                initial_prompt.content,
                plan_id=None,
                session_id=session_id,
                on_token=on_token,
                on_stream_event=on_stream_event,
            ):
                yield content
            return

        plan = self._create_plan(project_id, initial_prompt.content)
        if not plan:
            async for content in self._stream_sub_agent(
                producer_agent,
                initial_prompt.content,
                plan_id=None,
                session_id=session_id,
                on_token=on_token,
                on_stream_event=on_stream_event,
            ):
                yield content
            return

        producer_message = self._build_producer_message(initial_prompt.content, plan.id)
        producer_response = None
        async for content in self._stream_sub_agent(
            producer_agent,
            producer_message,
            plan_id=plan.id,
            session_id=session_id,
            on_token=on_token,
            on_stream_event=on_stream_event,
            metadata={"plan_id": plan.id},
        ):
            producer_response = content
            yield content

        if self._producer_response_has_error(producer_response):
            return

        plan = self.plan_service.load_plan(project_id, plan.id)
        if not plan or not plan.tasks:
            retry_message = self._build_producer_message(initial_prompt.content, plan.id, retry=True)
            retry_response = None
            async for content in self._stream_sub_agent(
                producer_agent,
                retry_message,
                plan_id=plan.id,
                session_id=session_id,
                on_token=on_token,
                on_stream_event=on_stream_event,
                metadata={"plan_id": plan.id, "retry": True},
            ):
                retry_response = content
                yield content
            if self._producer_response_has_error(retry_response):
                return
            plan = self.plan_service.load_plan(project_id, plan.id)

        if not plan or not plan.tasks:
            async for content in self._stream_error_message(
                "Producer did not generate any plan tasks.",
                session_id,
                on_token,
                on_stream_event,
            ):
                yield content
            return

        async for content in self._execute_plan_tasks(
            plan=plan,
            session_id=session_id,
            on_token=on_token,
            on_stream_event=on_stream_event,
        ):
            yield content

    async def _execute_plan_tasks(
        self,
        plan: Plan,
        session_id: str,
        on_token: Optional[Callable[[str], None]],
        on_stream_event: Optional[Callable[[StreamEvent], None]],
    ) -> AsyncIterator[str]:
        plan_instance = self.plan_service.create_plan_instance(plan)
        self.plan_service.start_plan_execution(plan_instance)

        while True:
            ready_tasks = self._get_ready_tasks(plan_instance)
            if not ready_tasks:
                if self._has_incomplete_tasks(plan_instance):
                    async for content in self._stream_error_message(
                        "Plan execution blocked by unmet dependencies or missing agents.",
                        session_id,
                        on_token,
                        on_stream_event,
                    ):
                        yield content
                break

            for task in ready_tasks:
                self.plan_service.mark_task_running(plan_instance, task.id)
                target_agent = self._sub_agent_lookup.get(task.agent_role.lower())
                if not target_agent:
                    error_message = f"Sub-agent '{task.agent_role}' not found for task {task.id}."
                    self.plan_service.mark_task_failed(plan_instance, task.id, error_message)
                    async for content in self._stream_error_message(
                        error_message,
                        session_id,
                        on_token,
                        on_stream_event,
                    ):
                        yield content
                    continue

                task_message = self._build_task_message(task, plan.id)
                async for content in self._stream_sub_agent(
                    target_agent,
                    task_message,
                    plan_id=plan.id,
                    session_id=session_id,
                    on_token=on_token,
                    on_stream_event=on_stream_event,
                    metadata={"plan_id": plan.id, "task_id": task.id},
                ):
                    yield content
                self.plan_service.mark_task_completed(plan_instance, task.id)

            updated_plan = self.plan_service.load_plan(plan.project_id, plan.id)
            if updated_plan:
                plan_instance = self.plan_service.sync_plan_instance(plan_instance, updated_plan)

    async def _select_responding_agent(self, message: AgentMessage) -> Optional[AgentRole]:
        """
        Select which agent should respond to a message based on content or routing rules.

        Args:
            message: The message to route

        Returns:
            AgentRole: The selected agent or None if no agent should respond
        """
        mentioned_agent = self._resolve_mentioned_agent_role(message.content)
        if mentioned_agent:
            return mentioned_agent

        producer_agent = self.get_agent(_PRODUCER_NAME)
        if producer_agent:
            return producer_agent

        content_lower = message.content.lower()
        for agent in self.agents.values():
            if agent.name.lower() in content_lower or agent.agent_id.lower() in content_lower:
                return agent

        if self.agents:
            return next(iter(self.agents.values()))

        return None

    def get_conversation_history(self) -> List[AgentMessage]:
        """Get the entire conversation history."""
        return self.conversation_history.copy()

    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()

    def update_context(self, project=None):
        """Update the agent context with new project information."""
        if project:
            self.project = project
            self._ensure_sub_agents_loaded(refresh=True)

    async def broadcast_message(self, message: AgentMessage) -> AsyncIterator[AgentMessage]:
        """
        Broadcast a message to all agents and collect their responses.

        Args:
            message: The message to broadcast

        Yields:
            AgentMessage: Responses from all agents
        """
        for agent in self.agents.values():
            try:
                async for response in agent.handle_message(message):
                    self.conversation_history.append(response)
                    yield response.content  # Yield just the content for consistency
            except Exception as e:
                error_msg = AgentMessage(
                    content=f"Error in agent {agent.name}: {str(e)}",
                    message_type=MessageType.ERROR,
                    sender_id="system",
                    sender_name="System"
                )
                logger.info(f"❌ Broadcasting error message: id={error_msg.message_id}, sender='system', content_preview='{error_msg.content[:50]}{'...' if len(error_msg.content) > 50 else ''}'")
                self.conversation_history.append(error_msg)
                yield error_msg.content  # Yield just the content for consistency