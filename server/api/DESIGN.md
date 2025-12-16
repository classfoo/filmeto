# FilmetoApi Design Document

## Overview

FilmetoApi is a unified interface for calling various AI model services through a streaming API. It supports both web-based access and local in-app calls, with a plugin-based architecture for extensibility.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                        │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │   Web Client     │              │   App Client     │    │
│  │  (HTTP/SSE)      │              │   (Direct Call)  │    │
│  └────────┬─────────┘              └────────┬─────────┘    │
└───────────┼─────────────────────────────────┼──────────────┘
            │                                 │
            └────────────┬────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                   API Layer                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         FilmetoApi (server/api/filmeto_api.py)       │   │
│  │  - Task validation                                    │   │
│  │  - Resource handling (local/url/base64)              │   │
│  │  - Streaming interface                               │   │
│  └────────────────────┬─────────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                  Service Layer                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      FilmetoService (server/service/filmeto_service) │   │
│  │  - Task routing                                       │   │
│  │  - Plugin management                                  │   │
│  │  - Progress aggregation                              │   │
│  │  - Heartbeat management                              │   │
│  └────────────────────┬─────────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │ IPC (stdin/stdout JSON-RPC)
┌─────────────────────────┼───────────────────────────────────┐
│                  Plugin Layer (Separate Processes)           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────┐  │
│  │ Text2Image Plugin│  │ Image2Video Plugin│  │   ...    │  │
│  │  - requirements  │  │  - requirements    │  │          │  │
│  │  - main.py       │  │  - main.py         │  │          │  │
│  └──────────────────┘  └──────────────────┘  └──────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Data Structures

### 1. ToolType Enum

```python
class ToolType(str, Enum):
    TEXT2IMAGE = "text2image"      # Text to image generation
    IMAGE2IMAGE = "image2image"    # Image to image transformation
    IMAGE2VIDEO = "image2video"    # Image to video animation
    TEXT2VIDEO = "text2video"      # Text to video generation
    SPEAK2VIDEO = "speak2video"    # Speech to video (avatar)
    TEXT2SPEAK = "text2speak"      # Text to speech synthesis
    TEXT2MUSIC = "text2music"      # Text to music generation
```

### 2. ResourceInput

Support for multiple input formats:

```python
class ResourceType(str, Enum):
    LOCAL_PATH = "local_path"
    REMOTE_URL = "remote_url"
    BASE64 = "base64"

class ResourceInput:
    type: ResourceType
    data: str              # Path, URL, or base64 string
    mime_type: str         # e.g., "image/png", "video/mp4"
    metadata: Dict[str, Any]  # Optional metadata
```

### 3. FilmetoTask

```python
class FilmetoTask:
    task_id: str                    # Unique task identifier
    tool_name: ToolType             # Tool to execute
    plugin_name: str                # Server plugin name
    parameters: Dict[str, Any]      # Tool-specific parameters
    resources: List[ResourceInput]  # Input resources (images, videos, etc.)
    created_at: datetime
    timeout: int = 300              # Timeout in seconds
    metadata: Dict[str, Any] = {}   # Additional metadata
```

### 4. TaskProgress

Streaming progress updates:

```python
class ProgressType(str, Enum):
    STARTED = "started"
    PROGRESS = "progress"
    HEARTBEAT = "heartbeat"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskProgress:
    task_id: str
    type: ProgressType
    percent: float          # 0-100
    message: str            # Human-readable message
    timestamp: datetime
    data: Dict[str, Any]    # Additional progress data
```

### 5. TaskResult

Final result structure:

```python
class TaskResult:
    task_id: str
    status: str                    # "success" or "error"
    output_files: List[str]        # Generated file paths
    output_resources: List[ResourceOutput]  # Processed resources
    error_message: str = ""
    execution_time: float          # Seconds
    metadata: Dict[str, Any] = {}
    
class ResourceOutput:
    type: str                      # "image", "video", "audio"
    path: str                      # Local path to file
    url: Optional[str]             # Optional URL if uploaded
    mime_type: str
    size: int                      # File size in bytes
    metadata: Dict[str, Any]
```

## API Interface

### FilmetoApi Class

```python
class FilmetoApi:
    """
    Unified API interface for AI model services.
    Supports both web and local calls with streaming.
    """
    
    async def execute_task_stream(
        self, 
        task: FilmetoTask
    ) -> AsyncIterator[Union[TaskProgress, TaskResult]]:
        """
        Execute a task and stream progress updates.
        
        Yields:
            - TaskProgress: Progress updates during execution
            - TaskResult: Final result (last item)
        """
        pass
    
    def validate_task(self, task: FilmetoTask) -> bool:
        """Validate task structure and parameters"""
        pass
    
    async def process_resource(
        self, 
        resource: ResourceInput
    ) -> str:
        """
        Process resource input and return local file path.
        Handles download for URLs, decode for base64.
        """
        pass
```

## Plugin Architecture

### Plugin Structure

Each plugin is an independent Python project:

```
server/plugins/
└── text2image_comfyui/
    ├── requirements.txt          # Plugin dependencies
    ├── plugin.yaml              # Plugin metadata
    ├── main.py                  # Entry point
    ├── src/
    │   ├── __init__.py
    │   ├── generator.py         # Core logic
    │   └── config.py            # Configuration
    └── README.md
```

### Plugin Interface (JSON-RPC over stdin/stdout)

Plugins communicate via JSON-RPC protocol on stdin/stdout:

**Request Format:**
```json
{
    "jsonrpc": "2.0",
    "method": "execute_task",
    "params": {
        "task_id": "uuid",
        "tool_name": "text2image",
        "parameters": {...},
        "resources": [...]
    },
    "id": 1
}
```

**Progress Response:**
```json
{
    "jsonrpc": "2.0",
    "method": "progress",
    "params": {
        "task_id": "uuid",
        "type": "progress",
        "percent": 45.5,
        "message": "Generating image...",
        "timestamp": "2025-12-16T10:30:00Z"
    }
}
```

**Result Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "task_id": "uuid",
        "status": "success",
        "output_files": ["/path/to/image.png"],
        "execution_time": 12.5
    },
    "id": 1
}
```

### Plugin Base Class

```python
class BaseServerPlugin(ABC):
    """
    Base class for server plugins.
    Handles JSON-RPC communication and progress reporting.
    """
    
    @abstractmethod
    async def execute_task(
        self, 
        task_data: Dict[str, Any],
        progress_callback: Callable
    ) -> Dict[str, Any]:
        """Execute task and return result"""
        pass
    
    def report_progress(
        self, 
        task_id: str, 
        percent: float, 
        message: str
    ):
        """Report progress via stdout"""
        pass
    
    def run(self):
        """Main loop: read from stdin, execute, write to stdout"""
        pass
```

## Service Implementation

### FilmetoService

```python
class FilmetoService:
    """
    Service layer managing plugin lifecycle and task execution.
    """
    
    def __init__(self):
        self.plugins: Dict[str, PluginProcess] = {}
        self.heartbeat_interval = 5  # seconds
    
    async def execute_task_stream(
        self, 
        task: FilmetoTask
    ) -> AsyncIterator[Union[TaskProgress, TaskResult]]:
        """
        Execute task through appropriate plugin with streaming.
        """
        # 1. Get or start plugin process
        plugin = await self.get_plugin(task.plugin_name)
        
        # 2. Send task to plugin
        await plugin.send_task(task)
        
        # 3. Stream progress and heartbeats
        async for message in plugin.receive_messages():
            if message.type == "progress":
                yield TaskProgress(**message.data)
            elif message.type == "result":
                yield TaskResult(**message.data)
                break
    
    async def get_plugin(self, plugin_name: str) -> PluginProcess:
        """Get or start plugin process"""
        pass
    
    async def start_plugin(self, plugin_name: str) -> PluginProcess:
        """Start plugin in separate process"""
        pass
    
    async def stop_plugin(self, plugin_name: str):
        """Stop plugin process"""
        pass
```

### PluginProcess

```python
class PluginProcess:
    """
    Manages a single plugin process and communication.
    """
    
    def __init__(self, plugin_name: str, plugin_path: str):
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def start(self):
        """Start the plugin process"""
        # 1. Load plugin.yaml for config
        # 2. Create virtual environment if needed
        # 3. Install requirements
        # 4. Start process with python main.py
        pass
    
    async def send_task(self, task: FilmetoTask):
        """Send task to plugin via stdin"""
        pass
    
    async def receive_messages(
        self
    ) -> AsyncIterator[Dict[str, Any]]:
        """Receive messages from plugin stdout"""
        pass
    
    async def stop(self):
        """Stop the plugin process"""
        pass
```

## Web API Layer

### REST Endpoints

```python
# FastAPI implementation
@app.post("/api/v1/tasks")
async def create_task(task: FilmetoTask) -> TaskResponse:
    """Create and start a new task"""
    pass

@app.get("/api/v1/tasks/{task_id}/stream")
async def stream_task(task_id: str):
    """Stream task progress (SSE)"""
    # Server-Sent Events
    async def event_generator():
        async for update in api.execute_task_stream(task):
            yield f"data: {json.dumps(update)}\n\n"
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream"
    )

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    """Get current task status"""
    pass

@app.get("/api/v1/tools")
async def list_tools() -> List[ToolInfo]:
    """List available tools"""
    pass

@app.get("/api/v1/plugins")
async def list_plugins() -> List[PluginInfo]:
    """List available plugins"""
    pass
```

## Heartbeat Mechanism

To keep streaming connections alive:

1. **Server-side**: FilmetoService sends heartbeat every 5 seconds
2. **Plugin-side**: Plugins can send heartbeat messages
3. **Client-side**: Clients should expect heartbeat and handle connection timeout

```python
class TaskProgress:
    type: ProgressType  # Can be HEARTBEAT
    
# Heartbeat message
{
    "task_id": "uuid",
    "type": "heartbeat",
    "timestamp": "2025-12-16T10:30:00Z"
}
```

## Error Handling

### Error Types

```python
class TaskError(Exception):
    code: str
    message: str
    details: Dict[str, Any]

class ValidationError(TaskError):
    code = "VALIDATION_ERROR"

class PluginNotFoundError(TaskError):
    code = "PLUGIN_NOT_FOUND"

class PluginExecutionError(TaskError):
    code = "PLUGIN_EXECUTION_ERROR"

class ResourceProcessingError(TaskError):
    code = "RESOURCE_PROCESSING_ERROR"

class TimeoutError(TaskError):
    code = "TIMEOUT_ERROR"
```

## Testing Strategy

### Unit Tests
- Task validation
- Resource processing (local/url/base64)
- Plugin communication protocol
- Progress streaming
- Error handling

### Integration Tests
- End-to-end task execution
- Plugin lifecycle management
- Web API endpoints
- Timeout handling

### Plugin Tests
- Mock plugin implementation
- Plugin base class functionality
- JSON-RPC communication

## Implementation Plan

### Phase 1: Core Structures
1. Define enums and data classes
2. Implement FilmetoTask, TaskProgress, TaskResult
3. Resource processing utilities

### Phase 2: Plugin Architecture
1. Plugin base class with JSON-RPC
2. Plugin process manager
3. Plugin discovery and loading

### Phase 3: Service Layer
1. FilmetoService implementation
2. Task routing and execution
3. Progress streaming and heartbeat

### Phase 4: API Layer
1. FilmetoApi interface
2. Web endpoints with FastAPI
3. SSE streaming support

### Phase 5: Example Plugin
1. Create text2image example plugin
2. Implement full workflow
3. Documentation

### Phase 6: Testing
1. Unit tests for all components
2. Integration tests
3. Example plugin tests

## Security Considerations

1. **Resource Validation**: Validate all file paths and URLs
2. **File Size Limits**: Enforce limits on uploaded resources
3. **Process Isolation**: Plugins run in separate processes
4. **Timeout Protection**: All tasks have configurable timeouts
5. **Input Sanitization**: Sanitize all user inputs
6. **API Authentication**: Support for API keys/tokens (future)

## Performance Considerations

1. **Async I/O**: All I/O operations are async
2. **Plugin Pooling**: Reuse plugin processes when possible
3. **Resource Caching**: Cache downloaded resources
4. **Streaming**: Stream results immediately, no buffering
5. **Lazy Plugin Loading**: Start plugins only when needed

## Configuration

### Plugin Configuration (plugin.yaml)

```yaml
name: text2image_comfyui
version: 1.0.0
description: Text to image generation using ComfyUI
author: Filmeto Team

tool_type: text2image
engine: comfyui

requirements:
  python: ">=3.9"
  packages:
    - torch>=2.0.0
    - pillow>=9.0.0

parameters:
  - name: prompt
    type: string
    required: true
    description: Text prompt for generation
  
  - name: negative_prompt
    type: string
    required: false
    default: ""
  
  - name: width
    type: integer
    required: false
    default: 512
    min: 256
    max: 2048
  
  - name: height
    type: integer
    required: false
    default: 512
    min: 256
    max: 2048

startup:
  timeout: 60  # seconds
  health_check: true

execution:
  timeout: 300  # seconds
  max_retries: 3
```

## Future Enhancements

1. Plugin marketplace and versioning
2. Distributed task execution
3. Result caching and deduplication
4. Real-time collaboration
5. Advanced monitoring and logging
6. Auto-scaling based on load
7. GPU resource management
8. Priority queue for tasks

