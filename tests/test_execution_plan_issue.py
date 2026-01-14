#!/usr/bin/env python
"""Unit test to reproduce the execution plan issue between PlannerNode and route_from_planner."""

import asyncio
from unittest.mock import Mock, MagicMock
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from agent.nodes.planner import PlannerNode
from agent.graph.router import route_from_planner
from agent.graph.state import ProductionAgentState
from agent.sub_agents.registry import SubAgentRegistry


def test_execution_plan_passing():
    """Test that execution plan is properly passed from PlannerNode to route_from_planner."""
    print("Testing execution plan passing from PlannerNode to route_from_planner...")
    
    # Create mock LLM
    mock_llm = Mock(spec=ChatOpenAI)
    mock_response = Mock()
    mock_response.content = '''{
        "description": "Test execution plan",
        "phase": "pre_production",
        "tasks": [
            {
                "task_id": 1,
                "agent_name": "Screenwriter",
                "skill_name": "script_outline",
                "parameters": {"topic": "test", "genre": "comedy"},
                "dependencies": [],
                "expected_output": "Script outline"
            }
        ],
        "success_criteria": "Complete script outline"
    }'''
    mock_llm.invoke.return_value = mock_response
    
    # Create mock sub-agent registry
    mock_sub_agent_registry = Mock(spec=SubAgentRegistry)
    mock_sub_agent_registry.get_agent_capabilities.return_value = {
        "Screenwriter": [{"name": "script_outline", "description": "Create script outline"}]
    }
    
    # Create initial state
    initial_state: ProductionAgentState = {
        "project_id": "test_project",
        "messages": [HumanMessage(content="Create a comedy script")],
        "next_action": "planner",  # This should trigger the planner
        "context": {
            "original_request": "Create a comedy script",
            "question_analysis": {
                "requires_sub_agents": True,
                "complexity": "moderate",
                "suggested_agents": ["Screenwriter"],
                "task_type": "pre_production",
                "reasoning": "Requires creative writing skills"
            }
        },
        "iteration_count": 0,
        "execution_plan": None,  # Initially None
        "current_task_index": 0,
        "sub_agent_results": {},
        "requires_multi_agent": True,
        "plan_refinement_count": 0,
        "flow_id": "test_flow_123"
    }
    
    print(f"Initial state execution_plan: {initial_state['execution_plan']}")
    
    # Create PlannerNode
    planner_node = PlannerNode(mock_llm, mock_sub_agent_registry)
    
    # Execute the planner node
    print("Executing PlannerNode...")
    try:
        planner_output_state = planner_node(initial_state)
        print("PlannerNode executed successfully")
        print(f"Planner output state execution_plan: {planner_output_state.get('execution_plan')}")
        
        if planner_output_state.get('execution_plan'):
            print(f"Execution plan tasks count: {len(planner_output_state['execution_plan'].get('tasks', []))}")
        else:
            print("ERROR: Execution plan is None or falsy after PlannerNode!")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception in PlannerNode: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Now test the router with the planner's output state
    print("\nTesting route_from_planner with planner's output state...")
    try:
        route_result = route_from_planner(planner_output_state)
        print(f"Route result: {route_result}")
        
        # Check if execution_plan is accessible in the router
        execution_plan_in_router = planner_output_state.get('execution_plan')
        print(f"Execution plan in state passed to router: {execution_plan_in_router}")
        
        if execution_plan_in_router:
            tasks = execution_plan_in_router.get('tasks', [])
            print(f"Tasks in execution plan: {len(tasks)}")
            if tasks:
                for i, task in enumerate(tasks):
                    print(f"  Task {i+1}: {task.get('agent_name')}/{task.get('skill_name')}")
        else:
            print("ERROR: Execution plan is not accessible in the state passed to router!")
            return False
            
        print("\nSUCCESS: Execution plan is properly accessible in route_from_planner")
        return True
        
    except Exception as e:
        print(f"ERROR: Exception in route_from_planner: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_execution_plan():
    """Test what happens when execution plan has no tasks."""
    print("\n" + "="*60)
    print("Testing execution plan with no tasks...")
    
    # Create a state with an execution plan that has no tasks
    state_with_empty_plan = {
        "project_id": "test_project",
        "messages": [HumanMessage(content="Simple query")],
        "next_action": "execute_sub_agent_plan",
        "context": {"original_request": "Simple query"},
        "iteration_count": 1,
        "execution_plan": {
            "description": "Empty plan",
            "phase": "unknown",
            "tasks": [],  # Empty tasks list
            "success_criteria": "Complete all tasks"
        },
        "current_task_index": 0,
        "sub_agent_results": {},
        "requires_multi_agent": False,
        "plan_refinement_count": 0,
        "flow_id": "test_flow_456"
    }
    
    print(f"Execution plan in state: {state_with_empty_plan['execution_plan']}")
    print(f"Tasks in plan: {state_with_empty_plan['execution_plan']['tasks']}")
    
    try:
        route_result = route_from_planner(state_with_empty_plan)
        print(f"Route result for empty plan: {route_result}")
        
        if route_result == "coordinator":
            print("As expected, empty plan routes to coordinator")
        else:
            print(f"Unexpected route: {route_result}")
            
        return True
    except Exception as e:
        print(f"ERROR in empty plan test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = test_execution_plan_passing()
    success2 = test_empty_execution_plan()
    
    if success1 and success2:
        print("\n" + "="*60)
        print("All tests completed successfully!")
    else:
        print("\n" + "="*60)
        print("Some tests failed!")