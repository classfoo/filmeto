# Filmeto Project Guidelines

## Project Structure

The Filmeto project follows a well-defined structure to maintain organization and clarity across the codebase.

### Directory Organization

- `app/` - Main application code including UI components, data models, and business logic
- `tests/` - **ALL test files must be placed in this directory** - This includes unit tests, integration tests, and end-to-end tests
- `docs/` - **ALL documentation files must be placed in this directory** - This includes API documentation, architecture guides, and user manuals
- `agent/` - AI agent module and related components
- `server/` - Backend server implementations
- `utils/` - Utility functions and helpers
- `style/` - Styling assets and themes
- `textures/` - Texture and asset files

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
├── test_app/
│   ├── test_data/
│   ├── test_ui/
│   └── test_plugins/
├── test_agent/
└── test_utils/
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
4. **Code text should use English and be extracted to global internationalization files, providing both en_US and zh_CN language sets**
5. Maintain consistent naming conventions across all directories
6. Keep documentation up-to-date with code changes
7. Write meaningful test cases that cover edge cases and error conditions

Following these guidelines ensures a maintainable, scalable, and well-documented codebase.