"""Planner Node for multi-agent collaboration."""

from typing import Any, Dict
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import json
import re
import logging

from agent.graph.state import AgentState
from agent.workflow_logger import workflow_logger

logger = logging.getLogger(__name__)


class PlannerNode:
    """
    Planner node that creates execution plans based on sub-agent skills.
    
    The planner:
    - Creates execution plans using sub-agent skills
    - Breaks down complex tasks into sub-agent tasks
    - Determines task dependencies and sequencing
    """
    
    def __init__(self, llm: ChatOpenAI, sub_agent_registry: Any):
        """Initialize planner node."""
        self.llm = llm
        self.sub_agent_registry = sub_agent_registry
        
        # Get agent capabilities
        capabilities = sub_agent_registry.get_agent_capabilities()
        capabilities_str = self._format_capabilities(capabilities)
        
        # Create planner prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a film production planner for Filmeto, an AI-powered video creation platform.

Your role is to create detailed execution plans using sub-agent skills to complete complex film production requests.

Available sub-agents and their skills:
{capabilities_str}

Film Production Workflow Guidelines:
1. Pre-Production Phase:
   - Screenwriter: script_outline → script_detail → dialogue_writing
   - Director: storyboard → scene_composition → shot_planning
   - MakeupArtist: costume_design → character_makeup → appearance_styling
   - Production: project_planning → resource_allocation

2. Production Phase:
   - Director: scene_direction
   - Actor: character_portrayal → performance_execution
   - Supervisor: continuity_tracking → shot_logging

3. Post-Production Phase:
   - Editor: video_editing → scene_assembly → pacing_control → final_assembly
   - SoundMixer: sound_design → audio_mixing → audio_quality_control
   - Supervisor: script_supervision

For each user request, create an execution plan with:
1. Sequence of tasks, each assigned to an appropriate sub-agent
2. Each task specifies: agent_name, skill_name, parameters
3. Dependencies between tasks (task_id references)
4. Expected outcomes

You MUST respond with valid JSON format:
{{{{
    "description": "Overall plan description",
    "phase": "pre_production" | "production" | "post_production" | "full_production",
    "tasks": [
        {{{{
            "task_id": 1,
            "agent_name": "Screenwriter",
            "skill_name": "script_outline",
            "parameters": {{{{"topic": "...", "genre": "..."}}}},
            "dependencies": [],
            "expected_output": "Script outline with story structure"
        }}}},
        {{{{
            "task_id": 2,
            "agent_name": "Director",
            "skill_name": "storyboard",
            "parameters": {{{{"script": "from_task_1"}}}},
            "dependencies": [1],
            "expected_output": "Visual storyboard"
        }}}}
    ],
    "success_criteria": "What determines successful completion"
}}}}

Create a detailed execution plan for the user's request, ensuring proper task sequencing and dependencies."""),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def _format_capabilities(self, capabilities: Dict[str, list]) -> str:
        """Format agent capabilities for prompt."""
        lines = []
        for agent_name, skills in capabilities.items():
            lines.append(f"\n{agent_name}:")
            for skill in skills:
                lines.append(f"  - {skill['name']}: {skill['description']}")
        return "\n".join(lines)
    
    def __call__(self, state: AgentState) -> AgentState:
        """Create an execution plan for the user's request."""
        flow_id = state.get("flow_id", "unknown")
        workflow_logger.log_node_entry(flow_id, "PlannerNode", state)
        
        logger.info("=" * 80)
        logger.info(f"[PlannerNode] ENTRY")
        logger.info(f"[PlannerNode] Iteration: {state.get('iteration_count', 0)}")
        
        messages = state["messages"]
        context = state.get("context", {})
        
        # Get question analysis if available
        analysis = context.get("question_analysis", {})
        suggested_agents = analysis.get("suggested_agents", [])
        logger.info(f"[PlannerNode] Suggested agents: {suggested_agents}")
        logger.info(f"[PlannerNode] Task type: {analysis.get('task_type', 'unknown')}")
        
        # Add analysis context to messages for planner
        analysis_context = f"[Context] Suggested agents: {suggested_agents}, Task type: {analysis.get('task_type', 'unknown')}"
        augmented_messages = list(messages) + [SystemMessage(content=analysis_context)]
        
        # Format prompt
        formatted_prompt = self.prompt.format_messages(messages=augmented_messages)
        
        logger.info("[PlannerNode] Invoking LLM to create execution plan...")
        workflow_logger.log_logic_step(flow_id, "PlannerNode", "plan_generation", f"Generating plan for {analysis.get('task_type', 'unknown')}")
        
        # Get plan from LLM
        response = self.llm.invoke(formatted_prompt)
        logger.debug(f"[PlannerNode] LLM response received: {response.content[:200]}...")
        
        # Parse plan (try to extract JSON from response)
        plan_content = response.content
        execution_plan = None
        
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', plan_content)
            if json_match:
                execution_plan = json.loads(json_match.group())
            else:
                execution_plan = json.loads(plan_content)
            logger.info("[PlannerNode] Successfully parsed execution plan JSON")
        except (json.JSONDecodeError, AttributeError) as e:
            # Fallback: create a simple plan structure
            logger.warning(f"[PlannerNode] JSON parsing failed: {e}, using fallback plan structure")
            workflow_logger.log_logic_step(flow_id, "PlannerNode", "plan_parsing_error", str(e))
            execution_plan = {
                "tasks": [],
                "description": plan_content,
                "phase": "unknown",
                "success_criteria": "Complete all tasks"
            }
        
        # Validate and structure the plan
        if "tasks" not in execution_plan:
            execution_plan["tasks"] = []

        # Ensure execution_plan is never None/Falsy
        if not execution_plan:
            execution_plan = {
                "tasks": [],
                "description": "Fallback plan due to parsing error",
                "phase": "unknown",
                "success_criteria": "Complete all tasks"
            }

        # Store plan in context
        context["plan_description"] = execution_plan.get("description", plan_content)
        context["plan_phase"] = execution_plan.get("phase", "unknown")

        task_count = len(execution_plan.get("tasks", []))
        logger.info(f"[PlannerNode] Execution plan created:")
        logger.info(f"  - Phase: {execution_plan.get('phase', 'unknown')}")
        logger.info(f"  - Task count: {task_count}")
        logger.info(f"  - Description: {execution_plan.get('description', 'N/A')[:100]}...")

        workflow_logger.log_logic_step(flow_id, "PlannerNode", "plan_created", {
            "phase": execution_plan.get("phase"),
            "task_count": task_count,
            "tasks": [f"{t.get('task_id')}: {t.get('agent_name')}/{t.get('skill_name')}" for t in execution_plan.get("tasks", [])]
        })

        # Log task details
        for i, task in enumerate(execution_plan.get("tasks", [])[:5]):  # Log first 5 tasks
            logger.info(f"  Task {i+1}: {task.get('agent_name', 'unknown')}/{task.get('skill_name', 'unknown')} (deps: {task.get('dependencies', [])})")
        if task_count > 5:
            logger.info(f"  ... and {task_count - 5} more tasks")

        # Create plan message
        plan_msg = f"[Execution Plan] Created plan with {task_count} tasks for phase: {execution_plan.get('phase', 'unknown')}\n"
        plan_msg += f"Description: {execution_plan.get('description', 'N/A')[:200]}..."

        logger.info(f"[PlannerNode] Routing to: execute_sub_agent_plan")
        logger.info("[PlannerNode] EXIT")
        logger.info("=" * 80)

        output_state = {
            "messages": [AIMessage(content=plan_msg)],
            "next_action": "execute_sub_agent_plan",
            "context": context,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "execution_plan": execution_plan,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": True,
            "plan_refinement_count": state.get("plan_refinement_count", 0),
            "flow_id": flow_id
        }
        workflow_logger.log_node_exit(flow_id, "PlannerNode", output_state, next_action="execute_sub_agent_plan")
        return output_state

