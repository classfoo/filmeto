# Filmeto Agent Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Filmeto Application                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                     AgentPanel (UI)                     │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │         ChatHistoryWidget                     │     │    │
│  │  │  - Display messages                           │     │    │
│  │  │  - Streaming updates                          │     │    │
│  │  │  - Scroll management                          │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │      AgentPromptWidget                   │     │    │
│  │  │  - Multi-line input                           │     │    │
│  │  │  - Auto-resize                                │     │    │
│  │  │  - Send button                                │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  │                                                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            │ Qt Signals                          │
│                            ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                   FilmetoAgent                          │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                          │    │
│  │  • Streaming chat interface                             │    │
│  │  • Conversation management                              │    │
│  │  • Context management                                   │    │
│  │  • Tool registry integration                            │    │
│  │                                                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
```

## LangGraph Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph State Machine                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│                      ┌──────────────┐                           │
│                      │  User Input  │                           │
│                      └──────┬───────┘                           │
│                             │                                     │
│                             ▼                                     │
│                   ┌─────────────────┐                           │
│              ┌────│  Coordinator    │────┐                      │
│              │    │   (分析请求)     │    │                      │
│              │    └─────────────────┘    │                      │
│              │                            │                      │
│              ▼                            ▼                      │
│     ┌────────────────┐          ┌────────────────┐             │
│     │    Planner     │          │   Use Tools    │             │
│     │   (创建计划)    │          │  (执行工具)     │             │
│     └────────┬───────┘          └────────┬───────┘             │
│              │                            │                      │
│              └──────────┬─────────────────┘                      │
│                         │                                        │
│                         ▼                                        │
│                ┌────────────────┐                               │
│                │    Executor    │                               │
│                │  (执行步骤)     │                               │
│                └────────┬───────┘                               │
│                         │                                        │
│                         ▼                                        │
│                ┌────────────────┐                               │
│                │   Responder    │                               │
│                │  (生成响应)     │                               │
│                └────────┬───────┘                               │
│                         │                                        │
│                         ▼                                        │
│                  ┌─────────────┐                                │
│                  │   Response  │                                │
│                  └─────────────┘                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Tool System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Tool Registry                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   FilmetoBaseTool                         │  │
│  │                   (Base Class)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│          ┌──────────────────┼──────────────────┐               │
│          │                  │                  │               │
│          ▼                  ▼                  ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Project    │  │  Character   │  │   Resource   │        │
│  │    Tools     │  │    Tools     │  │    Tools     │        │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤        │
│  │• get_project │  │• list_chars  │  │• list_res    │        │
│  │  _info       │  │• get_char    │  │              │        │
│  │• get_timeline│  │  _info       │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                   │
│          ┌──────────────────┬──────────────────┐               │
│          │                  │                  │               │
│          ▼                  ▼                  ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Timeline   │  │     Task     │  │    Custom    │        │
│  │    Tools     │  │    Tools     │  │    Tools     │        │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤        │
│  │• get_timeline│  │• create_task │  │• user_defined│        │
│  │  _info       │  │              │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Flow                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User Input                                                      │
│      │                                                            │
│      ▼                                                            │
│  ┌─────────────┐                                                │
│  │ AgentPanel  │                                                │
│  └──────┬──────┘                                                │
│         │                                                         │
│         │ message_submitted signal                               │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────┐                                           │
│  │  FilmetoAgent    │                                           │
│  │  .chat_stream()  │                                           │
│  └──────┬───────────┘                                           │
│         │                                                         │
│         │ async stream                                           │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────┐                                           │
│  │  LangGraph       │                                           │
│  │  Workflow        │                                           │
│  └──────┬───────────┘                                           │
│         │                                                         │
│         │ tool calls                                             │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────┐                                           │
│  │  Tool Registry   │                                           │
│  │  Execute Tools   │                                           │
│  └──────┬───────────┘                                           │
│         │                                                         │
│         │ tool results                                           │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────┐                                           │
│  │  LLM Response    │                                           │
│  │  (streaming)     │                                           │
│  └──────┬───────────┘                                           │
│         │                                                         │
│         │ tokens                                                 │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────┐                                           │
│  │  Qt Signals      │                                           │
│  │  (response_token)│                                           │
│  └──────┬───────────┘                                           │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────┐                                           │
│  │ ChatHistoryWidget│                                           │
│  │ (update display) │                                           │
│  └──────────────────┘                                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Conversation Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                    Conversation Storage                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Workspace                                                       │
│  └── project/                                                    │
│      ├── agent/                                                  │
│      │   ├── conversations_index.yaml                           │
│      │   │   ├── conversations: []                              │
│      │   │   │   ├── conversation_id                            │
│      │   │   │   ├── title                                      │
│      │   │   │   ├── created_at                                 │
│      │   │   │   └── updated_at                                 │
│      │   │                                                       │
│      │   └── conversations/                                     │
│      │       ├── conv_20260104_120000.json                      │
│      │       │   ├── conversation_id                            │
│      │       │   ├── title                                      │
│      │       │   ├── created_at                                 │
│      │       │   ├── updated_at                                 │
│      │       │   ├── messages: []                               │
│      │       │   │   ├── role (user/assistant/system/tool)     │
│      │       │   │   ├── content                                │
│      │       │   │   ├── timestamp                              │
│      │       │   │   └── metadata                               │
│      │       │   └── metadata                                   │
│      │       │                                                   │
│      │       └── conv_20260104_130000.json                      │
│      │                                                           │
│      ├── characters/                                            │
│      ├── resources/                                             │
│      ├── tasks/                                                 │
│      └── timeline/                                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Component Interaction                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   Workspace  │◄────────│   Project    │                     │
│  └──────┬───────┘         └──────┬───────┘                     │
│         │                         │                              │
│         │                         │                              │
│         ▼                         ▼                              │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ FilmetoAgent │◄────────│Conversation  │                     │
│  │              │         │  Manager     │                     │
│  └──────┬───────┘         └──────────────┘                     │
│         │                                                        │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ ToolRegistry │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   Project    │────────►│  Character   │                     │
│  │   Tools      │         │   Manager    │                     │
│  └──────────────┘         └──────────────┘                     │
│         │                                                        │
│         │                 ┌──────────────┐                     │
│         └────────────────►│   Resource   │                     │
│                           │   Manager    │                     │
│                           └──────────────┘                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                      AgentState Structure                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  AgentState (TypedDict)                                          │
│  ├── messages: Sequence[BaseMessage]                            │
│  │   ├── HumanMessage                                           │
│  │   ├── AIMessage                                              │
│  │   ├── SystemMessage                                          │
│  │   └── ToolMessage                                            │
│  │                                                               │
│  ├── next_action: str                                           │
│  │   ├── "use_tools"                                            │
│  │   ├── "respond"                                              │
│  │   ├── "plan"                                                 │
│  │   ├── "execute_plan"                                         │
│  │   └── "end"                                                  │
│  │                                                               │
│  ├── context: Dict[str, Any]                                    │
│  │   ├── plan: str (optional)                                   │
│  │   ├── tool_results: List (optional)                          │
│  │   └── custom_data: Any (optional)                            │
│  │                                                               │
│  └── iteration_count: int                                       │
│      └── (防止无限循环，最大10次)                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Streaming Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streaming Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User types message                                              │
│         │                                                         │
│         ▼                                                         │
│  [Send Button Click]                                            │
│         │                                                         │
│         ▼                                                         │
│  message_submitted signal                                        │
│         │                                                         │
│         ▼                                                         │
│  _on_message_submitted()                                        │
│         │                                                         │
│         ├─► Disable input                                       │
│         ├─► Add user message to UI                              │
│         └─► Start streaming message                             │
│                  │                                               │
│                  ▼                                               │
│         asyncio.create_task(_stream_response)                   │
│                  │                                               │
│                  ▼                                               │
│         agent.chat_stream()                                     │
│                  │                                               │
│                  ├─► LangGraph workflow                         │
│                  │                                               │
│                  └─► async for token:                           │
│                       │                                          │
│                       ├─► response_token_received.emit(token)   │
│                       │        │                                 │
│                       │        ▼                                 │
│                       │   _on_token_received()                  │
│                       │        │                                 │
│                       │        ├─► Accumulate response          │
│                       │        └─► Update UI (streaming)        │
│                       │                                          │
│                       └─► on_complete:                          │
│                                │                                 │
│                                ▼                                 │
│                       response_complete.emit(response)          │
│                                │                                 │
│                                ▼                                 │
│                       _on_response_complete()                   │
│                                │                                 │
│                                ├─► Final UI update              │
│                                └─► Re-enable input              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Legend

- `┌─┐` : Component boundary
- `│ │` : Vertical connection
- `─`   : Horizontal connection
- `▼`   : Data flow direction
- `◄─►` : Bidirectional communication
- `├─┤` : Branch/split
- `└─┘` : End of branch

## Notes

1. **Async Architecture**: All agent operations are asynchronous
2. **Qt Integration**: Uses Qt signals for thread-safe UI updates
3. **LangGraph**: Provides state machine workflow
4. **Tool System**: Extensible and modular
5. **Streaming**: Real-time token-by-token display
6. **Persistence**: Conversations saved to disk per project

