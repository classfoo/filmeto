#!/usr/bin/env python
"""Comprehensive test to simulate the actual LangGraph execution and identify the execution plan issue."""

import asyncio
from unittest.mock import Mock, MagicMock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.graph.state import ProductionAgentState
from agent.nodes.question_understanding import QuestionUnderstandingNode
from agent.nodes.planner import PlannerNode
from agent.nodes.coordinator import CoordinatorNode
from agent.graph.router import route_from_understanding, route_from_planner
from agent.sub_agents.registry import SubAgentRegistry
from agent.tools import ToolRegistry


def create_test_graph():
    """Create a simplified graph to test the planner -> router flow."""
    
    # Create mock components
    mock_llm = Mock(spec=ChatOpenAI)
    mock_response = Mock()
    # Return a JSON response that should create a valid execution plan
    mock_response.content = '''{
        "requires_sub_agents": true,
        "complexity": "moderate", 
        "suggested_agents": ["Screenwriter"],
        "task_type": "pre_production",
        "reasoning": "Requires creative writing skills"
    }'''
    mock_llm.invoke.return_value = mock_response
    
    # For the planner, return a valid plan
    def mock_planner_invoke(prompt):
        response = Mock()
        response.content = '''{
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
        return response
    
    mock_llm.invoke = Mock(side_effect=lambda prompt: 
                          mock_planner_invoke(prompt) if 
                          any('film production planner' in str(msg) if hasattr(msg, 'content') else 'film production planner' in str(msg) 
                              for msg in (getattr(prompt, 'messages', []) if hasattr(prompt, 'messages') else [])) 
                          else mock_response)
    
    mock_sub_agent_registry = Mock(spec=SubAgentRegistry)
    mock_sub_agent_registry.get_agent_capabilities.return_value = {
        "Screenwriter": [{"name": "script_outline", "description": "Create script outline"}],
        "Director": [{"name": "storyboard", "description": "Create storyboard"}]
    }
    
    # Create nodes
    question_understanding = QuestionUnderstandingNode(mock_llm, mock_sub_agent_registry)
    planner = PlannerNode(mock_llm, mock_sub_agent_registry)
    
    # Create coordinator node too to complete the flow
    mock_tools = []  # Empty tools for mock
    coordinator = CoordinatorNode(mock_llm, mock_tools)
    
    # Create graph
    workflow = StateGraph(ProductionAgentState)
    
    # Add nodes
    workflow.add_node("question_understanding", question_understanding)
    workflow.add_node("planner", planner)
    workflow.add_node("coordinator", coordinator)
    
    # Set entry point
    workflow.set_entry_point("question_understanding")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "question_understanding",
        route_from_understanding,
        {
            "planner": "planner",
            "coordinator": "coordinator"
        }
    )
    
    workflow.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "execute_sub_agent_plan": "coordinator",  # Simplified - routing to coordinator for this test
            "coordinator": "coordinator"
        }
    )
    
    workflow.add_edge("coordinator", END)
    
    # Compile graph
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def test_full_graph_execution():
    """Test the full graph execution to see if execution plan persists."""
    print("Testing full graph execution to check execution plan persistence...")
    
    try:
        graph = create_test_graph()
        
        # Create initial state
        initial_state = {
            "project_id": "test_project",
            "messages": [HumanMessage(content="Create a comedy script")],
            "next_action": "question_understanding",
            "context": {"original_request": "Create a comedy script"},
            "iteration_count": 0,
            "execution_plan": None,
            "current_task_index": 0,
            "sub_agent_results": {},
            "requires_multi_agent": False,
            "plan_refinement_count": 0,
            "flow_id": "test_flow_789"
        }
        
        print(f"Initial state execution_plan: {initial_state['execution_plan']}")
        
        # Execute the graph
        config = {"configurable": {"thread_id": "test_thread_1"}}
        print("Starting graph execution...")
        
        final_state = graph.invoke(initial_state, config=config)
        
        print(f"Final state execution_plan: {final_state.get('execution_plan')}")
        
        if final_state.get('execution_plan'):
            tasks = final_state['execution_plan'].get('tasks', [])
            print(f"Final state has {len(tasks)} tasks in execution plan")
            for i, task in enumerate(tasks):
                print(f"  Task {i+1}: {task.get('agent_name')}/{task.get('skill_name')}")
        else:
            print("ERROR: Execution plan is None or missing in final state!")
            return False
            
        print("\nGraph execution completed successfully")
        return True
        
    except Exception as e:
        print(f"ERROR in graph execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_debug_state_transitions():
    """Debug state transitions to see where execution plan might be lost."""
    print("\n" + "="*60)
    print("Debugging state transitions...")
    
    # Create the same mock components as above
    mock_llm = Mock(spec=ChatOpenAI)
    mock_response = Mock()
    mock_response.content = '''{
        "requires_sub_agents": true,
        "complexity": "moderate", 
        "suggested_agents": ["Screenwriter"],
        "task_type": "pre_production",
        "reasoning": "Requires creative writing skills"
    }'''
    mock_llm.invoke.return_value = mock_response
    
    def mock_planner_invoke(prompt):
        response = Mock()
        response.content = '''{
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
        return response
    
    mock_llm.invoke = Mock(side_effect=lambda prompt: 
                          mock_planner_invoke(prompt) if 
                          any('film production planner' in str(msg) if hasattr(msg, 'content') else 'film production' in str(msg) 
                              for msg in (getattr(prompt, 'messages', []) if hasattr(prompt, 'messages') else [])) 
                          else mock_response)
    
    mock_sub_agent_registry = Mock(spec=SubAgentRegistry)
    mock_sub_agent_registry.get_agent_capabilities.return_value = {
        "Screenwriter": [{"name": "script_outline", "description": "Create script outline"}]
    }
    
    # Test question understanding node
    print("Testing QuestionUnderstandingNode...")
    question_understanding = QuestionUnderstandingNode(mock_llm, mock_sub_agent_registry)
    
    initial_state = {
        "project_id": "test_project",
        "messages": [HumanMessage(content="Create a comedy script")],
        "next_action": "question_understanding",
        "context": {"original_request": "Create a comedy script"},
        "iteration_count": 0,
        "execution_plan": None,
        "current_task_index": 0,
        "sub_agent_results": {},
        "requires_multi_agent": False,
        "plan_refinement_count": 0,
        "flow_id": "debug_flow_1"
    }
    
    print(f"Before question understanding - execution_plan: {initial_state['execution_plan']}")
    question_result = question_understanding(initial_state)
    print(f"After question understanding - next_action: {question_result['next_action']}")
    print(f"After question understanding - execution_plan: {question_result.get('execution_plan')}")
    
    # Test planner node
    print("\nTesting PlannerNode...")
    planner = PlannerNode(mock_llm, mock_sub_agent_registry)
    
    # Use the result from question understanding as input to planner
    planner_input_state = question_result
    print(f"Before planner - execution_plan: {planner_input_state.get('execution_plan')}")
    planner_result = planner(planner_input_state)
    print(f"After planner - execution_plan: {planner_result.get('execution_plan')}")
    
    if planner_result.get('execution_plan'):
        tasks = planner_result['execution_plan'].get('tasks', [])
        print(f"Planner created {len(tasks)} tasks")
    else:
        print("ERROR: Planner did not create execution plan!")
        return False
    
    # Test router
    print("\nTesting route_from_planner...")
    route_result = route_from_planner(planner_result)
    print(f"Route result: {route_result}")
    
    # Double-check the execution_plan in the state passed to router
    execution_plan_in_router = planner_result.get('execution_plan')
    print(f"Execution plan in state passed to router: {execution_plan_in_router is not None}")
    
    if execution_plan_in_router:
        tasks = execution_plan_in_router.get('tasks', [])
        print(f"Tasks in plan passed to router: {len(tasks)}")
    else:
        print("ERROR: Execution plan is not accessible in router!")
        return False
    
    print("\nState transition debugging completed successfully")
    return True


if __name__ == "__main__":
    success1 = test_full_graph_execution()
    success2 = test_debug_state_transitions()
    
    if success1 and success2:
        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("The execution plan appears to be properly maintained through the workflow.")
    else:
        print("\n" + "="*60)
        print("Some tests failed - there may be an issue with execution plan persistence.")