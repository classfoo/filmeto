# Filmeto Agent Module

AI Agent system with LangGraph integration for intelligent video creation assistance.

## Quick Start

```python
from agent import FilmetoAgent

# Initialize agent
agent = FilmetoAgent(
    workspace=workspace,
    project=project,
    model="gpt-4o-mini",
    streaming=True
)

# Chat with agent
response = await agent.chat("What characters are in my project?")

# Stream response
async for token in agent.chat_stream("Create a video scene"):
    print(token, end='')
```

## Features

- 🤖 **LangGraph Integration**: Sophisticated multi-node workflow
- 💬 **Streaming Responses**: Real-time token-by-token output
- 🛠️ **Tool System**: Extensible tool registry with built-in tools
- 📝 **Conversation Management**: Persistent conversation history
- 🎯 **Smart Routing**: Coordinator, planner, executor, and responder nodes
- 🔧 **Project Integration**: Direct access to Filmeto project resources

## Architecture

```
User Input
    ↓
Coordinator (decides next action)
    ↓
[Tools] [Planner] [Direct Response]
    ↓
Response to User
```

## Built-in Tools

- `get_project_info` - Get current project details
- `list_characters` - List all characters
- `get_character_info` - Get character details
- `list_resources` - List project resources
- `get_timeline_info` - Get timeline state
- `create_task` - Create AI generation tasks

## Conversation Storage

Conversations are stored per-project:

```
project/
└── agent/
    ├── conversations_index.yaml
    └── conversations/
        └── conv_*.json
```

## Custom Tools

Create custom tools by extending `FilmetoBaseTool`:

```python
from agent.tools import FilmetoBaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(description="Parameter description")

class MyTool(FilmetoBaseTool):
    name: str = "my_tool"
    description: str = "Tool description"
    args_schema: type[BaseModel] = MyToolInput
    
    def _run(self, param: str) -> str:
        return f"Result: {param}"

# Register
agent.tool_registry.register_tool(MyTool(workspace=ws, project=proj))
```

## UI Integration

The agent is integrated with `AgentPanel` for seamless UI interaction:

- Real-time streaming display
- Chat history with scrolling
- Multi-line input with auto-resize
- Error handling and status updates

## Configuration

Set OpenAI API key in workspace settings:

```yaml
# workspace/settings.yaml
openai_api_key: "sk-..."
```

Or pass directly:

```python
agent = FilmetoAgent(
    workspace=workspace,
    project=project,
    api_key="your-key"
)
```

## Examples

See `examples/example_agent_usage.py` for comprehensive examples.

## Documentation

Full documentation: `docs/AGENT_MODULE_IMPLEMENTATION.md`

## Dependencies

- langgraph==1.0.5
- langchain>=1.0.0,<2.0.0
- langchain-core>=1.0.0,<2.0.0
- langchain-openai>=1.0.0,<2.0.0

