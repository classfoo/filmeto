from ..base_tool import BaseTool
from typing import Any, Dict
from ...plan.service import PlanService
from ...plan.models import PlanTask, Plan
from datetime import datetime
import uuid


class CreatePlanTool(BaseTool):
    """
    Tool to create a plan execution for a project.
    """

    def __init__(self):
        super().__init__(
            name="create_plan",
            description="Create a plan execution for the current project"
        )

    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the plan creation using PlanService.

        Args:
            parameters: Parameters for the plan including title, description, tasks
            context: Context containing project/workspace info

        Returns:
            Created plan details
        """
        # Extract required parameters
        title = parameters.get('title', 'Untitled Plan')
        description = parameters.get('description', 'No description provided')
        raw_tasks = parameters.get('tasks', [])

        # Extract project information from context
        project_info = context.get('project', {}) if context else {}
        workspace = context.get('workspace', '') if context else ''

        project_name = project_info.get('name', 'Unknown Project')

        # Initialize PlanService
        plan_service = PlanService()

        # Set workspace if provided
        if workspace:
            # Assuming workspace object has a workspace_path attribute
            # If not, we'll use the string directly
            if hasattr(workspace, 'workspace_path'):
                plan_service.set_workspace(workspace)
            else:
                # Create a mock workspace object if needed
                class MockWorkspace:
                    def __init__(self, path):
                        self.workspace_path = path
                mock_workspace = MockWorkspace(workspace)
                plan_service.set_workspace(mock_workspace)

        # Convert raw tasks to PlanTask objects
        plan_tasks = []
        for idx, raw_task in enumerate(raw_tasks):
            if isinstance(raw_task, dict):
                task_id = raw_task.get('id', f'task_{idx}_{int(datetime.now().timestamp())}')
                task_name = raw_task.get('name', raw_task.get('title', f'Task {idx+1}'))
                task_description = raw_task.get('description', raw_task.get('desc', 'No description'))
                task_title = raw_task.get('title', raw_task.get('role', 'other'))
                task_params = raw_task.get('parameters', raw_task.get('params', {}))
                task_needs = raw_task.get('needs', raw_task.get('dependencies', []))

                plan_task = PlanTask(
                    id=task_id,
                    name=task_name,
                    description=task_description,
                    title=task_title,
                    parameters=task_params,
                    needs=task_needs
                )
                plan_tasks.append(plan_task)
            else:
                # Handle case where raw_task is not a dict
                task_id = f'task_{idx}_{int(datetime.now().timestamp())}'
                plan_task = PlanTask(
                    id=task_id,
                    name=f'Task {idx+1}',
                    description=str(raw_task) if raw_task else 'No description',
                    title='other',
                    parameters={}
                )
                plan_tasks.append(plan_task)

        # Create the plan using PlanService
        plan = plan_service.create_plan(
            project_name=project_name,
            name=title,
            description=description,
            tasks=plan_tasks
        )

        # Return the created plan details
        return {
            'id': plan.id,
            'title': plan.name,
            'description': plan.description,
            'tasks': [self._convert_task_to_dict(task) for task in plan.tasks],
            'created_at': plan.created_at.isoformat(),
            'project': plan.project_name,
            'status': plan.status.value
        }

    def _convert_task_to_dict(self, task: PlanTask) -> Dict[str, Any]:
        """Convert a PlanTask object to a dictionary."""
        return {
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'title': task.title,
            'parameters': task.parameters,
            'needs': task.needs,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error_message': task.error_message
        }