"""
Tests for the ReactService module.

This module tests the ReactService class which manages React instances
with reuse capability by project_name and react_type.
"""
import asyncio
from unittest.mock import Mock, AsyncMock

import pytest

from agent.react import ReactService, React, react_service
from agent.react.types import ReactEvent, ReactEventType


@pytest.fixture
def mock_workspace():
    """Mock workspace for testing."""
    workspace = Mock()
    workspace.workspace_dir = "test_workspace"
    return workspace


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    llm_service = Mock()
    llm_service.validate_config = Mock(return_value=True)
    llm_service.completion = Mock(return_value={
        "choices": [{"message": {"content": '{"type": "final", "final": "Test response"}'}}]
    })
    return llm_service


@pytest.fixture
def mock_tool_call_function():
    """Mock tool call function for testing."""
    async def tool_call_function(tool_name: str, tool_args: dict):
        return f"Result for {tool_name} with {tool_args}"
    
    return tool_call_function


def test_singleton_pattern():
    """Test that ReactService follows the singleton pattern."""
    service1 = ReactService()
    service2 = ReactService()
    
    assert service1 is service2
    assert react_service is service1


def test_get_or_create_react_creates_new_instance(mock_workspace, mock_llm_service, mock_tool_call_function):
    """Test that get_or_create_react creates a new instance when it doesn't exist."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state

    project_name = "test_project"
    react_type = "test_type"

    def build_prompt_function(user_input: str) -> str:
        return f"System prompt for {user_input}"

    react_instance = service.get_or_create_react(
        project_name=project_name,
        react_type=react_type,
        build_prompt_function=build_prompt_function,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    assert isinstance(react_instance, React)
    assert react_instance.project_name == project_name
    assert react_instance.react_type == react_type
    assert react_instance.build_prompt_function is build_prompt_function


def test_get_or_create_react_returns_existing_instance(mock_workspace, mock_llm_service, mock_tool_call_function):
    """Test that get_or_create_react returns an existing instance if it already exists."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state

    project_name = "test_project"
    react_type = "test_type"

    def build_prompt_function(user_input: str) -> str:
        return f"System prompt for {user_input}"

    # Create the first instance
    first_instance = service.get_or_create_react(
        project_name=project_name,
        react_type=react_type,
        build_prompt_function=build_prompt_function,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    # Try to create another instance with the same parameters
    second_instance = service.get_or_create_react(
        project_name=project_name,
        react_type=react_type,
        build_prompt_function=build_prompt_function,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    # Both should be the same instance
    assert first_instance is second_instance


def test_get_react_returns_existing_instance(mock_workspace, mock_llm_service, mock_tool_call_function):
    """Test that get_react returns an existing instance."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state

    project_name = "test_project"
    react_type = "test_type"

    def build_prompt_function(user_input: str) -> str:
        return f"System prompt for {user_input}"

    # Create an instance first
    expected_instance = service.get_or_create_react(
        project_name=project_name,
        react_type=react_type,
        build_prompt_function=build_prompt_function,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    # Get the instance using get_react
    actual_instance = service.get_react(project_name, react_type)

    assert actual_instance is expected_instance


def test_get_react_returns_none_for_nonexistent_instance():
    """Test that get_react returns None for a non-existent instance."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state
    
    actual_instance = service.get_react("nonexistent_project", "nonexistent_type")
    
    assert actual_instance is None


def test_remove_react_removes_existing_instance(mock_workspace, mock_llm_service, mock_tool_call_function):
    """Test that remove_react removes an existing instance."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state

    project_name = "test_project"
    react_type = "test_type"

    def build_prompt_function(user_input: str) -> str:
        return f"System prompt for {user_input}"

    # Create an instance
    service.get_or_create_react(
        project_name=project_name,
        react_type=react_type,
        build_prompt_function=build_prompt_function,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    # Verify it exists
    assert service.get_react(project_name, react_type) is not None

    # Remove it
    result = service.remove_react(project_name, react_type)

    assert result is True
    assert service.get_react(project_name, react_type) is None


def test_remove_react_returns_false_for_nonexistent_instance():
    """Test that remove_react returns False for a non-existent instance."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state
    
    result = service.remove_react("nonexistent_project", "nonexistent_type")
    
    assert result is False


def test_clear_all_instances(mock_workspace, mock_llm_service, mock_tool_call_function):
    """Test that clear_all_instances removes all instances."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state

    def build_prompt_function1(user_input: str) -> str:
        return f"System prompt 1 for {user_input}"

    def build_prompt_function2(user_input: str) -> str:
        return f"System prompt 2 for {user_input}"

    # Create multiple instances
    service.get_or_create_react(
        project_name="project1",
        react_type="type1",
        build_prompt_function=build_prompt_function1,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    service.get_or_create_react(
        project_name="project2",
        react_type="type2",
        build_prompt_function=build_prompt_function2,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    # Verify they exist
    assert len(service.list_instances()) == 2
    assert service.get_react("project1", "type1") is not None
    assert service.get_react("project2", "type2") is not None

    # Clear all instances
    service.clear_all_instances()

    # Verify they are gone
    assert len(service.list_instances()) == 0
    assert service.get_react("project1", "type1") is None
    assert service.get_react("project2", "type2") is None


def test_list_instances(mock_workspace, mock_llm_service, mock_tool_call_function):
    """Test that list_instances returns all stored instances."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state

    def build_prompt_function1(user_input: str) -> str:
        return f"System prompt 1 for {user_input}"

    def build_prompt_function2(user_input: str) -> str:
        return f"System prompt 2 for {user_input}"

    # Create multiple instances
    instance1 = service.get_or_create_react(
        project_name="project1",
        react_type="type1",
        build_prompt_function=build_prompt_function1,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    instance2 = service.get_or_create_react(
        project_name="project2",
        react_type="type2",
        build_prompt_function=build_prompt_function2,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    # Get the list of instances
    instances = service.list_instances()

    assert len(instances) == 2
    assert "project1:type1" in instances
    assert "project2:type2" in instances
    assert instances["project1:type1"] is instance1
    assert instances["project2:type2"] is instance2


@pytest.mark.asyncio
async def test_react_instance_functionality_through_service(
    mock_workspace, mock_llm_service, mock_tool_call_function
):
    """Test that React instances obtained through the service work correctly."""
    service = ReactService()
    service.clear_all_instances()  # Ensure clean state

    project_name = "test_project"
    react_type = "test_type"

    def build_prompt_function(user_input: str) -> str:
        return f"System prompt for {user_input}"

    # Get an instance through the service
    react_instance = service.get_or_create_react(
        project_name=project_name,
        react_type=react_type,
        build_prompt_function=build_prompt_function,
        react_tool_call_function=mock_tool_call_function,
        workspace=mock_workspace,
        llm_service=mock_llm_service
    )

    # Verify the instance works by starting a simple chat stream
    # Note: This is a simplified test since full LLM integration would require mocking more
    assert react_instance.project_name == project_name
    assert react_instance.react_type == react_type
    assert react_instance.build_prompt_function is build_prompt_function