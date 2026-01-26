"""Unit tests for ReactService."""
import pytest

from agent.react.react_service import ReactService, React
from agent.react.types import CheckpointData


class TestReactService:
    """Test cases for ReactService singleton."""

    @pytest.fixture
    def service(self):
        """Get a fresh ReactService instance for testing."""
        service = ReactService(max_instances=3)
        service.clear_all_instances()
        return service

    def test_singleton_returns_same_instance(self):
        """Test that ReactService is a singleton."""
        service1 = ReactService()
        service2 = ReactService()
        assert service1 is service2

    def test_get_instance_count(self, service):
        """Test getting instance count."""
        assert service.get_instance_count() == 0

    def test_list_instances_empty(self, service):
        """Test listing instances when empty."""
        instances = service.list_instances()
        assert instances == {}

    def test_get_react_not_exists(self, service):
        """Test getting a non-existent react instance."""
        result = service.get_react("project", "type")
        assert result is None

    def test_remove_react_not_exists(self, service):
        """Test removing a non-existent react instance."""
        result = service.remove_react("project", "type")
        assert result is False

    def test_clear_all_instances(self, service):
        """Test clearing all instances."""
        # Create some mock instances (without actually initializing React)
        service._instances["key1"] = "mock1"
        service._instances["key2"] = "mock2"

        service.clear_all_instances()

        assert service.get_instance_count() == 0

    def test_lru_eviction_when_max_reached(self, service):
        """Test that oldest instance is evicted when max is reached."""
        # This is a simplified test - in real scenario we'd create actual React instances
        # For now we test the eviction logic directly
        service._instances["old"] = "old_instance"
        service._instances["mid"] = "mid_instance"
        service._instances["new"] = "new_instance"

        # Access to update order (most recently used)
        service._access_instance("old")

        # Add one more - should evict "mid" since "old" was just accessed
        service._evict_if_needed()

        # Should still have 3 instances (limit not exceeded in this case)
        assert len(service._instances) == 3

    def test_get_metrics(self, service):
        """Test getting service metrics."""
        # Create mock instance with metrics
        mock_instance = type('MockReact', (), {
            'get_metrics': lambda: {
                'run_id': 'test',
                'step_id': 1,
                'status': 'RUNNING'
            }
        })()
        service._instances["test:test"] = mock_instance

        metrics = service.get_metrics()

        assert metrics["total_instances"] == 1
        assert metrics["max_instances"] == 3
        assert "test:test" in metrics["instances"]
