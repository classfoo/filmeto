# Filmeto Project Guidelines

## Project Structure

The Filmeto project follows a well-defined structure to maintain organization and clarity across the codebase.

### Directory Organization

```
filmeto/
├── agent/           # AI agent module with chat, crew, llm, plan, prompt, react, skill, soul, tool
├── app/             # Main application code (config, data, plugins, spi, ui)
├── bin/             # Executable scripts and binaries
├── docs/            # **ALL documentation files must be placed here**
├── examples/        # Example code and demonstrations
├── i18n/            # Internationalization files (en_US, zh_CN)
├── server/          # Backend server implementations (api, plugins, service)
├── style/           # QSS styling files (dark_style.qss, light_style.qss)
├── tests/           # **ALL test files must be placed here**
├── textures/        # Texture and asset files
├── utils/           # Utility functions and helpers
└── workspace/       # Working directory for projects and demos
```

### Detailed Subdirectories

#### agent/ - AI Agent Module
- `chat/` - Chat functionality and conversation handling
- `crew/` - Crew management and orchestration
- `llm/` - Large Language Model integrations
- `plan/` - Planning and execution logic
- `prompt/` - Prompt templates and management
- `react/` - ReAct (Reasoning + Acting) framework
- `skill/` - Skill definitions and implementations
- `soul/` - Agent personality and soul traits
- `tool/` - Tool definitions and integrations

#### app/ - Main Application
- `config/` - Application configuration
- `data/` - Data models and storage
- `plugins/` - Application plugins
- `spi/` - Service Provider Interface
- `ui/` - User interface components

#### server/ - Backend Server
- `api/` - API endpoints
- `plugins/` - Server plugins
- `service/` - Business logic services

#### tests/ - Test Suite
- `react/` - React framework tests
- Test files should mirror the source structure

#### utils/ - Utilities
- `async_queue_utils.py` - Async queue utilities
- `comfy_ui_utils.py` - ComfyUI integration
- `download_utils.py` - Download handling
- `ffmpeg_utils.py` - FFmpeg operations
- `i18n_utils.py` - Internationalization helpers
- `plan_service.py` - Planning service
- `queue_utils.py` - Queue management
- `signal_utils.py` - Qt signal utilities
- `thread_utils.py` - Threading helpers

## Testing Guidelines

### Test File Placement
**CRITICAL: All test files must be placed in the `tests/` directory.** This ensures:

- Consistent location for all test assets
- Easier CI/CD pipeline configuration
- Better project maintainability
- Clear separation between production and test code

### Test Organization
Tests should be organized in subdirectories mirroring the structure of the code being tested:
```
tests/
├── test_app/        # Application tests
├── test_agent/      # Agent module tests
├── test_server/     # Server tests
└── react/           # React framework tests (existing)
```

## Documentation Guidelines

### Documentation File Placement
**CRITICAL: All documentation files must be placed in the `docs/` directory.** This ensures:

- Centralized location for all project documentation
- Consistent access patterns for developers and users
- Proper versioning alongside code changes
- Separation of concerns between code and documentation

### Documentation Types
The docs directory should contain:
- Architecture documentation
- API references
- User guides
- Developer guides
- Release notes
- Contribution guidelines

## Best Practices

1. **Always place new test files in the `tests/` directory**
2. **Always place new documentation files in the `docs/` directory**
3. **Component styles must be defined in global style files (dark_style.qss and light_style.qss) to ensure components can switch between different themes**
4. **Code text should use English and be extracted to global internationalization files (i18n/), providing both en_US and zh_CN language sets**
5. Maintain consistent naming conventions across all directories
6. Keep documentation up-to-date with code changes
7. Write meaningful test cases that cover edge cases and error conditions
8. Use existing utilities from `utils/` before creating new ones
9. Follow the existing module structure when adding new features

Following these guidelines ensures a maintainable, scalable, and well-documented codebase.
