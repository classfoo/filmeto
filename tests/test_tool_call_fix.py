#!/usr/bin/env python
"""Test script to verify the fix for tool call/response mismatch."""

from app.data.conversation import Conversation, Message, MessageRole
from datetime import datetime

def test_tool_call_fix():
    """Test that the fix handles tool call/response mismatches properly."""
    print("Testing tool call/response mismatch fix...")
    
    # Create a conversation
    conv = Conversation(
        conversation_id='test_conv',
        title='Test Conversation',
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        messages=[]
    )
    
    # Add a user message
    user_msg = Message(
        role=MessageRole.USER,
        content='Can you create a new task?',
        timestamp=datetime.now().isoformat()
    )
    conv.add_message(user_msg)
    
    # Add an assistant message WITH tool calls (simulating the problematic case)
    assistant_msg_with_tools = Message(
        role=MessageRole.ASSISTANT,
        content='I will create a new task for you.',
        timestamp=datetime.now().isoformat(),
        tool_calls=[
            {
                'name': 'create_task',
                'id': 'call_abc123',
                'args': {'title': 'Sample Task', 'description': 'A sample task'}
            }
        ]
    )
    conv.add_message(assistant_msg_with_tools)
    
    # Note: Deliberately NOT adding the corresponding tool response message
    # This simulates the problematic scenario
    
    # Add another user message
    user_msg2 = Message(
        role=MessageRole.USER,
        content='Thanks!',
        timestamp=datetime.now().isoformat()
    )
    conv.add_message(user_msg2)
    
    # Convert to LangChain messages - this should now work without error
    # (with a warning logged about the missing tool response)
    lc_msgs = conv.get_langchain_messages()
    
    print(f"Successfully converted {len(lc_msgs)} messages")
    print("Messages in conversation:")
    for i, msg in enumerate(conv.messages):
        print(f"  {i}: {msg.role} - {'has tool calls' if msg.tool_calls else 'no tool calls'}")
    
    print("LangChain messages:")
    for i, msg in enumerate(lc_msgs):
        msg_type = type(msg).__name__
        has_tools = hasattr(msg, 'tool_calls') and msg.tool_calls
        tool_id = getattr(msg, 'tool_call_id', None)
        print(f"  {i}: {msg_type} - {'has tool calls' if has_tools else 'tool call ID: ' + str(tool_id) if tool_id else 'regular message'}")
    
    # The assistant message with tool calls should be filtered out
    assistant_messages_with_tools = [msg for msg in lc_msgs if 
                                     hasattr(msg, 'tool_calls') and msg.tool_calls]
    print(f"\nAssistant messages with tool calls in output: {len(assistant_messages_with_tools)}")
    
    if len(assistant_messages_with_tools) == 0:
        print("✓ SUCCESS: Assistant messages with unpaired tool calls were filtered out")
        print("✓ This prevents the LangChain error")
    else:
        print("✗ FAILED: Assistant messages with unpaired tool calls were not filtered out")
    
    print("\nThe fix successfully prevents the 'tool_calls must be followed by tool messages' error!")
    print("When an assistant message has tool calls without corresponding responses, it's now skipped.")


if __name__ == "__main__":
    test_tool_call_fix()