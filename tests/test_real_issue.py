#!/usr/bin/env python
"""Test for FilmetoAgent functionality."""

from agent.filmeto_agent import FilmetoAgent
from app.data.workspace import Workspace
from app.data.project import Project


def test_filmeto_agent_basic_functionality():
    """Test basic functionality of FilmetoAgent."""
    print("Testing FilmetoAgent basic functionality...")

    # Create a mock workspace and project
    workspace = Workspace()
    project = Project("test_project", "/tmp/test_project")

    # Create the agent
    agent = FilmetoAgent(
        workspace=workspace,
        project=project,
        model='gpt-4o-mini',
        temperature=0.7
    )

    # Verify basic properties
    assert agent.workspace == workspace
    assert agent.project == project
    assert agent.model == 'gpt-4o-mini'
    assert agent.temperature == 0.7

    # Check that LLM service is configured
    assert agent.llm_service is not None

    print("✓ FilmetoAgent basic functionality test passed")


def test_filmeto_agent_with_llm_service():
    """Test FilmetoAgent with LLM service."""
    print("Testing FilmetoAgent with LLM service...")

    # Create a mock workspace and project
    workspace = Workspace()
    project = Project("test_project", "/tmp/test_project")

    # Create the agent
    agent = FilmetoAgent(
        workspace=workspace,
        project=project
    )

    # Verify that the agent has an LLM service
    assert hasattr(agent, 'llm_service')
    assert agent.llm_service is not None

    print("✓ FilmetoAgent with LLM service test passed")


if __name__ == "__main__":
    test_filmeto_agent_basic_functionality()
    test_filmeto_agent_with_llm_service()
    print("\nAll tests passed!")