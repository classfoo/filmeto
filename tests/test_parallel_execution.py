"""Tests for parallel task execution with dependency management.

This test suite covers:
- DependencyGraph in SubAgentExecutorNode
- Parallel task execution
- Task dependency handling
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any

from agent.nodes.sub_agent_executor import (
    SubAgentExecutorNode,
    PlanReviewNode,
    ResultSynthesisNode,
    DependencyGraph,
)
from agent.skills.base import SkillResult, SkillStatus


class TestDependencyGraphInExecutor:
    """Tests for DependencyGraph used in SubAgentExecutorNode."""
    
    def test_simple_linear_dependencies(self):
        """Test linear task dependencies."""
        graph = DependencyGraph()
        
        graph.add_task("1", {"name": "Task 1"}, [])
        graph.add_task("2", {"name": "Task 2"}, ["1"])
        graph.add_task("3", {"name": "Task 3"}, ["2"])
        
        # Initially only task 1 is ready
        assert graph.get_ready_tasks() == ["1"]
        
        # After completing 1, task 2 is ready
        graph.mark_complete("1")
        assert graph.get_ready_tasks() == ["2"]
        
        # After completing 2, task 3 is ready
        graph.mark_complete("2")
        assert graph.get_ready_tasks() == ["3"]
        
        # After completing 3, no more tasks
        graph.mark_complete("3")
        assert graph.get_ready_tasks() == []
        assert graph.is_complete()
    
    def test_parallel_tasks_no_dependencies(self):
        """Test tasks without dependencies can run in parallel."""
        graph = DependencyGraph()
        
        graph.add_task("1", {"name": "Task 1"}, [])
        graph.add_task("2", {"name": "Task 2"}, [])
        graph.add_task("3", {"name": "Task 3"}, [])
        
        # All tasks are ready immediately
        ready = graph.get_ready_tasks()
        assert set(ready) == {"1", "2", "3"}
    
    def test_diamond_dependency(self):
        """Test diamond-shaped dependencies."""
        graph = DependencyGraph()
        
        # Diamond: 1 -> [2, 3] -> 4
        graph.add_task("1", {"name": "Task 1"}, [])
        graph.add_task("2", {"name": "Task 2"}, ["1"])
        graph.add_task("3", {"name": "Task 3"}, ["1"])
        graph.add_task("4", {"name": "Task 4"}, ["2", "3"])
        
        # First level
        assert graph.get_ready_tasks() == ["1"]
        graph.mark_complete("1")
        
        # Second level (parallel)
        assert set(graph.get_ready_tasks()) == {"2", "3"}
        graph.mark_complete("2")
        
        # Task 4 not ready yet (waiting for 3)
        assert graph.get_ready_tasks() == ["3"]
        graph.mark_complete("3")
        
        # Now task 4 is ready
        assert graph.get_ready_tasks() == ["4"]
    
    def test_failed_task_handling(self):
        """Test handling of failed tasks."""
        graph = DependencyGraph()
        
        graph.add_task("1", {"name": "Task 1"}, [])
        graph.add_task("2", {"name": "Task 2"}, ["1"])
        graph.add_task("3", {"name": "Task 3"}, ["1"])
        
        graph.mark_complete("1")
        graph.mark_failed("2")
        graph.mark_complete("3")
        
        status = graph.get_completion_status()
        assert status["completed"] == 2
        assert status["failed"] == 1
        assert status["is_complete"] is True
    
    def test_running_status(self):
        """Test tracking of running tasks."""
        graph = DependencyGraph()
        
        graph.add_task("1", {"name": "Task 1"}, [])
        graph.add_task("2", {"name": "Task 2"}, [])
        
        assert graph.get_completion_status()["running"] == 0
        
        graph.mark_running("1")
        status = graph.get_completion_status()
        assert status["running"] == 1
        
        # Running task should not appear in ready tasks
        ready = graph.get_ready_tasks()
        assert "1" not in ready
        assert "2" in ready
        
        graph.mark_complete("1")
        assert graph.get_completion_status()["running"] == 0
    
    def test_complex_plan(self):
        """Test with a realistic film production plan."""
        graph = DependencyGraph()
        
        plan = {
            "tasks": [
                {"task_id": 1, "agent_name": "Screenwriter", "skill_name": "script_outline", "dependencies": []},
                {"task_id": 2, "agent_name": "Screenwriter", "skill_name": "script_detail", "dependencies": [1]},
                {"task_id": 3, "agent_name": "Director", "skill_name": "storyboard", "dependencies": [1]},
                {"task_id": 4, "agent_name": "MakeupArtist", "skill_name": "costume_design", "dependencies": [1]},
                {"task_id": 5, "agent_name": "Director", "skill_name": "scene_direction", "dependencies": [2, 3]},
                {"task_id": 6, "agent_name": "Actor", "skill_name": "performance_execution", "dependencies": [4, 5]},
                {"task_id": 7, "agent_name": "Editor", "skill_name": "video_editing", "dependencies": [6]},
            ]
        }
        
        graph.add_tasks_from_plan(plan)
        
        groups = graph.get_parallel_groups()
        
        # Group 1: Task 1 (script outline)
        assert groups[0] == ["1"]
        
        # Group 2: Tasks 2, 3, 4 (all depend only on 1)
        assert set(groups[1]) == {"2", "3", "4"}
        
        # Group 3: Task 5 (depends on 2 and 3)
        assert groups[2] == ["5"]
        
        # Group 4: Task 6 (depends on 4 and 5)
        assert groups[3] == ["6"]
        
        # Group 5: Task 7 (depends on 6)
        assert groups[4] == ["7"]


class TestSubAgentExecutorNode:
    """Tests for SubAgentExecutorNode."""
    
    @pytest.fixture
    def mock_registry(self):
        """Create a mock sub-agent registry."""
        registry = Mock()
        
        # Create mock agent
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent.llm = Mock()
        
        # Mock execute_task to return a successful result
        async def mock_execute_task(task, context):
            return SkillResult(
                status=SkillStatus.SUCCESS,
                output={"result": "test output"},
                message="Task completed",
                quality_score=0.9
            )
        
        async def mock_evaluate_result(result, task, context):
            return result
        
        mock_agent.execute_task = mock_execute_task
        mock_agent.evaluate_result = mock_evaluate_result
        
        registry.get_member = Mock(return_value=mock_agent)
        
        return registry
    
    @pytest.fixture
    def executor(self, mock_registry):
        """Create a SubAgentExecutorNode with mocks."""
        tool_registry = Mock()
        workspace = Mock()
        project = Mock()
        
        return SubAgentExecutorNode(
            sub_agent_registry=mock_registry,
            tool_registry=tool_registry,
            workspace=workspace,
            project=project,
            max_parallel_tasks=3
        )
    
    def test_no_plan_returns_respond(self, executor):
        """Test behavior when no execution plan exists."""
        state = {
            "messages": [],
            "execution_plan": None,
            "current_task_index": 0,
            "context": {},
            "sub_agent_results": {},
        }
        
        result = executor(state)
        
        assert result["next_action"] == "respond"
    
    def test_creates_dependency_graph(self, executor):
        """Test that dependency graph is created from plan."""
        state = {
            "messages": [],
            "execution_plan": {
                "tasks": [
                    {"task_id": 1, "agent_name": "TestAgent", "skill_name": "test", "dependencies": []},
                    {"task_id": 2, "agent_name": "TestAgent", "skill_name": "test", "dependencies": [1]},
                ]
            },
            "current_task_index": 0,
            "context": {},
            "sub_agent_results": {},
        }
        
        result = executor(state)
        
        # Check that dependency graph state was created in context
        assert "_dependency_graph_state" in result["context"]
    
    def test_all_tasks_complete_goes_to_review(self, executor):
        """Test that when all tasks are complete, goes to review."""
        # Create a graph with all tasks complete
        graph = DependencyGraph()
        graph.add_task("1", {"task_id": 1}, [])
        graph.mark_complete("1")
        
        state = {
            "messages": [],
            "execution_plan": {"tasks": [{"task_id": 1}]},
            "current_task_index": 1,
            "context": {"_dependency_graph_state": {"completed": ["1"], "failed": [], "running": []}}, # Simulate the graph state
            "sub_agent_results": {"1": {"status": "success"}},
        }
        
        result = executor(state)
        
        assert result["next_action"] == "review_plan"


class TestPlanReviewNode:
    """Tests for PlanReviewNode."""
    
    @pytest.fixture
    def review_node(self):
        """Create a PlanReviewNode with mock LLM."""
        llm = Mock()
        return PlanReviewNode(llm)
    
    def test_all_success_high_quality(self, review_node):
        """Test review with all successful high-quality results."""
        state = {
            "messages": [],
            "execution_plan": {},
            "sub_agent_results": {
                "1": {"status": "success", "quality_score": 0.9},
                "2": {"status": "success", "quality_score": 0.85},
            },
            "context": {},
        }
        
        result = review_node(state)
        
        assert result["next_action"] == "synthesize_results"
        assert result["context"]["plan_review"]["status"] == "success"
    
    def test_all_success_low_quality(self, review_node):
        """Test review with successful but low-quality results."""
        state = {
            "messages": [],
            "execution_plan": {},
            "sub_agent_results": {
                "1": {"status": "success", "quality_score": 0.5},
                "2": {"status": "success", "quality_score": 0.4},
            },
            "context": {},
        }
        
        result = review_node(state)
        
        assert result["next_action"] == "refine_plan"
        assert result["context"]["plan_review"]["status"] == "low_quality"
    
    def test_has_failures(self, review_node):
        """Test review with some failed tasks."""
        state = {
            "messages": [],
            "execution_plan": {},
            "sub_agent_results": {
                "1": {"status": "success", "quality_score": 0.9},
                "2": {"status": "failed", "error": "Test error"},
            },
            "context": {},
        }
        
        result = review_node(state)
        
        assert result["next_action"] == "refine_plan"
        assert result["context"]["plan_review"]["status"] == "has_failures"


class TestResultSynthesisNode:
    """Tests for ResultSynthesisNode."""
    
    @pytest.fixture
    def synthesis_node(self):
        """Create a ResultSynthesisNode with mock LLM."""
        llm = Mock()
        return ResultSynthesisNode(llm)
    
    def test_synthesis_output(self, synthesis_node):
        """Test that synthesis produces correct output."""
        state = {
            "messages": [],
            "execution_plan": {},
            "sub_agent_results": {
                "1": {
                    "status": "success",
                    "agent": "Screenwriter",
                    "skill": "script_outline",
                    "message": "Script created",
                    "quality_score": 0.9
                },
                "2": {
                    "status": "success",
                    "agent": "Director",
                    "skill": "storyboard",
                    "message": "Storyboard created",
                    "quality_score": 0.85
                },
            },
            "context": {
                "original_request": "Create a short film",
                "plan_description": "Create a 1-minute film"
            },
        }
        
        result = synthesis_node(state)
        
        assert result["next_action"] == "respond"
        
        # Check synthesis message contains expected content
        synthesis_msg = result["messages"][-1].content
        assert "Film Production Team Report" in synthesis_msg
        assert "Screenwriter" in synthesis_msg
        assert "Director" in synthesis_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
