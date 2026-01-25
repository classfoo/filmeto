#!/usr/bin/env python3
"""
Demo script for the new React module.
This script demonstrates the basic functionality of the React processor.
"""

import asyncio
import json
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.react import React, ReactEventType


async def mock_tool_call(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock tool call function for demonstration purposes.
    """
    print(f"Calling tool: {tool_name} with args: {tool_args}")
    
    if tool_name == "search":
        query = tool_args.get("query", "")
        return {"result": f"Mock search results for '{query}'"}
    elif tool_name == "calculate":
        expression = tool_args.get("expression", "")
        try:
            # Note: In a real implementation, use a safe evaluation method
            result = eval(expression)  # NOQA: S307
            return {"result": f"Calculation result: {result}"}
        except Exception as e:
            return {"error": f"Calculation failed: {str(e)}"}
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def main():
    """
    Main demo function.
    """
    print("Starting React module demo...")
    
    # Create a React instance
    react_instance = React(
        project_name="demo_project",
        react_type="demo_react",
        base_prompt_template="""
You are a helpful assistant that follows the ReAct (Reasoning and Acting) framework.
Your response should be in JSON format with one of these structures:
- For tool use: {{"type": "tool", "tool_name": "...", "tool_args": {{...}}}}
- For final response: {{"type": "final", "final": "..."}}""",
        react_tool_call_function=mock_tool_call,
        max_steps=5
    )
    
    print("\n1. Starting a new conversation...")
    user_message = "What is 15 times 27?"
    async for event in react_instance.chat_stream(user_message):
        print(f"Event: {event.event_type}")
        print(f"Payload: {json.dumps(event.payload, indent=2)}")
        print("-" * 50)
        
        # Stop after the first final response
        if event.event_type == ReactEventType.FINAL:
            break
    
    print("\n2. Continuing the conversation with a follow-up question...")
    follow_up = "Now add 100 to that result."
    async for event in react_instance.chat_stream(follow_up):
        print(f"Event: {event.event_type}")
        print(f"Payload: {json.dumps(event.payload, indent=2)}")
        print("-" * 50)
        
        # Stop after the final response
        if event.event_type == ReactEventType.FINAL:
            break


if __name__ == "__main__":
    asyncio.run(main())