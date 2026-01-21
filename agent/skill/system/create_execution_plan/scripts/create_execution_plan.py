#!/usr/bin/env python3
"""
Execution Plan Creation Skill Script

This script creates execution plans for film production projects using the plan service.
Supports both CLI execution and in-context execution via the SkillExecutor.
"""
import json
import sys
import argparse
from typing import Dict, Any, TYPE_CHECKING, Optional
import os

if TYPE_CHECKING:
    from agent.skill.skill_executor import SkillContext
    from agent.plan.service import PlanService


def execute(context: 'SkillContext', args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the create_execution_plan skill in context.

    This is the main entry point for in-context execution via SkillExecutor.

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

        # Import inside function to avoid sys.path manipulation
        from agent.plan.service import PlanService

        # Use the plan service from the context if available, otherwise create a new one
        plan_service = getattr(context, 'plan_service', None)
        if not plan_service:
            plan_service = PlanService()

        # Set the workspace if available in context
        if context and context.workspace:
            plan_service.set_workspace(context.workspace)

        # Create the plan in the context of the project if available
        project_name = None
        if context and context.project:
            project_name = getattr(context.project, 'project_name', None)

        # Create the plan
        plan = plan_service.create_plan(
            name=plan_name,
            description=description,
            tasks=tasks,
            project_name=project_name
        )

        if plan:
            return {
                "success": True,
                "message": f"Execution plan '{plan_name}' created successfully",
                "plan_id": plan.id,
                "plan_name": plan.name,
                "project_name": project_name
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create execution plan '{plan_name}'"
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating execution plan: {str(e)}"
        }


def create_execution_plan(plan_name: str, description: str = "", tasks: Optional[list] = None) -> Dict[str, Any]:
    """
    Create an execution plan using the plan service.

    Args:
        plan_name (str): Name of the execution plan
        description (str): Description of the plan
        tasks (list): Array of tasks for the plan

    Returns:
        dict: Result of the operation with success status and message
    """
    try:
        # Import inside function to avoid sys.path manipulation
        from agent.plan.service import PlanService

        # Initialize the plan service
        plan_service = PlanService()

        # Create the plan
        plan = plan_service.create_plan(
            name=plan_name,
            description=description,
            tasks=tasks or []
        )

        if plan:
            return {
                "success": True,
                "message": f"Execution plan '{plan_name}' created successfully",
                "plan_id": plan.id,
                "plan_name": plan.name
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create execution plan '{plan_name}'"
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


if __name__ == "__main__":
    main()