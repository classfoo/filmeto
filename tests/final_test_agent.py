#!/usr/bin/env python3
"""Comprehensive test for the final FilmetoAgent implementation."""

import asyncio
import os
from unittest.mock import MagicMock

from agent import FilmetoAgent


async def comprehensive_test():
    """Comprehensive test of the final FilmetoAgent implementation."""
    
    print("=== Comprehensive Test of Updated FilmetoAgent ===\n")
    
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
    
    print("1. Initializing FilmetoAgent...")
    try:
        agent = FilmetoAgent(
            workspace=mock_workspace,
            project=mock_project,
            api_key=api_key,
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        if agent.llm_service.validate_config():
            print("   ✓ FilmetoAgent initialized successfully")
        else:
            print("   ✗ FilmetoAgent initialization failed")
            return False
    except Exception as e:
        print(f"   ✗ Error initializing agent: {e}")
        return False
    
    print("\n2. Testing conversation management...")
    try:
        # Test conversation creation
        conversation = agent.create_conversation("Test Conversation")
        print(f"   ✓ Conversation created: {conversation.conversation_id}")
        
        # Test getting conversation
        conv_id = conversation.conversation_id
        agent.set_conversation(conv_id)
        print("   ✓ Conversation set successfully")
        
        # Test listing conversations
        conv_list = agent.list_conversations()
        print(f"   ✓ Listed conversations: {len(conv_list)} found")
        
    except Exception as e:
        print(f"   ✗ Error in conversation management: {e}")
        return False
    
    print("\n3. Testing agent capabilities...")
    try:
        capabilities = agent.get_agent_capabilities()
        print(f"   ✓ Retrieved agent capabilities for {len(capabilities)} agents")
        for agent_name, skills in capabilities.items():
            print(f"     - {agent_name}: {len(skills)} skills")
        
        available_agents = agent.get_available_agents()
        print(f"   ✓ Available agents: {len(available_agents)}")
        
    except Exception as e:
        print(f"   ✗ Error retrieving capabilities: {e}")
        return False
    
    print("\n4. Testing context updates...")
    try:
        # Create new mock objects
        new_mock_workspace = MagicMock()
        new_mock_project = MagicMock()
        new_mock_project.project_name = "new_test_project"
        new_mock_project.get_conversation_manager.return_value = MagicMock()
        
        # Update context
        agent.update_context(workspace=new_mock_workspace, project=new_mock_project)
        print("   ✓ Context updated successfully")
        
    except Exception as e:
        print(f"   ✗ Error updating context: {e}")
        return False
    
    print("\n5. Testing event callbacks...")
    try:
        def dummy_callback(event):
            pass
        
        agent.add_stream_callback(dummy_callback)
        print("   ✓ Stream callback added successfully")
        
        agent.remove_stream_callback(dummy_callback)
        print("   ✓ Stream callback removed successfully")
        
    except Exception as e:
        print(f"   ✗ Error in event callback management: {e}")
        return False
    
    print("\n=== All tests passed! ===")
    print("The updated FilmetoAgent implementation is working correctly.")
    return True


if __name__ == "__main__":
    success = asyncio.run(comprehensive_test())
    if success:
        print("\n✓ All comprehensive tests passed!")
    else:
        print("\n✗ Some tests failed!")
        exit(1)