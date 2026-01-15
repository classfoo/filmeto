#!/usr/bin/env python
"""Test for FilmetoAgent execution capabilities."""

import asyncio
from unittest.mock import Mock
from langchain_core.messages import HumanMessage
from agent.filmeto_agent import FilmetoAgent
from app.data.workspace import Workspace
from app.data.project import Project


def test_filmeto_agent_basic_execution():
    """Test basic execution capabilities of FilmetoAgent."""
    print("Testing FilmetoAgent basic execution...")

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

    print("✓ FilmetoAgent basic execution test passed")


def test_filmeto_agent_streaming():
    """Test streaming capabilities of FilmetoAgent."""
    print("Testing FilmetoAgent streaming...")

    # Create a mock workspace and project
    workspace = Workspace()
    project = Project("test_project", "/tmp/test_project")

    # Create the agent with streaming enabled
    agent = FilmetoAgent(
        workspace=workspace,
        project=project,
        model='gpt-4o-mini',
        temperature=0.7,
        streaming=True
    )

    # Verify streaming is enabled
    assert agent.streaming is True

    print("✓ FilmetoAgent streaming test passed")


def test_filmeto_agent_message_handling():
    """Test message handling of FilmetoAgent."""
    print("Testing FilmetoAgent message handling...")

    # Create a mock workspace and project
    workspace = Workspace()
    project = Project("test_project", "/tmp/test_project")

    # Create the agent
    agent = FilmetoAgent(
        workspace=workspace,
        project=project
    )

    # Verify initial state
    assert len(agent.conversation_history) == 0

    print("✓ FilmetoAgent message handling test passed")


if __name__ == "__main__":
    test_filmeto_agent_basic_execution()
    test_filmeto_agent_streaming()
    test_filmeto_agent_message_handling()
    print("\nAll FilmetoAgent tests passed!")