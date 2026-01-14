#!/usr/bin/env python
"""Test to reproduce the exact issue where execution_plan is falsy in route_from_planner."""

from agent.graph.router import route_from_planner
from agent.graph.state import ProductionAgentState
from langchain_core.messages import HumanMessage


def test_falsy_execution_plan_issue():
    """Test the specific issue where execution_plan is falsy in route_from_planner."""
    print("Testing the specific issue: execution_plan is falsy in route_from_planner")
    
    # Case 1: execution_plan is None
    print("\nCase 1: execution_plan is None")
    state_none = {
        "execution_plan": None,
        "flow_id": "test_case_1"
    }
    
    result1 = route_from_planner(state_none)
    print(f"Input: execution_plan=None, Route result: {result1}")
    
    # Case 2: execution_plan is an empty dict
    print("\nCase 2: execution_plan is an empty dict")
    state_empty_dict = {
        "execution_plan": {},
        "flow_id": "test_case_2"
    }
    
    result2 = route_from_planner(state_empty_dict)
    print(f"Input: execution_plan={{}}, Route result: {result2}")
    
    # Case 3: execution_plan has empty tasks
    print("\nCase 3: execution_plan has empty tasks")
    state_empty_tasks = {
        "execution_plan": {
            "description": "Test plan",
            "phase": "pre_production",
            "tasks": [],  # Empty tasks list
            "success_criteria": "Complete tasks"
        },
        "flow_id": "test_case_3"
    }
    
    result3 = route_from_planner(state_empty_tasks)
    print(f"Input: execution_plan with empty tasks, Route result: {result3}")
    
    # Case 4: execution_plan is missing entirely from state
    print("\nCase 4: execution_plan key is missing from state")
    state_missing_key = {
        "flow_id": "test_case_4"
        # No execution_plan key
    }
    
    result4 = route_from_planner(state_missing_key)
    print(f"Input: execution_plan key missing, Route result: {result4}")
    
    # Case 5: Valid execution plan with tasks
    print("\nCase 5: Valid execution plan with tasks")
    state_valid = {
        "execution_plan": {
            "description": "Test plan",
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
            "success_criteria": "Complete tasks"
        },
        "flow_id": "test_case_5"
    }
    
    result5 = route_from_planner(state_valid)
    print(f"Input: execution_plan with tasks, Route result: {result5}")
    
    print("\n" + "="*60)
    print("Analysis:")
    print("- When execution_plan is None, empty dict, or missing: route to 'coordinator'")
    print("- When execution_plan has empty tasks: route to 'coordinator'") 
    print("- When execution_plan has tasks: route to 'execute_sub_agent_plan'")
    print("- This is the expected behavior of route_from_planner")
    
    # The real issue might be that PlannerNode is not setting execution_plan properly
    print("\nThe issue is likely that PlannerNode is not setting execution_plan in the state correctly")
    return True


def test_planner_node_state_update():
    """Test if PlannerNode properly updates the execution_plan in the state."""
    print("\n" + "="*60)
    print("Testing if PlannerNode properly updates execution_plan in state...")
    
    # Since we can't easily mock the LLM for this test, let's examine the logic directly
    print("The PlannerNode should always set execution_plan in its output state.")
    print("Looking at the current implementation...")
    
    # Simulate what happens in route_from_planner
    print("\nIn route_from_planner:")
    print("  execution_plan = state.get('execution_plan')")
    print("  if execution_plan:  # This checks if execution_plan is truthy")
    print("    tasks = execution_plan.get('tasks', [])")
    print("    if tasks and len(tasks) > 0:") 
    print("      route = 'execute_sub_agent_plan'")
    print("    else:")
    print("      route = 'coordinator'  # This happens when tasks is empty")
    print("  else:")
    print("    route = 'coordinator'  # This happens when execution_plan is falsy")
    
    print("\nThe issue occurs when:")
    print("1. PlannerNode fails to set execution_plan in output state")
    print("2. execution_plan is set to None or empty dict")
    print("3. execution_plan has empty tasks list")
    
    # The fix should ensure PlannerNode always sets a valid execution_plan
    print("\nOur previous fix added:")
    print('  if not execution_plan:')
    print('      execution_plan = {')
    print('          "tasks": [],')
    print('          "description": "Fallback plan due to parsing error",')
    print('          "phase": "unknown",')
    print('          "success_criteria": "Complete all tasks"')
    print('      }')
    
    print("\nThis ensures execution_plan is always truthy, but if tasks is empty,")
    print("it will still route to coordinator instead of execute_sub_agent_plan.")
    
    return True


if __name__ == "__main__":
    success1 = test_falsy_execution_plan_issue()
    success2 = test_planner_node_state_update()
    
    if success1 and success2:
        print("\n" + "="*60)
        print("Issue analysis completed!")
        print("\nThe real issue is not that execution_plan is not accessible,")
        print("but that when the planner cannot generate proper tasks, it creates")
        print("an execution plan with an empty tasks list, which causes the router")
        print("to route back to coordinator instead of to execute_sub_agent_plan.")
    else:
        print("\n" + "="*60)
        print("Test failed.")