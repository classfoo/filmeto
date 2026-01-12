import logging
import json
from typing import Any, Dict, Optional
import uuid
from datetime import datetime

class WorkflowLogger:
    """
    Logger for tracking the detailed execution flow of FilmetoAgent.
    Tracks logic processing links for nodes, roles, and sub-agents.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WorkflowLogger, cls).__new__(cls)
            cls._instance.logger = logging.getLogger("FilmetoWorkflow")
            cls._instance.logger.setLevel(logging.INFO)
            # Ensure handler exists if not configured externally
            if not cls._instance.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                cls._instance.logger.addHandler(handler)
        return cls._instance

    def log_flow_start(self, project_id: str, flow_id: Optional[str] = None) -> str:
        """Log the start of a new workflow execution."""
        if not flow_id:
            flow_id = str(uuid.uuid4())
        
        self.logger.info(f"🚀 [FLOW_START] Project: {project_id} | Flow ID: {flow_id}")
        return flow_id

    def log_flow_end(self, flow_id: str, status: str = "completed"):
        """Log the end of a workflow execution."""
        self.logger.info(f"🏁 [FLOW_END] Flow ID: {flow_id} | Status: {status}")

    def log_node_entry(self, flow_id: str, node_name: str, input_state: Dict[str, Any]):
        """Log entry into a graph node."""
        state_summary = self._summarize_state(input_state)
        self.logger.info(f"➡️ [NODE_ENTRY] Flow ID: {flow_id} | Node: {node_name} | State: {state_summary}")

    def log_node_exit(self, flow_id: str, node_name: str, output_state: Dict[str, Any], next_action: Optional[str] = None):
        """Log exit from a graph node."""
        state_summary = self._summarize_state(output_state)
        next_action_str = f" | Next: {next_action}" if next_action else ""
        self.logger.info(f"⬅️ [NODE_EXIT] Flow ID: {flow_id} | Node: {node_name} | State: {state_summary}{next_action_str}")

    def log_logic_step(self, flow_id: str, component: str, step: str, details: Any = None):
        """Log a specific logic step or decision within a component."""
        details_str = f" | Details: {self._format_details(details)}" if details else ""
        self.logger.info(f"⚙️ [LOGIC] Flow ID: {flow_id} | Component: {component} | Step: {step}{details_str}")

    def log_sub_agent_start(self, flow_id: str, sub_agent_name: str, task: str):
        """Log the start of a sub-agent execution."""
        self.logger.info(f"🤖 [SUB_AGENT_START] Flow ID: {flow_id} | Agent: {sub_agent_name} | Task: {task[:100]}...")

    def log_sub_agent_end(self, flow_id: str, sub_agent_name: str, result: Any):
        """Log the end of a sub-agent execution."""
        result_summary = self._format_details(result)
        self.logger.info(f"✅ [SUB_AGENT_END] Flow ID: {flow_id} | Agent: {sub_agent_name} | Result: {result_summary}")

    def log_role_action(self, flow_id: str, role: str, action: str, description: str):
        """Log a specific role-based action."""
        self.logger.info(f"🎭 [ROLE_ACTION] Flow ID: {flow_id} | Role: {role} | Action: {action} | Desc: {description}")

    def log_router_decision(self, flow_id: str, source: str, destination: str, reason: str = ""):
        """Log a routing decision."""
        reason_str = f" | Reason: {reason}" if reason else ""
        self.logger.info(f"🔀 [ROUTER] Flow ID: {flow_id} | {source} -> {destination}{reason_str}")

    def _summarize_state(self, state: Dict[str, Any]) -> str:
        """Create a brief summary of the state."""
        if not state:
            return "Empty"
        
        summary = []
        if "iteration_count" in state:
            summary.append(f"Iter: {state['iteration_count']}")
        if "next_action" in state:
            summary.append(f"Next: {state['next_action']}")
        if "messages" in state:
            summary.append(f"Msgs: {len(state['messages'])}")
        
        return ", ".join(summary)

    def _format_details(self, details: Any) -> str:
        """Format details for logging, truncating if necessary."""
        if details is None:
            return "None"
        try:
            details_str = str(details)
            if len(details_str) > 200:
                return details_str[:200] + "..."
            return details_str
        except Exception:
            return "Unprintable"

workflow_logger = WorkflowLogger()
