"""Integration tests for React flow."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock

from agent.react import React, ReactEventType
from agent.react.storage import ReactStorage
from agent.react.types import CheckpointData


class MockWorkspace:
    """Mock workspace for testing."""
    def get_path(self):
        return "/tmp/test_workspace"


class TestReactIntegration:
    """Integration tests for React flow."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace path."""
        return str(tmp_path)

    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        mock = Mock()
        mock.validate_config.return_value = True
        mock.default_model = "test-model"
        mock.temperature = 0.7
        return mock

    @pytest.fixture
    def sample_react(self, temp_workspace, mock_llm_service):
        """Create a React instance for testing."""
        return React(
            workspace=MockWorkspace(),
            project_name="test_project",
            react_type="test_type",
            build_prompt_function=lambda: "You are a helpful assistant.",
            tool_call_function=lambda name, args: {"result": f"Called {name}"},
            llm_service=mock_llm_service,
            max_steps=5,
        )

    @pytest.mark.asyncio
    async def test_react_initialization(self, sample_react):
        """Test React instance initialization."""
        assert sample_react.project_name == "test_project"
        assert sample_react.react_type == "test_type"
        assert sample_react.max_steps == 5
        assert sample_react.status == "IDLE"
        assert sample_react.step_id == 0

    @pytest.mark.asyncio
    async def test_start_new_run(self, sample_react):
        """Test starting a new run."""
        sample_react._start_new_run()
        assert sample_react.status == "RUNNING"
        assert sample_react.step_id == 0
        assert sample_react.run_id != ""
        assert len(sample_react.messages) == 1  # System prompt
        assert sample_react.messages[0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_create_event(self, sample_react):
        """Test event creation."""
        sample_react.run_id = "test_run"
        sample_react.step_id = 1
        event = sample_react._create_event("llm_thinking", {"message": "thinking"})
        assert event.event_type == "llm_thinking"
        assert event.run_id == "test_run"
        assert event.step_id == 1
        assert event.payload["message"] == "thinking"

    def test_drain_pending_messages(self, sample_react):
        """Test draining pending messages."""
        sample_react.pending_user_messages = ["msg1", "msg2", "msg3"]
        messages = sample_react._drain_pending_messages()
        assert messages == ["msg1", "msg2", "msg3"]
        assert sample_react.pending_user_messages == []

    def test_maybe_update_checkpoint(self, sample_react):
        """Test checkpoint interval logic."""
        # With interval of 2, should only save every 2 steps
        sample_react.checkpoint_interval = 2
        sample_react._steps_since_checkpoint = 0

        # First call - doesn't save
        sample_react._maybe_update_checkpoint()
        assert sample_react._steps_since_checkpoint == 1

        # Second call - saves
        sample_react._maybe_update_checkpoint()
        assert sample_react._steps_since_checkpoint == 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, sample_react):
        """Test metrics are tracked correctly."""
        # Initially all zeros
        metrics = sample_react.get_metrics()
        assert metrics["total_llm_calls"] == 0
        assert metrics["total_tool_calls"] == 0

        # Metrics will be updated during actual flow
        # This is a basic structure test
        assert "run_id" in metrics
        assert "step_id" in metrics
        assert "status" in metrics

    @pytest.mark.asyncio
    async def test_context_manager(self, sample_react):
        """Test async context manager cleanup."""
        sample_react.status = "RUNNING"
        sample_react._in_react_loop = True

        async with sample_react:
            # Inside context, status should still be RUNNING
            pass

        # After context, should be cleaned up
        assert sample_react._in_react_loop is False
        # Status should be IDLE since it was RUNNING before
        assert sample_react.status == "IDLE"

    @pytest.mark.asyncio
    async def test_context_manager_with_final_status(self, sample_react):
        """Test context manager doesn't change terminal status."""
        sample_react.status = "FINAL"
        sample_react._in_react_loop = True

        async with sample_react:
            pass

        assert sample_react._in_react_loop is False
        # FINAL status should not be changed to IDLE
        assert sample_react.status == "FINAL"


class TestReactStorageIntegration:
    """Integration tests for ReactStorage with actual files."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a ReactStorage with temp directory."""
        return ReactStorage(
            project_name="test_project",
            react_type="test_type",
            workspace_root=str(tmp_path)
        )

    @pytest.fixture
    def sample_checkpoint(self):
        """Create a sample checkpoint."""
        return CheckpointData(
            run_id="run_123",
            step_id=3,
            status="RUNNING",
            messages=[
                {"role": "system", "content": "Prompt"},
                {"role": "user", "content": "Hello"},
            ],
            pending_user_messages=["Next message"],
            last_tool_calls=None,
            last_tool_results=None,
        )

    def test_full_checkpoint_lifecycle(self, storage, sample_checkpoint):
        """Test save, load, delete checkpoint lifecycle."""
        # Initially no checkpoint
        assert storage.load_checkpoint() is None

        # Save checkpoint
        storage.save_checkpoint(sample_checkpoint)
        assert storage.checkpoint_file.exists()

        # Load checkpoint
        loaded = storage.load_checkpoint()
        assert loaded is not None
        assert loaded.run_id == sample_checkpoint.run_id
        assert loaded.step_id == sample_checkpoint.step_id

        # Delete checkpoint
        result = storage.delete_checkpoint()
        assert result is True
        assert not storage.checkpoint_file.exists()

        # Can't load after deletion
        assert storage.load_checkpoint() is None

    def test_checkpoint_overwrite(self, storage, sample_checkpoint):
        """Test overwriting an existing checkpoint."""
        # Save first checkpoint
        storage.save_checkpoint(sample_checkpoint)

        # Modify and save again
        sample_checkpoint.step_id = 5
        storage.save_checkpoint(sample_checkpoint)

        # Load should get updated version
        loaded = storage.load_checkpoint()
        assert loaded.step_id == 5

    def test_history_operations(self, storage):
        """Test history file operations."""
        event1 = {"type": "test1", "data": "data1"}
        event2 = {"type": "test2", "data": "data2"}

        # Append events
        storage.append_to_history(event1)
        storage.append_to_history(event2)
        assert storage.history_file.exists()

        # Clear history
        storage.clear_history()
        assert not storage.history_file.exists()

    def test_config_operations(self, storage):
        """Test config file operations."""
        config = {"model": "gpt-4", "temperature": 0.5}

        # Save config
        storage.save_config(config)
        assert storage.config_file.exists()

        # Load config
        loaded = storage.load_config()
        assert loaded == config
