import asyncio
import pytest
from unittest.mock import AsyncMock

from agent.react import React, ReactEventType


@pytest.mark.asyncio
async def test_react_basic_functionality():
    """
    Test basic React functionality.
    """
    async def mock_tool_call(tool_name, tool_args):
        if tool_name == "test_tool":
            return {"result": f"Processed {tool_args.get('input', 'no input')}"}
        return {"error": f"Unknown tool: {tool_name}"}
    
    react_instance = React(
        project_name="test_project",
        react_type="test_react",
        base_prompt_template="You are a test assistant. Respond with {\"type\": \"final\", \"final\": \"Test response\"}",
        react_tool_call_function=mock_tool_call,
        max_steps=3
    )
    
    # Collect all events
    events = []
    async for event in react_instance.chat_stream("Test message"):
        events.append(event)
        if event.event_type == ReactEventType.FINAL:
            break
    
    # Verify we got events
    assert len(events) > 0
    assert any(event.event_type == ReactEventType.FINAL for event in events)


@pytest.mark.asyncio
async def test_react_tool_call():
    """
    Test React with tool calls.
    """
    async def mock_tool_call(tool_name, tool_args):
        if tool_name == "calculate":
            expression = tool_args.get("expression", "")
            try:
                # Safe calculation for testing
                result = eval(expression)  # NOQA: S307
                return {"result": f"Calculation result: {result}"}
            except Exception as e:
                return {"error": f"Calculation failed: {str(e)}"}
        return {"error": f"Unknown tool: {tool_name}"}

    react_instance = React(
        project_name="test_project",
        react_type="test_react",
        base_prompt_template="You are a test assistant that performs calculations. When asked to calculate, respond with {\"type\": \"tool\", \"tool_name\": \"calculate\", \"tool_args\": {\"expression\": \"<expression>\"}}. Otherwise respond with {\"type\": \"final\", \"final\": \"<response>\"}",
        react_tool_call_function=mock_tool_call,
        max_steps=3
    )

    events = []
    async for event in react_instance.chat_stream("Calculate 5 plus 3"):
        events.append(event)
        # Break after tool execution or final response
        if event.event_type == ReactEventType.FINAL or (
            event.event_type == ReactEventType.TOOL_END and event.payload.get("ok", False)
        ):
            break

    # Verify tool was called
    tool_start_events = [e for e in events if e.event_type == ReactEventType.TOOL_START]
    tool_end_events = [e for e in events if e.event_type == ReactEventType.TOOL_END]

    assert len(tool_start_events) >= 1
    assert len(tool_end_events) >= 1
    assert tool_end_events[0].payload["ok"] is True


@pytest.mark.asyncio
async def test_react_message_intervention():
    """
    Test that new messages can intervene during execution.
    """
    async def mock_tool_call(tool_name, tool_args):
        return {"result": "Tool executed"}
    
    react_instance = React(
        project_name="test_project",
        react_type="test_react",
        base_prompt_template='You are a test assistant. Respond with {"type": "final", "final": "Response"}',
        react_tool_call_function=mock_tool_call,
        max_steps=3
    )
    
    # Start a conversation
    stream1 = react_instance.chat_stream("First message")
    first_event = await stream1.__anext__()
    assert first_event.event_type == ReactEventType.LLM_THINKING
    
    # Add another message while the first is still processing
    stream2 = react_instance.chat_stream("Second message")
    second_event = await stream2.__anext__()
    assert second_event.event_type == ReactEventType.LLM_THINKING
    
    # Both streams should continue normally
    events1 = [first_event]
    async for event in stream1:
        events1.append(event)
        if event.event_type == ReactEventType.FINAL:
            break
    
    events2 = [second_event]
    async for event in stream2:
        events2.append(event)
        if event.event_type == ReactEventType.FINAL:
            break
    
    # Both should have final events
    assert any(e.event_type == ReactEventType.FINAL for e in events1)
    assert any(e.event_type == ReactEventType.FINAL for e in events2)


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_react_basic_functionality())
    print("✓ Basic functionality test passed")
    
    asyncio.run(test_react_tool_call())
    print("✓ Tool call test passed")
    
    asyncio.run(test_react_message_intervention())
    print("✓ Message intervention test passed")
    
    print("\nAll tests passed!")