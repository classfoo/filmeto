"""New Production Agent - Main orchestrator agent without LangChain/LangGraph dependencies.

This agent uses LiteLLM for LLM calls and implements a simple state machine for workflow orchestration.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Literal
from agent.sub_agents.registry import SubAgentRegistry
from agent.tools import ToolRegistry
from agent.streaming import StreamEventEmitter
from agent.workflow_logger import workflow_logger
from agent.graph.state import ProductionAgentState
from agent.nodes.question_understanding import QuestionUnderstandingNode
from agent.nodes.planner import PlannerNode
from agent.nodes.coordinator import CoordinatorNode
from agent.nodes.executor import ExecutorNode
from agent.nodes.response import ResponseNode
from agent.nodes.plan_refinement import PlanRefinementNode
from agent.nodes.sub_agent_executor import SubAgentExecutorNode, PlanReviewNode, ResultSynthesisNode
import litellm
from litellm import acompletion

# Disable LiteLLM enterprise features to prevent import errors
litellm.suppress_debug_info = True

# Additional configuration to prevent enterprise feature loading
litellm.enable_enterprise_features = False


logger = logging.getLogger(__name__)


class ProductionAgent:
    """
    New Production Agent - The main orchestrator for Filmeto without LangChain/LangGraph dependencies.

    This agent acts as the "Producer" role in film production,
    coordinating all aspects of the project and managing sub-agents.
    """

    def __init__(
        self,
        project_id: str,
        workspace: Any,
        project: Any,
        model: str,
        api_key: str,
        base_url: Optional[str] = None,
        sub_agent_registry: SubAgentRegistry = None,
        tool_registry: ToolRegistry = None,
        stream_emitter: Optional[StreamEventEmitter] = None,
        temperature: float = 0.7
    ):
        """
        Initialize New Production Agent.

        Args:
            project_id: Project identifier for context isolation
            workspace: Workspace instance
            project: Project instance
            model: Model name for LiteLLM
            api_key: API key for LLM
            base_url: Base URL for LLM API
            sub_agent_registry: Registry of sub-agents
            tool_registry: Registry of tools
            stream_emitter: Optional stream emitter for events
            temperature: Temperature for LLM
        """
        self.project_id = project_id
        self.workspace = workspace
        self.project = project
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.sub_agent_registry = sub_agent_registry or SubAgentRegistry()
        self.tool_registry = tool_registry or ToolRegistry(workspace=workspace, project=project)
        self.stream_emitter = stream_emitter

        # Initialize nodes with LiteLLM-compatible LLM wrapper
        self.llm_wrapper = LiteLLMWrapper(model=model, api_key=api_key, base_url=base_url, temperature=temperature)
        
        self.question_understanding = QuestionUnderstandingNode(self.llm_wrapper, self.sub_agent_registry)
        self.coordinator = CoordinatorNode(self.llm_wrapper, self.tool_registry.get_all_tools())
        self.planner = PlannerNode(self.llm_wrapper, self.sub_agent_registry)
        self.executor = ExecutorNode(self.llm_wrapper, self.tool_registry.get_all_tools())
        self.responder = ResponseNode(self.llm_wrapper)
        self.sub_agent_executor = SubAgentExecutorNode(
            self.sub_agent_registry,
            self.tool_registry,
            workspace=self.workspace,
            project=self.project
        )
        self.plan_review = PlanReviewNode(self.llm_wrapper)
        self.plan_refinement = PlanRefinementNode(self.llm_wrapper, self.sub_agent_registry)
        self.result_synthesis = ResultSynthesisNode(self.llm_wrapper)

        # Set stream emitters if available
        if self.stream_emitter:
            self.coordinator.set_stream_emitter(self.stream_emitter)
            self.executor.set_stream_emitter(self.stream_emitter)
            self.sub_agent_executor.set_stream_emitter(self.stream_emitter)
            self.plan_review.set_stream_emitter(self.stream_emitter)
            self.result_synthesis.set_stream_emitter(self.stream_emitter)

    async def execute(
        self,
        messages: List[Dict[str, Any]],  # List of message dicts instead of LangChain messages
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the Production Agent workflow.

        Args:
            messages: Conversation messages as list of dicts
            config: Optional configuration

        Returns:
            Final state after execution
        """
        logger.info("=" * 80)
        logger.info(f"[NewProductionAgent] ENTRY: execute")
        logger.info(f"[NewProductionAgent] Project ID: {self.project_id}")
        logger.info(f"[NewProductionAgent] Message count: {len(messages)}")
        if messages:
            last_msg = str(messages[-1].get('content', ''))[:100]
            logger.info(f"[NewProductionAgent] Last message: {last_msg}...")
        logger.info("=" * 80)

        # Create initial state
        flow_id = workflow_logger.log_flow_start(self.project_id)

        initial_state: ProductionAgentState = {
            "project_id": self.project_id,
            "messages": messages,
            "next_action": "question_understanding",
            "context": {
                "original_request": str(messages[-1].get('content', '')) if messages else ""
            },
            "iteration_count": 0,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": False,
            "plan_refinement_count": 0,
            "flow_id": flow_id
        }

        logger.info(f"[NewProductionAgent] Initial state created: next_action={initial_state['next_action']}")

        # Execute workflow with fixed logic
        final_state = await self._execute_workflow(initial_state, config)

        workflow_logger.log_flow_end(flow_id)

        logger.info("=" * 80)
        logger.info(f"[NewProductionAgent] EXIT: execute")
        logger.info(f"[NewProductionAgent] Final iteration_count: {final_state.get('iteration_count', 0)}")
        logger.info(f"[NewProductionAgent] Final next_action: {final_state.get('next_action', 'unknown')}")
        logger.info(f"[NewProductionAgent] Sub-agent results count: {len(final_state.get('sub_agent_results', {}))}")
        logger.info("=" * 80)

        return final_state

    async def stream(
        self,
        messages: List[Dict[str, Any]],  # List of message dicts instead of LangChain messages
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Stream the Production Agent workflow execution.

        Args:
            messages: Conversation messages as list of dicts
            config: Optional configuration

        Yields:
            State updates as the workflow progresses
        """
        logger.info("=" * 80)
        logger.info(f"[NewProductionAgent] ENTRY: stream")
        logger.info(f"[NewProductionAgent] Project ID: {self.project_id}")
        logger.info(f"[NewProductionAgent] Message count: {len(messages)}")
        if messages:
            last_msg = str(messages[-1].get('content', ''))[:100]
            logger.info(f"[NewProductionAgent] Last message: {last_msg}...")
        logger.info("=" * 80)

        # Create initial state
        flow_id = workflow_logger.log_flow_start(self.project_id)

        initial_state: ProductionAgentState = {
            "project_id": self.project_id,
            "messages": messages,
            "next_action": "question_understanding",
            "context": {
                "original_request": str(messages[-1].get('content', '')) if messages else ""
            },
            "iteration_count": 0,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": False,
            "plan_refinement_count": 0,
            "flow_id": flow_id
        }

        logger.info(f"[NewProductionAgent] Initial state created: next_action={initial_state['next_action']}")

        # Stream workflow execution
        event_count = 0
        async for event in self._stream_workflow(initial_state, config):
            event_count += 1
            node_names = list(event.keys())
            logger.debug(f"[NewProductionAgent] Stream event #{event_count}: nodes={node_names}")
            yield event

        workflow_logger.log_flow_end(flow_id)

        logger.info("=" * 80)
        logger.info(f"[NewProductionAgent] EXIT: stream")
        logger.info(f"[NewProductionAgent] Total events streamed: {event_count}")
        logger.info("=" * 80)

    async def _execute_workflow(self, initial_state: ProductionAgentState, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the workflow with fixed logic."""
        state = initial_state.copy()
        max_iterations = 20  # Prevent infinite loops
        
        while state.get('iteration_count', 0) < max_iterations:
            next_action = state.get('next_action', 'question_understanding')
            
            # Route based on next_action
            if next_action == 'question_understanding':
                state = self._call_node(self.question_understanding, state, config)
            elif next_action == 'coordinator':
                state = self._call_node(self.coordinator, state, config)
            elif next_action == 'planner':
                state = self._call_node(self.planner, state, config)
            elif next_action == 'use_tools':
                state = self._call_node(self.executor, state, config)
            elif next_action == 'respond':
                state = self._call_node(self.responder, state, config)
            elif next_action == 'execute_sub_agent_plan':
                state = self._call_node(self.sub_agent_executor, state, config)
            elif next_action == 'review_plan':
                state = self._call_node(self.plan_review, state, config)
            elif next_action == 'refine_plan':
                state = self._call_node(self.plan_refinement, state, config)
            elif next_action == 'synthesize_results':
                state = self._call_node(self.result_synthesis, state, config)
            else:
                # Unknown action, exit
                logger.warning(f"Unknown action: {next_action}, exiting workflow")
                break
                
            # Increment iteration count
            state['iteration_count'] = state.get('iteration_count', 0) + 1
            
            # Check if we're done
            if state.get('next_action') == 'respond':
                break
                
        return state

    async def _stream_workflow(self, initial_state: ProductionAgentState, config: Optional[Dict[str, Any]]):
        """Stream the workflow execution."""
        state = initial_state.copy()
        max_iterations = 20  # Prevent infinite loops
        
        while state.get('iteration_count', 0) < max_iterations:
            next_action = state.get('next_action', 'question_understanding')
            
            # Route based on next_action
            if next_action == 'question_understanding':
                state = self._call_node(self.question_understanding, state, config)
            elif next_action == 'coordinator':
                state = self._call_node(self.coordinator, state, config)
            elif next_action == 'planner':
                state = self._call_node(self.planner, state, config)
            elif next_action == 'use_tools':
                state = self._call_node(self.executor, state, config)
            elif next_action == 'respond':
                state = self._call_node(self.responder, state, config)
            elif next_action == 'execute_sub_agent_plan':
                state = self._call_node(self.sub_agent_executor, state, config)
            elif next_action == 'review_plan':
                state = self._call_node(self.plan_review, state, config)
            elif next_action == 'refine_plan':
                state = self._call_node(self.plan_refinement, state, config)
            elif next_action == 'synthesize_results':
                state = self._call_node(self.result_synthesis, state, config)
            else:
                # Unknown action, exit
                logger.warning(f"Unknown action: {next_action}, exiting workflow")
                break
                
            # Yield the current state update
            yield {next_action: state}
            
            # Increment iteration count
            state['iteration_count'] = state.get('iteration_count', 0) + 1
            
            # Check if we're done
            if state.get('next_action') == 'respond':
                break

    def _call_node(self, node, state: ProductionAgentState, config: Optional[Dict[str, Any]]) -> ProductionAgentState:
        """Call a node with the current state."""
        # Convert messages to LangChain format temporarily for compatibility with existing nodes
        # This is a temporary solution to reuse existing node implementations
        # In a full refactor, we'd update all nodes to work with the new format
        try:
            # Call the node's __call__ method - nodes expect (self, state), not config
            result = node(state)
            return result
        except Exception as e:
            logger.error(f"Error calling node {node.__class__.__name__}: {e}")
            # Return state unchanged in case of error
            return state


class LiteLLMWrapper:
    """
    Wrapper around LiteLLM to provide interface compatible with LangChain's ChatOpenAI.
    """

    def __init__(self, model: str, api_key: str, base_url: Optional[str] = None, temperature: float = 0.7):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature

    async def invoke(self, messages) -> Any:
        """
        Invoke the LLM with the given messages.

        Args:
            messages: List of LangChain messages or message dicts

        Returns:
            Response object with content attribute
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = convert_messages_to_openai_format(messages)

            # Prepare the call to LiteLLM
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
                "api_key": self.api_key
            }

            if self.base_url:
                kwargs["base_url"] = self.base_url

            # Make the async call to LiteLLM
            response = await acompletion(**kwargs)

            # Extract the content from the response
            content = response.choices[0].message.content

            # Return a mock response object that mimics LangChain's response
            return MockLangChainResponse(content)

        except Exception as e:
            logger.error(f"Error calling LiteLLM: {e}")
            # Return a mock response with error message
            return MockLangChainResponse(f"Error: {str(e)}")

    def bind_tools(self, tools):
        """
        Bind tools to the LLM for function calling.

        Args:
            tools: List of tools to bind

        Returns:
            A new instance with tools bound
        """
        # For now, just return self since we're not implementing full tool binding
        # In a real implementation, we would need to handle tool calling properly
        bound_instance = LiteLLMWithTools(self.model, self.api_key, self.base_url, self.temperature, tools)
        return bound_instance


class LiteLLMWithTools(LiteLLMWrapper):
    """
    LiteLLM wrapper that has tools bound to it.
    """

    def __init__(self, model: str, api_key: str, base_url: Optional[str] = None, temperature: float = 0.7, tools=None):
        super().__init__(model, api_key, base_url, temperature)
        self.tools = tools or []

    async def invoke(self, messages) -> Any:
        """
        Invoke the LLM with the given messages and tools.

        Args:
            messages: List of LangChain messages or message dicts

        Returns:
            Response object with content attribute
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = convert_messages_to_openai_format(messages)

            # Prepare the call to LiteLLM with tools
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
                "api_key": self.api_key
            }

            if self.base_url:
                kwargs["base_url"] = self.base_url

            # Add tools if available
            if self.tools:
                # Convert tools to OpenAI format
                openai_tools = []
                for tool in self.tools:
                    # Convert LangChain-style tool to OpenAI format
                    if hasattr(tool, 'name') and hasattr(tool, 'description'):
                        openai_tool = {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        }

                        # Add parameters if available
                        if hasattr(tool, 'args_schema') and tool.args_schema:
                            schema = tool.args_schema.schema()
                            if "properties" in schema:
                                openai_tool["function"]["parameters"]["properties"] = schema["properties"]
                            if "required" in schema:
                                openai_tool["function"]["parameters"]["required"] = schema["required"]

                        openai_tools.append(openai_tool)

                if openai_tools:
                    kwargs["tools"] = openai_tools

            # Make the async call to LiteLLM
            response = await acompletion(**kwargs)

            # Extract the content from the response
            content = response.choices[0].message.content

            # Return a mock response object that mimics LangChain's response
            return MockLangChainResponse(content)

        except Exception as e:
            logger.error(f"Error calling LiteLLM: {e}")
            # Return a mock response with error message
            return MockLangChainResponse(f"Error: {str(e)}")


class MockLangChainResponse:
    """
    Mock response object that mimics LangChain's response structure.
    """

    def __init__(self, content: str):
        self.content = content


def convert_messages_to_openai_format(messages):
    """
    Convert messages to OpenAI-compatible format.

    Args:
        messages: List of LangChain-style messages or message dicts

    Returns:
        List of message dicts in OpenAI format
    """
    openai_messages = []

    for msg in messages:
        if hasattr(msg, 'role') and hasattr(msg, 'content'):
            # LangChain message object
            role = msg.role.lower() if isinstance(msg.role, str) else str(msg.role).lower()
            if role == 'human':
                role = 'user'
            elif role == 'ai':
                role = 'assistant'
            elif role == 'system':
                role = 'system'

            openai_messages.append({
                "role": role,
                "content": msg.content
            })
        elif isinstance(msg, dict):
            # Already in dict format
            if 'role' in msg and 'content' in msg:
                role = msg['role'].lower()
                if role == 'human':
                    role = 'user'
                elif role == 'ai':
                    role = 'assistant'

                openai_messages.append({
                    "role": role,
                    "content": msg['content']
                })

    return openai_messages