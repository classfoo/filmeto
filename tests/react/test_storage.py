"""Unit tests for ReactStorage."""
import json
import pytest
import tempfile
from pathlib import Path

from agent.react.storage import ReactStorage
from agent.react.types import CheckpointData


class TestReactStorage:
    """Test cases for ReactStorage."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_workspace):
        """Create a ReactStorage instance for testing."""
        return ReactStorage(
            project_name="test_project",
            react_type="test_react",
            workspace_root=temp_workspace
        )

    @pytest.fixture
    def sample_checkpoint(self):
        """Create a sample checkpoint for testing."""
        return CheckpointData(
            run_id="test_run_123",
            step_id=5,
            status="RUNNING",
            messages=[
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
            ],
            pending_user_messages=["What's next?"],
            last_tool_calls=None,
            last_tool_results=None,
        )

    def test_save_and_load_checkpoint(self, storage, sample_checkpoint):
        """Test saving and loading a checkpoint."""
        storage.save_checkpoint(sample_checkpoint)
        loaded = storage.load_checkpoint()

        assert loaded is not None
        assert loaded.run_id == sample_checkpoint.run_id
        assert loaded.step_id == sample_checkpoint.step_id
        assert loaded.status == sample_checkpoint.status
        assert len(loaded.messages) == len(sample_checkpoint.messages)
        assert loaded.pending_user_messages == sample_checkpoint.pending_user_messages

    def test_load_nonexistent_checkpoint(self, storage):
        """Test loading a checkpoint that doesn't exist returns None."""
        result = storage.load_checkpoint()
        assert result is None

    def test_save_checkpoint_atomic(self, storage, sample_checkpoint):
        """Test that checkpoint save is atomic (uses temp file)."""
        storage.save_checkpoint(sample_checkpoint)

        # Check that .tmp file doesn't exist after save
        temp_file = storage.checkpoint_file.with_suffix('.tmp')
        assert not temp_file.exists()

        # Check that main file exists
        assert storage.checkpoint_file.exists()

    def test_save_and_load_config(self, storage):
        """Test saving and loading config."""
        config = {"model": "gpt-4", "temperature": 0.7}
        storage.save_config(config)

        loaded = storage.load_config()
        assert loaded == config

    def test_load_nonexistent_config(self, storage):
        """Test loading config that doesn't exist returns None."""
        result = storage.load_config()
        assert result is None

    def test_append_to_history(self, storage):
        """Test appending events to history."""
        event1 = {"type": "test", "data": "event1"}
        event2 = {"type": "test", "data": "event2"}

        storage.append_to_history(event1)
        storage.append_to_history(event2)

        # Read history file and verify
        with open(storage.history_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert json.loads(lines[0]) == event1
        assert json.loads(lines[1]) == event2

    def test_clear_history(self, storage):
        """Test clearing history file."""
        storage.append_to_history({"type": "test"})
        assert storage.history_file.exists()

        storage.clear_history()
        assert not storage.history_file.exists()

    def test_delete_checkpoint(self, storage, sample_checkpoint):
        """Test deleting checkpoint file."""
        storage.save_checkpoint(sample_checkpoint)
        assert storage.checkpoint_file.exists()

        result = storage.delete_checkpoint()
        assert result is True
        assert not storage.checkpoint_file.exists()

    def test_delete_nonexistent_checkpoint(self, storage):
        """Test deleting a checkpoint that doesn't exist."""
        result = storage.delete_checkpoint()
        assert result is False

    def test_load_invalid_json_returns_none(self, storage):
        """Test that loading invalid JSON returns None."""
        # Write invalid JSON to checkpoint file
        storage.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(storage.checkpoint_file, 'w') as f:
            f.write("not valid json")

        result = storage.load_checkpoint()
        assert result is None

    def test_load_missing_required_field_returns_none(self, storage):
        """Test that loading checkpoint with missing fields returns None."""
        storage.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(storage.checkpoint_file, 'w') as f:
            json.dump({"run_id": "test"}, f)  # Missing required fields

        result = storage.load_checkpoint()
        assert result is None

    def test_checkpoint_data_updated_at_changes(self, storage, sample_checkpoint):
        """Test that updated_at is set when saving."""
        original_time = sample_checkpoint.created_at
        storage.save_checkpoint(sample_checkpoint)

        loaded = storage.load_checkpoint()
        # updated_at should be >= original time
        assert loaded.updated_at >= original_time
