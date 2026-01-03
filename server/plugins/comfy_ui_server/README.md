# Text2Image Demo Plugin

A simple demonstration plugin for the Filmeto API that generates placeholder images with text.

## Description

This plugin demonstrates how to create a server-side plugin for Filmeto. It generates colored gradient images with the prompt text rendered on them, simulating the behavior of a real text-to-image AI model.

## Features

- Generates colorful gradient images
- Renders prompt text on the image
- Simulates multi-step generation process
- Reports progress during execution
- Supports custom width, height, and steps

## Requirements

- Python >= 3.9
- Pillow >= 9.0.0

## Installation

The plugin dependencies are automatically installed when the plugin is first used.

Alternatively, you can manually install:

```bash
cd server/plugins/text2image_demo
pip install -r requirements.txt
```

## Parameters

- `prompt` (string, required): Text prompt for generation
- `negative_prompt` (string, optional): Negative prompt (not used in demo)
- `width` (integer, optional): Image width (default: 512, range: 256-2048)
- `height` (integer, optional): Image height (default: 512, range: 256-2048)
- `steps` (integer, optional): Number of generation steps (default: 20, range: 1-100)

## Usage

### Via Python API

```python
from server.api.filmeto_api import FilmetoApi
from server.api.types import FilmetoTask, ToolType

api = FilmetoApi()

task = FilmetoTask(
    tool_name=ToolType.TEXT2IMAGE,
    plugin_name="text2image_demo",
    parameters={
        "prompt": "A beautiful sunset over mountains",
        "width": 768,
        "height": 512,
        "steps": 20
    }
)

async for update in api.execute_task_stream(task):
    if isinstance(update, TaskProgress):
        print(f"Progress: {update.percent}% - {update.message}")
    elif isinstance(update, TaskResult):
        print(f"Generated: {update.output_files}")
```

### Via Web API

```bash
curl -X POST http://localhost:8000/api/v1/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "text2image",
    "plugin_name": "text2image_demo",
    "parameters": {
      "prompt": "A beautiful sunset",
      "width": 512,
      "height": 512
    }
  }'
```

## Output

Generated images and videos are temporarily saved to a system temporary directory and then copied to the project's resources directory. The temporary files are managed by the system and will be automatically cleaned up.

## Testing

You can test the plugin directly:

```bash
cd server/plugins/text2image_demo
python main.py
```

Then send a test request via stdin:

```json
{"jsonrpc": "2.0", "method": "execute_task", "params": {"task_id": "test123", "tool_name": "text2image", "parameters": {"prompt": "test", "width": 512, "height": 512}}, "id": 1}
```

## Creating Your Own Plugin

This demo plugin serves as a template for creating your own plugins:

1. Copy the plugin directory structure
2. Update `plugin.yaml` with your plugin metadata
3. Implement the `execute_task` method in your main plugin class
4. Use `progress_callback` to report progress
5. Return results in the standard format

See the base plugin class in `server/plugins/base_plugin.py` for more details.

