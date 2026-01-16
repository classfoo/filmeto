import os
import json
import yaml
import tempfile
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
from datetime import datetime
import shutil

from .models import Plan, PlanInstance, PlanTask, PlanStatus, TaskStatus


class PlanService:
    """
    Singleton service for managing Plans and PlanInstances.

    This service handles the creation, storage, retrieval, and execution of plans.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PlanService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.flow_storage_dir = Path("workspace/agent/plan/flow")
            self.flow_storage_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True

    def _get_ready_tasks(self, plan_instance: PlanInstance) -> List[PlanTask]:
        """
        Get tasks that are ready to run based on their dependencies.

        A task is ready if:
        1. Its status is CREATED
        2. All its dependencies (in the 'needs' list) are COMPLETED
        """
        ready_tasks = []

        for task in plan_instance.tasks:
            if task.status != TaskStatus.CREATED:
                continue

            # Check if all dependencies are completed
            all_deps_satisfied = True
            for dep_task_id in task.needs:
                dep_task = next((t for t in plan_instance.tasks if t.id == dep_task_id), None)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    all_deps_satisfied = False
                    break

            if all_deps_satisfied:
                ready_tasks.append(task)

        return ready_tasks

    def _update_task_status(self, plan_instance: PlanInstance, task_id: str,
                           new_status: TaskStatus, error_message: Optional[str] = None) -> bool:
        """
        Update the status of a specific task in a plan instance.
        """
        task = next((t for t in plan_instance.tasks if t.id == task_id), None)
        if not task:
            return False

        task.status = new_status
        if new_status == TaskStatus.RUNNING and task.started_at is None:
            task.started_at = datetime.now()
        elif new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()

        if error_message:
            task.error_message = error_message

        # Save the updated instance
        self._save_plan_instance(plan_instance)
        return True

    def _update_plan_status(self, plan_instance: PlanInstance, new_status: PlanStatus) -> bool:
        """
        Update the status of a plan instance.
        """
        plan_instance.status = new_status
        if new_status == PlanStatus.RUNNING and plan_instance.started_at is None:
            plan_instance.started_at = datetime.now()
        elif new_status in [PlanStatus.COMPLETED, PlanStatus.FAILED, PlanStatus.CANCELLED]:
            plan_instance.completed_at = datetime.now()

        # Save the updated instance
        self._save_plan_instance(plan_instance)
        return True
    
    def _get_flow_dir(self, project_id: str, plan_id: str) -> Path:
        """Get the directory path for a specific plan."""
        return self.flow_storage_dir / f"{project_id}_{plan_id}"

    def _save_plan(self, plan: Plan) -> None:
        """Save a Plan to disk atomically."""
        plan_dir = self._get_flow_dir(plan.project_id, plan.id)
        plan_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data for serialization
        plan_data = asdict(plan)
        plan_data['created_at'] = plan_data['created_at'].isoformat()
        plan_data['status'] = plan_data['status'].value  # Convert enum to string
        plan_data['tasks'] = []

        for task in plan.tasks:
            task_dict = asdict(task)
            task_dict['created_at'] = task.created_at.isoformat()
            task_dict['started_at'] = task.started_at.isoformat() if task.started_at else None
            task_dict['completed_at'] = task.completed_at.isoformat() if task.completed_at else None
            task_dict['status'] = task.status.value  # Convert enum to string
            plan_data['tasks'].append(task_dict)

        # Write to temporary file first
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            dir=plan_dir,
            suffix='.tmp'
        )

        try:
            yaml.dump(plan_data, temp_file, default_flow_style=False, allow_unicode=True)
            temp_file.close()

            # Atomically move the temporary file to the target location
            target_path = plan_dir / "plan.yml"
            shutil.move(temp_file.name, target_path)
        except Exception:
            # Clean up the temporary file if something went wrong
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
            raise

    def _save_plan_instance(self, plan_instance: PlanInstance) -> None:
        """Save a PlanInstance to disk atomically."""
        plan_dir = self._get_flow_dir(plan_instance.project_id, plan_instance.plan_id)
        plan_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data for serialization
        instance_data = asdict(plan_instance)
        instance_data['created_at'] = instance_data['created_at'].isoformat()
        instance_data['started_at'] = instance_data['started_at'].isoformat() if instance_data['started_at'] else None
        instance_data['completed_at'] = instance_data['completed_at'].isoformat() if instance_data['completed_at'] else None
        instance_data['status'] = instance_data['status'].value  # Convert enum to string

        instance_data['tasks'] = []
        for task in plan_instance.tasks:
            task_dict = asdict(task)
            task_dict['created_at'] = task.created_at.isoformat()
            task_dict['started_at'] = task.started_at.isoformat() if task.started_at else None
            task_dict['completed_at'] = task.completed_at.isoformat() if task.completed_at else None
            task_dict['status'] = task.status.value  # Convert enum to string
            instance_data['tasks'].append(task_dict)

        # Write to temporary file first
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            dir=plan_dir,
            suffix='.tmp'
        )

        try:
            yaml.dump(instance_data, temp_file, default_flow_style=False, allow_unicode=True)
            temp_file.close()

            # Atomically move the temporary file to the target location
            target_path = plan_dir / "plan_instance.yml"
            shutil.move(temp_file.name, target_path)
        except Exception:
            # Clean up the temporary file if something went wrong
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
            raise

    def start_plan_execution(self, plan_instance: PlanInstance) -> bool:
        """
        Start the execution of a plan instance.

        This sets the plan status to RUNNING and marks eligible tasks as READY.
        """
        if plan_instance.status != PlanStatus.CREATED:
            return False  # Can only start execution of a CREATED plan

        # Update plan status to RUNNING
        self._update_plan_status(plan_instance, PlanStatus.RUNNING)

        # Mark initial ready tasks (those with no dependencies)
        for task in plan_instance.tasks:
            if task.status == TaskStatus.CREATED and len(task.needs) == 0:
                self._update_task_status(plan_instance, task.id, TaskStatus.READY)

        return True

    def get_next_ready_tasks(self, plan_instance: PlanInstance) -> List[PlanTask]:
        """
        Get the next tasks that are ready to be executed based on dependencies.
        """
        return self._get_ready_tasks(plan_instance)

    def mark_task_running(self, plan_instance: PlanInstance, task_id: str) -> bool:
        """
        Mark a task as running.
        """
        return self._update_task_status(plan_instance, task_id, TaskStatus.RUNNING)

    def mark_task_completed(self, plan_instance: PlanInstance, task_id: str) -> bool:
        """
        Mark a task as completed and update dependent tasks to READY if their
        dependencies are satisfied.
        """
        success = self._update_task_status(plan_instance, task_id, TaskStatus.COMPLETED)
        if not success:
            return False

        # Check if there are any tasks that become ready due to this completion
        for task in plan_instance.tasks:
            if task.status == TaskStatus.CREATED:
                # Check if all dependencies are now satisfied
                all_deps_satisfied = True
                for dep_task_id in task.needs:
                    dep_task = next((t for t in plan_instance.tasks if t.id == dep_task_id), None)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        all_deps_satisfied = False
                        break

                if all_deps_satisfied:
                    self._update_task_status(plan_instance, task.id, TaskStatus.READY)

        # Check if the entire plan is completed
        incomplete_tasks = [t for t in plan_instance.tasks
                           if t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]]

        if not incomplete_tasks:
            self._update_plan_status(plan_instance, PlanStatus.COMPLETED)

        return True

    def mark_task_failed(self, plan_instance: PlanInstance, task_id: str, error_message: str) -> bool:
        """
        Mark a task as failed.
        """
        success = self._update_task_status(plan_instance, task_id, TaskStatus.FAILED, error_message)
        if success:
            # Mark the entire plan as failed
            self._update_plan_status(plan_instance, PlanStatus.FAILED)
        return success

    def cancel_plan(self, plan_instance: PlanInstance) -> bool:
        """
        Cancel an entire plan instance.

        This marks the plan as CANCELLED and all non-completed tasks as CANCELLED too.
        """
        # Update all non-completed tasks to cancelled
        for task in plan_instance.tasks:
            if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]:
                self._update_task_status(plan_instance, task.id, TaskStatus.CANCELLED)

        # Update the plan status to cancelled
        return self._update_plan_status(plan_instance, PlanStatus.CANCELLED)

    def cancel_task(self, plan_instance: PlanInstance, task_id: str) -> bool:
        """
        Cancel a specific task in a plan instance.
        """
        return self._update_task_status(plan_instance, task_id, TaskStatus.CANCELLED)
    
    def create_plan(self, project_id: str, name: str, description: str,
                        tasks: List[PlanTask], metadata: Optional[Dict] = None) -> Plan:
        """Create a new Plan."""
        plan_id = f"p_{int(datetime.now().timestamp())}_{len(tasks)}"
        plan = Plan(
            id=plan_id,
            project_id=project_id,
            name=name,
            description=description,
            tasks=tasks,
            metadata=metadata or {}
        )

        self._save_plan(plan)
        return plan

    def create_plan_instance(self, plan: Plan) -> PlanInstance:
        """Create a new PlanInstance from a Plan."""
        instance_id = f"pi_{int(datetime.now().timestamp())}"

        # Copy tasks from the plan to the instance
        instance_tasks = []
        for task in plan.tasks:
            instance_task = PlanTask(
                id=task.id,
                name=task.name,
                description=task.description,
                agent_role=task.agent_role,
                parameters=task.parameters.copy(),
                needs=task.needs.copy(),
                status=TaskStatus.CREATED
            )
            instance_tasks.append(instance_task)

        plan_instance = PlanInstance(
            plan_id=plan.id,
            instance_id=instance_id,
            project_id=plan.project_id,
            tasks=instance_tasks,
            metadata=plan.metadata.copy()
        )

        self._save_plan_instance(plan_instance)
        return plan_instance

    def load_plan(self, project_id: str, plan_id: str) -> Optional[Plan]:
        """Load a Plan from disk."""
        plan_dir = self._get_flow_dir(project_id, plan_id)
        plan_path = plan_dir / "plan.yml"

        if not plan_path.exists():
            return None

        with open(plan_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Convert timestamps back to datetime objects
        created_at = datetime.fromisoformat(data['created_at'])

        # Reconstruct tasks
        tasks = []
        for task_data in data.get('tasks', []):
            task = PlanTask(
                id=task_data['id'],
                name=task_data['name'],
                description=task_data['description'],
                agent_role=task_data['agent_role'],
                parameters=task_data.get('parameters', {}),
                needs=task_data.get('needs', []),
                status=TaskStatus(task_data.get('status', 'created')),  # Convert string back to enum
                created_at=datetime.fromisoformat(task_data['created_at']),
                started_at=datetime.fromisoformat(task_data['started_at']) if task_data.get('started_at') else None,
                completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data.get('completed_at') else None,
                error_message=task_data.get('error_message')
            )
            tasks.append(task)

        plan = Plan(
            id=data['id'],
            project_id=data['project_id'],
            name=data['name'],
            description=data['description'],
            tasks=tasks,
            created_at=created_at,
            status=PlanStatus(data.get('status', 'created')),  # Convert string back to enum
            metadata=data.get('metadata', {})
        )

        return plan

    def update_plan(
        self,
        project_id: str,
        plan_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tasks: Optional[List[PlanTask]] = None,
        append_tasks: Optional[List[PlanTask]] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[Plan]:
        """
        Update an existing Plan definition.
        """
        plan = self.load_plan(project_id, plan_id)
        if not plan:
            return None

        if name is not None:
            plan.name = name
        if description is not None:
            plan.description = description
        if metadata:
            plan.metadata.update(metadata)

        if tasks is not None:
            plan.tasks = tasks
        if append_tasks:
            plan.tasks.extend(append_tasks)

        self._save_plan(plan)
        return plan

    def load_plan_instance(self, project_id: str, plan_id: str, instance_id: str) -> Optional[PlanInstance]:
        """Load a PlanInstance from disk."""
        plan_dir = self._get_flow_dir(project_id, plan_id)
        plan_instance_path = plan_dir / "plan_instance.yml"

        if not plan_instance_path.exists():
            return None

        with open(plan_instance_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Convert timestamps back to datetime objects
        created_at = datetime.fromisoformat(data['created_at'])
        started_at = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        completed_at = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None

        # Reconstruct tasks
        tasks = []
        for task_data in data.get('tasks', []):
            task = PlanTask(
                id=task_data['id'],
                name=task_data['name'],
                description=task_data['description'],
                agent_role=task_data['agent_role'],
                parameters=task_data.get('parameters', {}),
                needs=task_data.get('needs', []),
                status=TaskStatus(task_data.get('status', 'created')),  # Convert string back to enum
                created_at=datetime.fromisoformat(task_data['created_at']),
                started_at=datetime.fromisoformat(task_data['started_at']) if task_data.get('started_at') else None,
                completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data.get('completed_at') else None,
                error_message=task_data.get('error_message')
            )
            tasks.append(task)

        plan_instance = PlanInstance(
            plan_id=data['plan_id'],
            instance_id=data['instance_id'],
            project_id=data['project_id'],
            tasks=tasks,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            status=PlanStatus(data.get('status', 'created')),  # Convert string back to enum
            metadata=data.get('metadata', {})
        )

        return plan_instance
    
    def get_all_plans_for_project(self, project_id: str) -> List[Plan]:
        """Get all Plans for a specific project."""
        project_dirs = [d for d in self.flow_storage_dir.iterdir()
                       if d.is_dir() and d.name.startswith(f"{project_id}_")]

        plans = []
        for plan_dir in project_dirs:
            plan_id = plan_dir.name.split('_', 1)[1]  # Extract plan ID after project_id_
            plan = self.load_plan(project_id, plan_id)
            if plan:
                plans.append(plan)

        return plans

    def get_all_instances_for_plan(self, project_id: str, plan_id: str) -> List[PlanInstance]:
        """Get all PlanInstances for a specific plan."""
        plan_dir = self._get_flow_dir(project_id, plan_id)
        plan_instance_path = plan_dir / "plan_instance.yml"

        instances = []
        if plan_instance_path.exists():
            instance = self.load_plan_instance(project_id, plan_id, "unknown")  # We'll get the actual instance_id from the loaded data
            if instance:
                instances.append(instance)

        return instances