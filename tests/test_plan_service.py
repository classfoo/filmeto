import unittest
import tempfile
import shutil
from pathlib import Path

from agent.plan.models import Plan, PlanInstance, PlanTask, PlanStatus, TaskStatus
from agent.plan.service import PlanService


class TestPlanService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_workspace = "workspace/agent/plan/flow"
        
        # Temporarily change the storage directory for testing
        PlanService._instance = None  # Reset singleton instance
        self.service = PlanService()
        self.service.flow_storage_dir = self.temp_dir / "agent" / "plan" / "flow"
        self.service.flow_storage_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)
        PlanService._instance = None  # Reset singleton instance
    
    def test_create_and_load_plan(self):
        """Test creating and loading a Plan."""
        project_name = "test_project"
        name = "Test Plan"
        description = "A test plan"

        tasks = [
            PlanTask(
                id="task1",
                name="Task 1",
                description="First task",
                title="researcher",
                needs=[]
            ),
            PlanTask(
                id="task2",
                name="Task 2",
                description="Second task",
                title="writer",
                needs=["task1"]
            )
        ]

        # Create a plan
        plan = self.service.create_plan(
            project_name=project_name,
            name=name,
            description=description,
            tasks=tasks
        )

        # Load the plan
        loaded_plan = self.service.load_plan(project_name, plan.id)

        self.assertIsNotNone(loaded_plan)
        self.assertEqual(loaded_plan.name, name)
        self.assertEqual(loaded_plan.description, description)
        self.assertEqual(len(loaded_plan.tasks), 2)
        self.assertEqual(loaded_plan.tasks[0].id, "task1")
        self.assertEqual(loaded_plan.tasks[1].id, "task2")
        self.assertEqual(loaded_plan.tasks[1].needs, ["task1"])
    
    def test_create_and_load_plan_instance(self):
        """Test creating and loading a PlanInstance."""
        project_name = "test_project"
        name = "Test Plan"
        description = "A test plan"

        tasks = [
            PlanTask(
                id="task1",
                name="Task 1",
                description="First task",
                title="researcher",
                needs=[]
            )
        ]

        # Create a plan
        plan = self.service.create_plan(
            project_name=project_name,
            name=name,
            description=description,
            tasks=tasks
        )

        # Create a plan instance
        plan_instance = self.service.create_plan_instance(plan)

        # Load the plan instance
        loaded_instance = self.service.load_plan_instance(
            project_name,
            plan.id,
            plan_instance.instance_id
        )

        self.assertIsNotNone(loaded_instance)
        self.assertEqual(loaded_instance.plan_id, plan.id)
        self.assertEqual(loaded_instance.project_name, project_name)
        self.assertEqual(len(loaded_instance.tasks), 1)
        self.assertEqual(loaded_instance.tasks[0].id, "task1")
        self.assertEqual(loaded_instance.tasks[0].status, TaskStatus.CREATED)
    
    def test_start_plan_execution(self):
        """Test starting plan execution."""
        project_name = "test_project"
        name = "Test Plan"
        description = "A test plan"

        tasks = [
            PlanTask(
                id="task1",
                name="Task 1",
                description="First task",
                title="researcher",
                needs=[]
            ),
            PlanTask(
                id="task2",
                name="Task 2",
                description="Second task",
                title="writer",
                needs=["task1"]
            )
        ]

        # Create a plan
        plan = self.service.create_plan(
            project_name=project_name,
            name=name,
            description=description,
            tasks=tasks
        )

        # Create a plan instance
        plan_instance = self.service.create_plan_instance(plan)

        # Start execution
        success = self.service.start_plan_execution(plan_instance)

        self.assertTrue(success)
        self.assertEqual(plan_instance.status, PlanStatus.RUNNING)

        # Task1 should be READY since it has no dependencies
        task1 = next(t for t in plan_instance.tasks if t.id == "task1")
        self.assertEqual(task1.status, TaskStatus.READY)

        # Task2 should still be CREATED since it depends on task1
        task2 = next(t for t in plan_instance.tasks if t.id == "task2")
        self.assertEqual(task2.status, TaskStatus.CREATED)
    
    def test_mark_task_completed_with_dependencies(self):
        """Test marking a task as completed and checking dependency handling."""
        project_name = "test_project"
        name = "Test Plan"
        description = "A test plan"

        tasks = [
            PlanTask(
                id="task1",
                name="Task 1",
                description="First task",
                title="researcher",
                needs=[]
            ),
            PlanTask(
                id="task2",
                name="Task 2",
                description="Second task",
                title="writer",
                needs=["task1"]
            )
        ]

        # Create a plan
        plan = self.service.create_plan(
            project_name=project_name,
            name=name,
            description=description,
            tasks=tasks
        )

        # Create a plan instance and start execution
        plan_instance = self.service.create_plan_instance(plan)
        self.service.start_plan_execution(plan_instance)

        # Mark task1 as completed
        success = self.service.mark_task_completed(plan_instance, "task1")

        self.assertTrue(success)

        # Task1 should be COMPLETED
        task1 = next(t for t in plan_instance.tasks if t.id == "task1")
        self.assertEqual(task1.status, TaskStatus.COMPLETED)

        # Task2 should now be READY since its dependency is satisfied
        task2 = next(t for t in plan_instance.tasks if t.id == "task2")
        self.assertEqual(task2.status, TaskStatus.READY)
    
    def test_cancel_plan(self):
        """Test cancelling an entire plan."""
        project_name = "test_project"
        name = "Test Plan"
        description = "A test plan"

        tasks = [
            PlanTask(
                id="task1",
                name="Task 1",
                description="First task",
                title="researcher",
                needs=[]
            ),
            PlanTask(
                id="task2",
                name="Task 2",
                description="Second task",
                title="writer",
                needs=[]
            )
        ]

        # Create a plan
        plan = self.service.create_plan(
            project_name=project_name,
            name=name,
            description=description,
            tasks=tasks
        )

        # Create a plan instance and start execution
        plan_instance = self.service.create_plan_instance(plan)
        self.service.start_plan_execution(plan_instance)

        # Mark task1 as running
        self.service.mark_task_running(plan_instance, "task1")

        # Cancel the entire plan
        success = self.service.cancel_plan(plan_instance)

        self.assertTrue(success)
        self.assertEqual(plan_instance.status, PlanStatus.CANCELLED)

        # Both tasks should be cancelled
        task1 = next(t for t in plan_instance.tasks if t.id == "task1")
        self.assertEqual(task1.status, TaskStatus.CANCELLED)

        task2 = next(t for t in plan_instance.tasks if t.id == "task2")
        self.assertEqual(task2.status, TaskStatus.CANCELLED)
    
    def test_cancel_single_task(self):
        """Test cancelling a single task."""
        project_name = "test_project"
        name = "Test Plan"
        description = "A test plan"

        tasks = [
            PlanTask(
                id="task1",
                name="Task 1",
                description="First task",
                title="researcher",
                needs=[]
            )
        ]

        # Create a plan
        plan = self.service.create_plan(
            project_name=project_name,
            name=name,
            description=description,
            tasks=tasks
        )

        # Create a plan instance
        plan_instance = self.service.create_plan_instance(plan)

        # Cancel the task
        success = self.service.cancel_task(plan_instance, "task1")

        self.assertTrue(success)

        # The task should be cancelled
        task1 = next(t for t in plan_instance.tasks if t.id == "task1")
        self.assertEqual(task1.status, TaskStatus.CANCELLED)


if __name__ == '__main__':
    unittest.main()