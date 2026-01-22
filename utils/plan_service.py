"""
Plan Service Module

This module provides a centralized service for creating and managing execution plans
using the PlanService from the agent/plan package.
"""

from typing import Dict, List, Any, Optional
from agent.plan.service import PlanService
from agent.plan.models import Plan, PlanTask, PlanInstance, PlanStatus, TaskStatus
from datetime import datetime


class PlanServiceManager:
    """
    A wrapper class that provides a simplified interface to the PlanService
    for creating and managing execution plans.
    """
    
    def __init__(self):
        self._plan_service = PlanService()
    
    def set_workspace(self, workspace: Any) -> None:
        """
        Set the workspace for the plan service.
        
        Args:
            workspace: Workspace object with workspace_path attribute
        """
        self._plan_service.set_workspace(workspace)
    
    def create_plan(
        self,
        project_name: str,
        plan_name: str,
        description: str,
        tasks: List[Dict[str, Any]]
    ) -> Plan:
        """
        Create a new execution plan.
        
        Args:
            project_name: Name of the project
            plan_name: Name of the plan
            description: Description of the plan
            tasks: List of task dictionaries with id, name, description, title, parameters, and needs
            
        Returns:
            Created Plan object
        """
        # Convert task dictionaries to PlanTask objects
        plan_tasks = []
        for task_data in tasks:
            task = PlanTask(
                id=task_data.get('id', f'task_{int(datetime.now().timestamp())}'),
                name=task_data.get('name', ''),
                description=task_data.get('description', ''),
                title=task_data.get('title', 'other'),
                parameters=task_data.get('parameters', {}),
                needs=task_data.get('needs', [])
            )
            plan_tasks.append(task)
        
        # Create the plan using PlanService
        plan = self._plan_service.create_plan(
            project_name=project_name,
            name=plan_name,
            description=description,
            tasks=plan_tasks
        )
        
        return plan
    
    def create_plan_instance(self, plan: Plan) -> PlanInstance:
        """
        Create a new instance of a plan for execution.
        
        Args:
            plan: Plan object to instantiate
            
        Returns:
            Created PlanInstance object
        """
        return self._plan_service.create_plan_instance(plan)
    
    def start_plan_execution(self, plan_instance: PlanInstance) -> bool:
        """
        Start the execution of a plan instance.
        
        Args:
            plan_instance: PlanInstance to start execution for
            
        Returns:
            True if execution started successfully, False otherwise
        """
        return self._plan_service.start_plan_execution(plan_instance)
    
    def get_next_ready_tasks(self, plan_instance: PlanInstance) -> List[PlanTask]:
        """
        Get the next tasks that are ready to be executed based on dependencies.
        
        Args:
            plan_instance: PlanInstance to get ready tasks for
            
        Returns:
            List of ready PlanTask objects
        """
        return self._plan_service.get_next_ready_tasks(plan_instance)
    
    def mark_task_running(self, plan_instance: PlanInstance, task_id: str) -> bool:
        """
        Mark a task as running.
        
        Args:
            plan_instance: PlanInstance containing the task
            task_id: ID of the task to mark as running
            
        Returns:
            True if successful, False otherwise
        """
        return self._plan_service.mark_task_running(plan_instance, task_id)
    
    def mark_task_completed(self, plan_instance: PlanInstance, task_id: str) -> bool:
        """
        Mark a task as completed.
        
        Args:
            plan_instance: PlanInstance containing the task
            task_id: ID of the task to mark as completed
            
        Returns:
            True if successful, False otherwise
        """
        return self._plan_service.mark_task_completed(plan_instance, task_id)
    
    def mark_task_failed(self, plan_instance: PlanInstance, task_id: str, error_message: str) -> bool:
        """
        Mark a task as failed.
        
        Args:
            plan_instance: PlanInstance containing the task
            task_id: ID of the task to mark as failed
            error_message: Error message to associate with the failure
            
        Returns:
            True if successful, False otherwise
        """
        return self._plan_service.mark_task_failed(plan_instance, task_id, error_message)
    
    def cancel_plan(self, plan_instance: PlanInstance) -> bool:
        """
        Cancel an entire plan instance.
        
        Args:
            plan_instance: PlanInstance to cancel
            
        Returns:
            True if successful, False otherwise
        """
        return self._plan_service.cancel_plan(plan_instance)
    
    def load_plan(self, project_name: str, plan_id: str) -> Optional[Plan]:
        """
        Load a plan from storage.
        
        Args:
            project_name: Name of the project
            plan_id: ID of the plan to load
            
        Returns:
            Loaded Plan object or None if not found
        """
        return self._plan_service.load_plan(project_name, plan_id)
    
    def load_plan_instance(self, project_name: str, plan_id: str, instance_id: str) -> Optional[PlanInstance]:
        """
        Load a plan instance from storage.
        
        Args:
            project_name: Name of the project
            plan_id: ID of the plan
            instance_id: ID of the plan instance to load
            
        Returns:
            Loaded PlanInstance object or None if not found
        """
        return self._plan_service.load_plan_instance(project_name, plan_id, instance_id)
    
    def get_all_plans_for_project(self, project_name: str) -> List[Plan]:
        """
        Get all plans for a specific project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            List of Plan objects
        """
        return self._plan_service.get_all_plans_for_project(project_name)
    
    def get_all_instances_for_plan(self, project_name: str, plan_id: str) -> List[PlanInstance]:
        """
        Get all instances for a specific plan.
        
        Args:
            project_name: Name of the project
            plan_id: ID of the plan
            
        Returns:
            List of PlanInstance objects
        """
        return self._plan_service.get_all_instances_for_plan(project_name, plan_id)


# Global instance of PlanServiceManager
plan_service_manager = PlanServiceManager()


def create_execution_plan(
    project_name: str,
    plan_name: str,
    description: str,
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convenience function to create an execution plan.
    
    Args:
        project_name: Name of the project
        plan_name: Name of the plan
        description: Description of the plan
        tasks: List of task dictionaries
        
    Returns:
        Dictionary representation of the created plan
    """
    plan = plan_service_manager.create_plan(
        project_name=project_name,
        plan_name=plan_name,
        description=description,
        tasks=tasks
    )
    
    return {
        'id': plan.id,
        'project_name': plan.project_name,
        'name': plan.name,
        'description': plan.description,
        'tasks': [
            {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'title': task.title,
                'parameters': task.parameters,
                'needs': task.needs,
                'status': task.status.value
            } for task in plan.tasks
        ],
        'created_at': plan.created_at.isoformat(),
        'status': plan.status.value,
        'metadata': plan.metadata
    }


def execute_plan_synchronously(
    project_name: str,
    plan_name: str,
    description: str,
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute a plan synchronously from creation to completion.

    Args:
        project_name: Name of the project
        plan_name: Name of the plan
        description: Description of the plan
        tasks: List of task dictionaries

    Returns:
        Dictionary with execution results
    """
    # Create the plan
    plan = plan_service_manager.create_plan(
        project_name=project_name,
        plan_name=plan_name,
        description=description,
        tasks=tasks
    )

    # Create a plan instance for execution
    plan_instance = plan_service_manager.create_plan_instance(plan)

    # Start the plan execution
    plan_service_manager.start_plan_execution(plan_instance)

    # Execute tasks in order respecting dependencies
    max_iterations = 100  # Prevent infinite loops
    iteration_count = 0

    while (plan_instance.status != PlanStatus.COMPLETED and
           plan_instance.status != PlanStatus.FAILED and
           plan_instance.status != PlanStatus.CANCELLED and
           iteration_count < max_iterations):

        ready_tasks = plan_service_manager.get_next_ready_tasks(plan_instance)

        if not ready_tasks:
            # If no tasks are ready but plan isn't complete, check if we're stuck
            incomplete_tasks = [
                task for task in plan_instance.tasks
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]
            if incomplete_tasks:
                # Plan might be stuck due to unmet dependencies or other issues
                # In a real implementation, you might want to handle this differently
                break
            else:
                # All tasks are completed
                break

        iteration_count += 1

        # Execute each ready task
        for task in ready_tasks:
            # Mark task as running
            plan_service_manager.mark_task_running(plan_instance, task.id)

            # Simulate task execution (in a real implementation, this would call the actual task)
            # For now, we'll just mark it as completed
            plan_service_manager.mark_task_completed(plan_instance, task.id)

    return {
        'plan_id': plan.id,
        'instance_id': plan_instance.instance_id,
        'status': plan_instance.status.value,
        'tasks': [
            {
                'id': task.id,
                'name': task.name,
                'status': task.status.value,
                'error_message': task.error_message
            } for task in plan_instance.tasks
        ]
    }