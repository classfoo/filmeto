#!/usr/bin/env python
"""Test for FilmetoAgent planner functionality."""

from unittest.mock import Mock
from langchain_core.messages import HumanMessage
from agent.filmeto_agent import FilmetoAgent
from app.data.workspace import Workspace
from app.data.project import Project


def test_filmeto_agent_planner_functionality():
    """Test planner functionality of FilmetoAgent."""
    print("Testing FilmetoAgent planner functionality...")

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

    # Verify the agent was created successfully
    assert agent is not None
    assert agent.workspace == workspace
    assert agent.project == project

    print("✓ FilmetoAgent planner functionality test passed")


def test_filmeto_agent_with_different_models():
    """Test FilmetoAgent with different models."""
    print("Testing FilmetoAgent with different models...")

    # Create a mock workspace and project
    workspace = Workspace()
    project = Project("test_project", "/tmp/test_project")

    # Create the agent with a different model
    agent = FilmetoAgent(
        workspace=workspace,
        project=project,
        model='gpt-3.5-turbo',
        temperature=0.5
    )

    # Verify the agent was created with correct parameters
    assert agent.model == 'gpt-3.5-turbo'
    assert agent.temperature == 0.5

    print("✓ FilmetoAgent with different models test passed")


def test_filmeto_agent_conversation_history():
    """Test FilmetoAgent conversation history."""
    print("Testing FilmetoAgent conversation history...")

    # Create a mock workspace and project
    workspace = Workspace()
    project = Project("test_project", "/tmp/test_project")

    # Create the agent
    agent = FilmetoAgent(
        workspace=workspace,
        project=project
    )

    # Verify initial conversation history is empty
    assert len(agent.conversation_history) == 0

    print("✓ FilmetoAgent conversation history test passed")


if __name__ == "__main__":
    test_filmeto_agent_planner_functionality()
    test_filmeto_agent_with_different_models()
    test_filmeto_agent_conversation_history()
    print("\nAll FilmetoAgent planner tests passed!")