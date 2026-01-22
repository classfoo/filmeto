#!/usr/bin/env python3
"""
Execution Plan Creation Skill Script

This script creates execution plans for film production projects using the create_plan tool.
Supports both CLI execution and in-context execution via the SkillExecutor.
"""
import json
import sys
import argparse
from typing import Dict, Any, TYPE_CHECKING
import os

if TYPE_CHECKING:
    from agent.skill.skill_executor import SkillContext


def execute(context: 'SkillContext', args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the create_execution_plan skill in context.

    This is the main entry point for in-context execution via SkillExecutor.
    It calls the 'create_plan' tool using the execute_tool function.

    Args:
        context: SkillContext object containing workspace and project
        args: Dictionary of arguments for the skill

    Returns:
        dict: Result of the operation with success status and message
    """
    try:
        # Extract arguments
        plan_name = args.get('plan_name')
        description = args.get('description', '')
        tasks = args.get('tasks', [])

        if not plan_name:
            return {
                "success": False,
                "message": "plan_name is required"
            }

        # Call the 'create_plan' tool using execute_tool
        # The parameters for the tool are passed in the parameters dict
        tool_params = {
            'title': plan_name,
            'description': description,
            'tasks': tasks
        }

        # Use execute_tool to call the create_plan tool
        result = execute_tool("create_plan", tool_params)

        # Process the result from the tool
        if result and isinstance(result, dict):
            if 'id' in result:  # If the tool returned a plan ID, it was successful
                return {
                    "success": True,
                    "message": f"Execution plan '{plan_name}' created successfully",
                    "plan_id": result['id'],
                    "plan_name": result.get('title', plan_name),
                    "project": result.get('project', 'Unknown Project')
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to create execution plan '{plan_name}': {result.get('message', 'Unknown error')}"
                }
        else:
            return {
                "success": False,
                "message": f"Failed to create execution plan '{plan_name}': Unexpected result format"
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating execution plan: {str(e)}"
        }


def create_execution_plan(plan_name: str, description: str = "", tasks: list = None) -> Dict[str, Any]:
    """
    Create an execution plan using the create_plan tool.

    Args:
        plan_name (str): Name of the execution plan
        description (str): Description of the plan
        tasks (list): Array of tasks for the plan

    Returns:
        dict: Result of the operation with success status and message
    """
    try:
        # Call the 'create_plan' tool using execute_tool
        # The parameters for the tool are passed in the parameters dict
        tool_params = {
            'title': plan_name,
            'description': description,
            'tasks': tasks or []
        }

        # Use execute_tool to call the create_plan tool
        result = execute_tool("create_plan", tool_params)

        # Process the result from the tool
        if result and isinstance(result, dict):
            if 'id' in result:  # If the tool returned a plan ID, it was successful
                return {
                    "success": True,
                    "message": f"Execution plan '{plan_name}' created successfully",
                    "plan_id": result['id'],
                    "plan_name": result.get('title', plan_name)
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to create execution plan '{plan_name}': {result.get('message', 'Unknown error')}"
                }
        else:
            return {
                "success": False,
                "message": f"Failed to create execution plan '{plan_name}': Unexpected result format"
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating execution plan: {str(e)}"
        }


def main():
    """CLI entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Create an execution plan for film production projects"
    )
    parser.add_argument(
        "plan_name", type=str,
        help="Name of the execution plan"
    )
    parser.add_argument(
        "--description", type=str, default="",
        help="Description of the plan"
    )
    parser.add_argument(
        "--tasks", type=str, default="[]",
        help="JSON string of tasks for the plan"
    )
    parser.add_argument(
        "--project-path", type=str, required=True,
        help="Path to the project directory"
    )

    args = parser.parse_args()

    try:
        # Parse tasks JSON
        tasks = json.loads(args.tasks)

        # Create the execution plan
        result = create_execution_plan(args.plan_name, args.description, tasks)

        print(json.dumps(result, indent=2))

    except json.JSONDecodeError:
        error_result = {
            "success": False,
            "error": "invalid_json",
            "message": f"Invalid JSON for tasks: {args.tasks}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "message": f"Error in execution plan creation: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


# Alias for SkillExecutor compatibility
execute_in_context = execute


if __name__ == "__main__":
    main()