"""
Test script for the Plan Service functionality
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.plan_service import create_execution_plan, execute_plan_synchronously, plan_service_manager
from agent.plan.models import PlanTask
from datetime import datetime


def test_create_plan():
    """Test creating a plan using the plan service"""
    print("Testing plan creation...")
    
    tasks = [
        {
            'id': 'task_1',
            'name': 'Research',
            'description': 'Research the problem',
            'title': 'researcher',
            'parameters': {'param1': 'value1'},
            'needs': []
        },
        {
            'id': 'task_2',
            'name': 'Analysis',
            'description': 'Analyze the findings',
            'title': 'analyst',
            'parameters': {'param2': 'value2'},
            'needs': ['task_1']
        },
        {
            'id': 'task_3',
            'name': 'Report',
            'description': 'Write a report',
            'title': 'writer',
            'parameters': {'param3': 'value3'},
            'needs': ['task_2']
        }
    ]
    
    plan_data = create_execution_plan(
        project_name='TestProject',
        plan_name='Test Plan',
        description='A test plan for verifying plan service functionality',
        tasks=tasks
    )
    
    print(f"Created plan with ID: {plan_data['id']}")
    print(f"Plan name: {plan_data['name']}")
    print(f"Number of tasks: {len(plan_data['tasks'])}")
    
    for task in plan_data['tasks']:
        print(f"  - Task: {task['name']} (ID: {task['id']}) - Needs: {task['needs']}")
    
    return plan_data


def test_execute_plan():
    """Test executing a plan using the plan service"""
    print("\nTesting plan execution...")
    
    tasks = [
        {
            'id': 'task_1',
            'name': 'Research',
            'description': 'Research the problem',
            'title': 'researcher',
            'parameters': {'param1': 'value1'},
            'needs': []
        },
        {
            'id': 'task_2',
            'name': 'Analysis',
            'description': 'Analyze the findings',
            'title': 'analyst',
            'parameters': {'param2': 'value2'},
            'needs': ['task_1']
        },
        {
            'id': 'task_3',
            'name': 'Report',
            'description': 'Write a report',
            'title': 'writer',
            'parameters': {'param3': 'value3'},
            'needs': ['task_2']
        }
    ]
    
    execution_result = execute_plan_synchronously(
        project_name='TestProject',
        plan_name='Test Execution Plan',
        description='A test plan for verifying plan execution functionality',
        tasks=tasks
    )
    
    print(f"Execution completed with status: {execution_result['status']}")
    print(f"Plan ID: {execution_result['plan_id']}")
    print(f"Instance ID: {execution_result['instance_id']}")
    
    for task in execution_result['tasks']:
        print(f"  - Task: {task['name']} - Status: {task['status']}")
    
    return execution_result


def test_plan_service_class():
    """Test using the PlanServiceManager class directly"""
    print("\nTesting PlanServiceManager class...")

    # Create tasks as dictionaries (as expected by the create_plan method)
    task_dicts = [
        {
            'id': 'direct_task_1',
            'name': 'Direct Task 1',
            'description': 'A task created directly through PlanServiceManager',
            'title': 'executor',
            'parameters': {'step': 1},
            'needs': []
        },
        {
            'id': 'direct_task_2',
            'name': 'Direct Task 2',
            'description': 'Another task created directly through PlanServiceManager',
            'title': 'executor',
            'parameters': {'step': 2},
            'needs': ['direct_task_1']
        }
    ]

    # Create a plan using the manager
    plan = plan_service_manager.create_plan(
        project_name='TestProject',
        plan_name='Direct Test Plan',
        description='A test plan created directly through PlanServiceManager',
        tasks=task_dicts
    )

    print(f"Created plan with ID: {plan.id}")
    print(f"Plan name: {plan.name}")
    print(f"Number of tasks: {len(plan.tasks)}")

    # Create an instance of the plan
    plan_instance = plan_service_manager.create_plan_instance(plan)
    print(f"Created plan instance with ID: {plan_instance.instance_id}")

    # Start execution
    started = plan_service_manager.start_plan_execution(plan_instance)
    print(f"Started plan execution: {started}")

    # Get ready tasks
    ready_tasks = plan_service_manager.get_next_ready_tasks(plan_instance)
    print(f"Ready tasks: {len(ready_tasks)}")

    return plan, plan_instance


if __name__ == "__main__":
    print("Running Plan Service tests...\n")
    
    # Test 1: Create a plan
    plan_data = test_create_plan()
    
    # Test 2: Execute a plan
    execution_result = test_execute_plan()
    
    # Test 3: Use PlanServiceManager directly
    plan, plan_instance = test_plan_service_class()
    
    print("\nAll tests completed successfully!")