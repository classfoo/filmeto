#!/usr/bin/env python3
"""Test script for the updated FilmetoAgent implementation."""

import asyncio
import os
from unittest.mock import MagicMock

from agent import FilmetoAgent


async def test_updated_filmeto_agent():
    """Test the updated FilmetoAgent implementation."""
    
    # Create mock workspace and project
    mock_workspace = MagicMock()
    mock_project = MagicMock()
    mock_project.project_name = "test_project"
    mock_project.get_conversation_manager.return_value = MagicMock()
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not set, using dummy key for testing")
        api_key = "dummy-key-for-testing"
    
    # Initialize the agent
    agent = FilmetoAgent(
        workspace=mock_workspace,
        project=mock_project,
        api_key=api_key,
        model="gpt-3.5-turbo",  # Using a cheaper model for testing
        temperature=0.7
    )
    
    print("Testing FilmetoAgent initialization...")
    if agent.production_agent:
        print("✓ FilmetoAgent initialized successfully")
    else:
        print("✗ FilmetoAgent initialization failed")
        return
    
    print("\nTesting conversation creation...")
    try:
        conversation = agent.create_conversation("Test Conversation")
        print(f"✓ Conversation created: {conversation.conversation_id}")
    except Exception as e:
        print(f"✗ Error creating conversation: {e}")
        return
    
    print("\nTesting chat functionality...")
    try:
        # This would normally require a real API call, so we'll just check if the method exists
        if hasattr(agent, 'chat_stream'):
            print("✓ chat_stream method exists")
        if hasattr(agent, 'chat'):
            print("✓ chat method exists")
    except Exception as e:
        print(f"✗ Error checking methods: {e}")
    
    print("\nTesting agent capabilities...")
    try:
        capabilities = agent.get_agent_capabilities()
        print(f"✓ Retrieved agent capabilities for {len(capabilities)} agents")
        for agent_name, skills in capabilities.items():
            print(f"  - {agent_name}: {len(skills)} skills")
    except Exception as e:
        print(f"✗ Error retrieving capabilities: {e}")
    
    print("\nFilmetoAgent test completed!")


if __name__ == "__main__":
    asyncio.run(test_updated_filmeto_agent())