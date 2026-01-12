"""Production Agent - Main orchestrator agent for the Filmeto system.

This is the main entry point that manages:
- Question understanding
- Planning
- Coordination
- Sub-agent execution
- Response synthesis
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.graph.state import ProductionAgentState
from agent.nodes import (
    QuestionUnderstandingNode,
    PlannerNode,
    CoordinatorNode,
    ExecutorNode,
    ResponseNode,
    PlanRefinementNode,
    route_from_understanding,
    route_from_coordinator,
    route_after_tools,
    route_from_planner,
    route_from_sub_agent_executor,
    route_from_plan_review,
    route_from_refinement,
)
from agent.nodes.sub_agent_executor import (
    SubAgentExecutorNode,
    PlanReviewNode,
    ResultSynthesisNode
)
from agent.sub_agents.registry import SubAgentRegistry
from agent.tools import ToolRegistry
from agent.streaming import StreamEventEmitter
from agent.workflow_logger import workflow_logger
import logging

logger = logging.getLogger(__name__)


class ProductionAgent:
    """
    Production Agent - The main orchestrator for Filmeto.
    
    This agent acts as the "Producer" role in film production,
    coordinating all aspects of the project and managing sub-agents.
    
    Architecture:
    - This is a complete LangGraph instance (not a subgraph)
    - Manages question understanding, planning, coordination
    - Delegates to specialized sub-agents (Director, Screenwriter, etc.)
    - Each sub-agent is also a LangGraph Subgraph
    """
    
    def __init__(
        self,
        project_id: str,
        workspace: Any,
        project: Any,
        llm: ChatOpenAI,
        sub_agent_registry: SubAgentRegistry,
        tool_registry: ToolRegistry,
        stream_emitter: Optional[StreamEventEmitter] = None
    ):
        """
        Initialize Production Agent.
        
        Args:
            project_id: Project identifier for context isolation
            workspace: Workspace instance
            project: Project instance
            llm: Language model
            sub_agent_registry: Registry of sub-agents
            tool_registry: Registry of tools
            stream_emitter: Optional stream emitter for events
        """
        self.project_id = project_id
        self.workspace = workspace
        self.project = project
        self.llm = llm
        self.sub_agent_registry = sub_agent_registry
        self.tool_registry = tool_registry
        self.stream_emitter = stream_emitter
        
        # Memory for checkpointing
        self.memory = MemorySaver()
        
        # Build the main graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the main LangGraph workflow for Production Agent.
        
        Workflow:
        1. question_understanding: Analyze request, determine complexity
        2. coordinator: Handle simple tasks
        3. planner: Create execution plan for complex tasks
        4. execute_sub_agent_plan: Execute with sub-agents
        5. review_plan: Review results
        6. refine_plan: Refine if needed
        7. synthesize_results: Combine results
        8. respond: Generate final response
        """
        tools = self.tool_registry.get_all_tools()
        
        # Create nodes
        question_understanding = QuestionUnderstandingNode(
            self.llm, 
            self.sub_agent_registry
        )
        coordinator = CoordinatorNode(self.llm, tools)
        planner = PlannerNode(self.llm, self.sub_agent_registry)
        executor = ExecutorNode(self.llm, tools)
        responder = ResponseNode(self.llm)
        
        # Create sub-agent nodes
        sub_agent_executor = SubAgentExecutorNode(
            self.sub_agent_registry,
            self.tool_registry,
            workspace=self.workspace,
            project=self.project
        )
        plan_review = PlanReviewNode(self.llm)
        plan_refinement = PlanRefinementNode(self.llm, self.sub_agent_registry)
        result_synthesis = ResultSynthesisNode(self.llm)
        
        # Set stream emitter if available
        if self.stream_emitter:
            sub_agent_executor.set_stream_emitter(self.stream_emitter)
            plan_review.set_stream_emitter(self.stream_emitter)
            result_synthesis.set_stream_emitter(self.stream_emitter)
        
        # Create graph
        workflow = StateGraph(ProductionAgentState)
        
        # Add all nodes
        workflow.add_node("question_understanding", question_understanding)
        workflow.add_node("coordinator", coordinator)
        workflow.add_node("planner", planner)
        workflow.add_node("use_tools", executor)
        workflow.add_node("respond", responder)
        workflow.add_node("execute_sub_agent_plan", sub_agent_executor)
        workflow.add_node("review_plan", plan_review)
        workflow.add_node("refine_plan", plan_refinement)
        workflow.add_node("synthesize_results", result_synthesis)
        
        # Set entry point
        workflow.set_entry_point("question_understanding")
        
        # Add edges from question_understanding
        workflow.add_conditional_edges(
            "question_understanding",
            route_from_understanding,
            {
                "planner": "planner",
                "coordinator": "coordinator"
            }
        )
        
        # Add edges from coordinator
        workflow.add_conditional_edges(
            "coordinator",
            route_from_coordinator,
            {
                "use_tools": "use_tools",
                "respond": "respond",
                "end": END
            }
        )
        
        # Add edge from tools back to coordinator
        workflow.add_conditional_edges(
            "use_tools",
            route_after_tools,
            {
                "coordinator": "coordinator",
                "end": END
            }
        )
        
        # Add edges from planner
        workflow.add_conditional_edges(
            "planner",
            route_from_planner,
            {
                "execute_sub_agent_plan": "execute_sub_agent_plan",
                "coordinator": "coordinator"
            }
        )
        
        # Add edges from sub-agent executor
        workflow.add_conditional_edges(
            "execute_sub_agent_plan",
            route_from_sub_agent_executor,
            {
                "execute_sub_agent_plan": "execute_sub_agent_plan",
                "review_plan": "review_plan",
                "end": END
            }
        )
        
        # Add edges from plan review
        workflow.add_conditional_edges(
            "review_plan",
            route_from_plan_review,
            {
                "refine_plan": "refine_plan",
                "synthesize_results": "synthesize_results",
                "respond": "respond"
            }
        )
        
        # Add edges from plan refinement
        workflow.add_conditional_edges(
            "refine_plan",
            route_from_refinement,
            {
                "execute_sub_agent_plan": "execute_sub_agent_plan",
                "synthesize_results": "synthesize_results"
            }
        )
        
        # Add edge from synthesis to respond
        workflow.add_edge("synthesize_results", "respond")
        
        # Add edge from responder to end
        workflow.add_edge("respond", END)
        
        # Compile graph
        return workflow.compile(checkpointer=self.memory)
    
    async def execute(
        self,
        messages: List[BaseMessage],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the Production Agent workflow.
        
        Args:
            messages: Conversation messages
            config: Optional configuration (for thread_id, etc.)
            
        Returns:
            Final state after execution
        """
        logger.info("=" * 80)
        logger.info(f"[ProductionAgent] ENTRY: execute")
        logger.info(f"[ProductionAgent] Project ID: {self.project_id}")
        logger.info(f"[ProductionAgent] Message count: {len(messages)}")
        if messages:
            last_msg = str(messages[-1].content)[:100] if hasattr(messages[-1], 'content') else str(messages[-1])[:100]
            logger.info(f"[ProductionAgent] Last message: {last_msg}...")
        logger.info("=" * 80)
        
        # Create initial state
        flow_id = workflow_logger.log_flow_start(self.project_id)
        
        initial_state: ProductionAgentState = {
            "project_id": self.project_id,
            "messages": messages,
            "next_action": "question_understanding",
            "context": {
                "original_request": str(messages[-1].content) if messages else ""
            },
            "iteration_count": 0,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": False,
            "plan_refinement_count": 0,
            "flow_id": flow_id
        }
        
        logger.info(f"[ProductionAgent] Initial state created: next_action={initial_state['next_action']}")
        
        # Prepare config with additional context
        if config is None:
            config = {"configurable": {}}
        
        # Add project_id to configurable context instead of workspace and project objects
        if "configurable" not in config:
            config["configurable"] = {}
        
        config["configurable"]["project_id"] = self.project_id
        
        logger.info(f"[ProductionAgent] Starting graph execution...")
        # Execute graph
        final_state = await self.graph.ainvoke(initial_state, config=config)
        
        workflow_logger.log_flow_end(flow_id)
        
        logger.info("=" * 80)
        logger.info(f"[ProductionAgent] EXIT: execute")
        logger.info(f"[ProductionAgent] Final iteration_count: {final_state.get('iteration_count', 0)}")
        logger.info(f"[ProductionAgent] Final next_action: {final_state.get('next_action', 'unknown')}")
        logger.info(f"[ProductionAgent] Sub-agent results count: {len(final_state.get('sub_agent_results', {}))}")
        logger.info("=" * 80)
        
        return final_state
    
    async def stream(
        self,
        messages: List[BaseMessage],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Stream the Production Agent workflow execution.
        
        Args:
            messages: Conversation messages
            config: Optional configuration
            
        Yields:
            State updates as the workflow progresses
        """
        logger.info("=" * 80)
        logger.info(f"[ProductionAgent] ENTRY: stream")
        logger.info(f"[ProductionAgent] Project ID: {self.project_id}")
        logger.info(f"[ProductionAgent] Message count: {len(messages)}")
        if messages:
            last_msg = str(messages[-1].content)[:100] if hasattr(messages[-1], 'content') else str(messages[-1])[:100]
            logger.info(f"[ProductionAgent] Last message: {last_msg}...")
        logger.info("=" * 80)
        
        # Create initial state
        flow_id = workflow_logger.log_flow_start(self.project_id)
        
        initial_state: ProductionAgentState = {
            "project_id": self.project_id,
            "messages": messages,
            "next_action": "question_understanding",
            "context": {
                "original_request": str(messages[-1].content) if messages else ""
            },
            "iteration_count": 0,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": False,
            "plan_refinement_count": 0,
            "flow_id": flow_id
        }
        
        logger.info(f"[ProductionAgent] Initial state created: next_action={initial_state['next_action']}")
        
        # Prepare config with additional context
        if config is None:
            config = {"configurable": {}}
        
        # Add project_id to configurable context instead of workspace and project objects
        if "configurable" not in config:
            config["configurable"] = {}
        
        config["configurable"]["project_id"] = self.project_id
        
        logger.info(f"[ProductionAgent] Starting graph streaming...")
        event_count = 0
        # Stream graph execution
        async for event in self.graph.astream(initial_state, config=config):
            event_count += 1
            node_names = list(event.keys())
            logger.debug(f"[ProductionAgent] Stream event #{event_count}: nodes={node_names}")
            yield event
            
        workflow_logger.log_flow_end(flow_id)
        
        logger.info("=" * 80)
        logger.info(f"[ProductionAgent] EXIT: stream")
        logger.info(f"[ProductionAgent] Total events streamed: {event_count}")
        logger.info("=" * 80)
    
    def update_context(self, workspace: Any = None, project: Any = None):
        """
        Update workspace and project context.
        
        Args:
            workspace: New workspace instance
            project: New project instance
        """
        if workspace:
            self.workspace = workspace
        if project:
            self.project = project
        
        # Update tool registry
        self.tool_registry.update_context(workspace, project)
        
        # Rebuild graph with updated context
        self.graph = self._build_graph()
