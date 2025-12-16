# Filmeto - AI-Powered Video and Image Editing Application

## Project Overview

Filmeto is a comprehensive desktop application for AI-powered video and image editing. The application features a modern PySide6-based UI with support for AI-generated content, timeline editing, canvas drawing, and multi-layer composition. It supports various AI models for text-to-image, image-to-video, and other generative tasks.

### Key Features
- Multi-layer canvas editing with drawing tools
- Timeline-based video editing with subtitle and voiceover tracks
- AI-powered content generation with support for multiple models
- Dynamic plugin system for tools
- Internationalization support with multiple languages
- Project and task management system
- Export functionality for final videos

### Tech Stack
- **UI Framework**: PySide6
- **Async Handling**: qasync for asyncio integration
- **AI/ML**: diffusers, modelscope, dashscope for AI model integration
- **Media Processing**: opencv-python for image/video processing
- **Networking**: websockets, custom server implementation
- **Data Format**: YAML for configuration files
- **Internationalization**: Custom i18n utilities

## Project Structure

```
filmeto/
├── app/                    # Main application code
│   ├── data/              # Data models (project, timeline, tasks, layers)
│   ├── plugins/           # Plugin system and tools
│   ├── spi/               # Service provider interfaces
│   └── ui/                # UI components and widgets
├── server/                # Backend server (currently minimal)
├── test/                  # Test files
├── utils/                 # Utility functions
├── docs/                  # Documentation
├── style/                 # Style sheets (QSS)
├── textures/              # Textures and assets
└── i18n/                  # Internationalization files
```

### Key Components

#### App Layer
- `app/app.py`: Main application class that initializes the Qt application, loads styles and fonts
- `app/ui/main_window.py`: Main window with top bar, left/right bars, workspace areas, and timeline
- `app/data/workspace.py`: Workspace management with project, tasks, and timeline handling
- `app/ui/editor/tool_editor.py`: Dynamic tool loading editor widget for AI tools

#### UI Components
- `app/ui/canvas/canvas_editor.py`: Canvas editor with drawing tools and layer management
- `app/ui/timeline/`: Timeline components with horizontal timeline and container
- `app/ui/layers/layers_widget.py`: Layer management widget
- `app/ui/task_list/`: Task list management for AI processing
- `app/ui/prompt_input/`: Prompt input widget for AI generation

#### Data Models
- `app/data/project.py`: Project management with timeline and configuration
- `app/data/timeline.py`: Timeline model with timeline items and frame management
- `app/data/layer.py`: Layer model with image and text layers
- `app/data/task.py`: Task management for AI processing jobs

#### Utilities
- `utils/i18n_utils.py`: Internationalization system with language switching
- `utils/ffmpeg_utils.py`: Video processing with FFmpeg
- `utils/yaml_utils.py`: YAML configuration handling
- `utils/queue_utils.py`: Async queue utilities for task processing

## Building and Running

### Prerequisites
- Python 3.8 or higher
- Pip package manager

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd filmeto

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
python main.py
```

### Testing
The project has various test files in both the root and test directories:
```bash
# Run specific test file
python test_canvas_drawing.py

# Run tests with pytest
python -m pytest test/ -v
```

## Development Conventions

### UI Development
- All UI components inherit from `BaseWidget` to ensure consistent workspace access
- Custom styling is applied through QSS (Qt Style Sheets) similar to CSS
- Internationalization is handled through the translation manager using `tr()` function
- Asynchronous operations use the qasync integration for asyncio compatibility

### Data Flow
1. Workspace manages projects and tasks
2. Projects contain timelines with timeline items
3. Timeline items contain layers
4. Canvas editor displays and manipulates layers
5. Tasks handle AI processing and update timeline items
6. Use blinker signals for communication between datas and ui

### Plugin System
- Tools are dynamically loaded from the plugins directory
- Tools implement the BaseTool interface
- The ToolEditorWidget manages dynamic tool loading and execution

### Canvas and Drawing
- The canvas system supports multiple layers with transparency
- Drawing modes include brush, eraser, and selection
- Layers can be managed through the layers widget
- The canvas supports scaling and panning for better editing experience

## Key Files and Classes

- `main.py`: Entry point that initializes the application and main window
- `app/app.py`: Main application class responsible for Qt application setup
- `app/ui/main_window.py`: Main application window with all UI components
- `app/data/workspace.py`: Core data management for projects, tasks, and timeline
- `app/ui/canvas/canvas_editor.py`: Canvas editing functionality with drawing tools
- `app/ui/editor/tool_editor.py`: Dynamic tool loading for AI processing
- `utils/i18n_utils.py`: Internationalization system

## Architecture Notes

- The application follows a component-based architecture with clear separation between UI, data, and business logic
- All UI components have access to the workspace for consistent state management
- The canvas editor supports multi-layer editing with transparent layer widgets
- The timeline system supports multiple tracks (video, subtitle, voiceover)
- AI processing is handled through an asynchronous task system
- The plugin system allows for dynamic tool loading and extension