# Prompt Input Component

## Overview

The Prompt Input Component is a reusable UI widget for the Filmeto application that provides an adaptive text input interface with template management capabilities. It follows the application's dark theme aesthetic and architectural patterns.

## Features

- **Adaptive Height Expansion**: Input field expands from single-line (40px) to multi-line (120px) on hover/focus
- **Character Counter**: Real-time character count display (appears on hover/focus)
- **Template Management**: Save, search, and reuse prompt templates
- **Template Filtering**: Real-time filtering with 300ms debounce
- **Keyboard Navigation**: Full keyboard support including Enter to submit, Ctrl+Enter for line break
- **Dark Theme Integration**: Consistent with Filmeto's dark theme
- **Signal-Based Architecture**: Qt signals for easy integration with parent widgets

## Component Structure

```
app/ui/prompt_input/
├── __init__.py                 # Package initialization
├── prompt_input_widget.py      # Main widget implementation
└── template_item_widget.py     # Template list item widget

app/data/
└── workspace.py                # Extended with PromptManager

workspace/{project_name}/
└── prompts/                    # Template storage directory
    ├── template_*.yaml         # Individual template files
    └── ...
```

## Usage

### Basic Usage

```python
from app.data.workspace import Workspace
from app.ui.prompt import CanvasPromptWidget

# Create workspace instance
workspace = Workspace("./workspace", "demo")

# Create prompt input widget
prompt_widget = CanvasPromptWidget(workspace)

# Connect to signals
prompt_widget.prompt_submitted.connect(on_prompt_submitted)
prompt_widget.prompt_changed.connect(on_prompt_changed)

# Add to your layout
layout.addWidget(prompt_widget)
```

### Signal Handling

```python
def on_prompt_submitted(prompt_text: str):
    """Handle submitted prompt"""
    print(f"Submitted: {prompt_text}")
    # Process the prompt
    # ...
    # Optionally clear the input
    prompt_widget.clear_prompt()

def on_prompt_changed(prompt_text: str):
    """Handle prompt text changes"""
    print(f"Current text: {prompt_text}")
```

### Public API

| Method/Signal | Type | Description |
|--------------|------|-------------|
| `set_placeholder(text)` | Method | Set input field placeholder text |
| `get_prompt_text()` | Method | Retrieve current prompt text |
| `clear_prompt()` | Method | Clear input field content |
| `prompt_submitted` | Signal | Emitted when send button clicked, passes prompt text |
| `prompt_changed` | Signal | Emitted when text changes, passes updated text |

## Template Management

### PromptManager API

```python
# Get prompt manager from workspace
prompt_manager = workspace.get_prompt_manager()

# Load all templates
templates = prompt_manager.load_templates()

# Add a new template
success = prompt_manager.add_template(
    icon_path="textures/icons/text.png",
    text="Generate a cinematic scene"
)

# Search templates
results = prompt_manager.search_templates("cinematic")

# Delete a template
prompt_manager.delete_template(template_id)

# Increment usage count
prompt_manager.increment_usage(template_id)
```

### Template Data Model

Templates are stored as YAML files with the following structure:

```yaml
id: "550e8400-e29b-41d4-a716-446655440000"
icon: "textures/prompt_icons/text.png"
text: "Generate a cinematic scene with dramatic lighting"
created_at: "2024-01-15T10:30:00"
usage_count: 5
```

## Component Behavior

### State Transitions

| State | Height | Counter | Trigger |
|-------|--------|---------|---------|
| Default | 40px | Hidden | No hover, no focus |
| Expanded | 120px | Visible | Mouse hover OR focus |
| Focused | 120px | Visible | Active text input |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit prompt |
| `Ctrl+Enter` | Insert line break |
| `Escape` | Close template dropdown |
| `Tab` | Move to send button |

### Template Filtering

- Automatic filtering as user types
- 300ms debounce delay
- Case-insensitive substring match
- Shows up to 10 matching results
- Dropdown appears below input field

## Styling

The component uses inline QSS styling for maximum flexibility:

### Color Palette

| Element | Background | Border | Text | Hover |
|---------|-----------|--------|------|-------|
| Input Field | `#2b2d30` | `#505254` | `#E1E1E1` | Border: `#4080ff` |
| Send Button | `#3d3f4e` | None | `#E1E1E1` | Bg: `#4080ff` |
| Character Counter | Transparent | None | `#888888` | N/A |
| Template Dropdown | `#2c2c2c` | `#505254` | `#E1E1E1` | N/A |
| Template Item | Transparent | None | `#E1E1E1` | Bg: `#3a3c3f` |
| Selected Template | `#4080ff` | None | `#FFFFFF` | N/A |

## Testing

Run the test file to see the component in action:

```bash
python test_prompt_input.py
```

The test window includes:
- Prompt input widget
- Status display
- Submitted prompt display
- Clear button
- Pre-populated test templates

## Integration Points

### Parent Widget Integration

Typical usage pattern:

1. Create `PromptInputWidget` instance
2. Connect to `prompt_submitted` signal
3. Handle submitted prompt text
4. Optionally clear prompt after processing

### Example: Task Creation Dialog

```python
class TaskCreationDialog(QDialog):
    def __init__(self, workspace: Workspace):
        super().__init__()
        
        # Create prompt input
        self.prompt_input = PromptInputWidget(workspace)
        self.prompt_input.prompt_submitted.connect(self._create_task)
        
        # Add to layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.prompt_input)
    
    def _create_task(self, prompt: str):
        # Submit task with prompt
        self.workspace.submit_task({
            'prompt': prompt,
            # ... other parameters
        })
        
        # Clear input
        self.prompt_input.clear_prompt()
```

## Performance Considerations

### Optimizations

- **Lazy Loading**: Templates loaded on first dropdown open
- **Debouncing**: 300ms delay before filtering on input
- **Caching**: In-memory template cache, reload on demand
- **Async Operations**: Qt signals for non-blocking updates

### Resource Limits

- Maximum templates: 500 (practical limit)
- Max prompt length: 10,000 characters (soft limit with warning)
- Icon file size: Maximum 100KB per icon
- Template text length: Maximum 2,000 characters

## Error Handling

The component handles common error scenarios:

- **Empty Input**: Shows warning message on submit
- **Duplicate Templates**: Prevents adding duplicates with error message
- **Invalid YAML**: Skips corrupted template files with console warning
- **Missing Icons**: Gracefully handles missing icon files
- **Long Text**: Shows warning color when text exceeds 10,000 characters

## Accessibility

### Features

- Placeholder text for empty state
- Tooltip on send button
- Visual feedback for all interactive elements
- Keyboard navigation support
- Clear focus indicators

### Best Practices

- Maintain minimum width of 200px
- Use high-contrast colors for text
- Provide clear visual states (hover, focus, selected)
- Support keyboard-only navigation

## Future Enhancements

Potential improvements not included in current implementation:

- [ ] Cloud synchronization of templates
- [ ] Template sharing between projects
- [ ] Template versioning and history
- [ ] Rich text formatting support
- [ ] Voice input integration
- [ ] Multi-language template support
- [ ] Template categories/tags
- [ ] Import/export templates

## Troubleshooting

### Common Issues

**Templates not appearing:**
- Check that `prompts/` directory exists in workspace
- Verify YAML files are properly formatted
- Ensure templates have all required fields

**Dropdown not showing:**
- Type at least one character to trigger filtering
- Check that templates match the search query
- Verify template cache is loaded

**Styling not applied:**
- Ensure QSS is properly set in component initialization
- Check for conflicting global stylesheets
- Verify object names match CSS selectors

## Dependencies

- PySide6 (Qt for Python)
- Python 3.8+
- PyYAML (for template storage)
- qasync (for async/await support in Qt)

## Internationalization (i18n)

The component fully supports internationalization through Qt's translation system.

### Translatable Strings

| UI Element | Translation Key | Default (English) |
|------------|----------------|-------------------|
| Placeholder | `Enter your prompt here...` | "Enter your prompt here..." |
| Character Counter | `{count} characters` | "{count} characters" |
| Send Button Tooltip | `Submit prompt` | "Submit prompt" |
| Empty Input Warning Title | `Empty Input` | "Empty Input" |
| Empty Input Warning Message | `Please enter a prompt` | "Please enter a prompt" |
| Initial Counter | `0 characters` | "0 characters" |

### Implementation

The component uses the `tr()` function from `utils.i18n_utils` for all user-facing strings and automatically updates when the language changes:

```python
from utils.i18n_utils import tr, translation_manager

# All UI text is wrapped in tr()
self.text_edit.setPlaceholderText(tr("Enter your prompt here..."))

# Component listens for language changes
translation_manager.language_changed.connect(self._update_ui_text)
```

### Dynamic Language Switching

The component supports dynamic language switching without restart:

```python
from utils.i18n_utils import translation_manager

# Switch language
translation_manager.switch_language("en_US")
# Component UI will automatically update
```

All translations are stored in `i18n/filmeto_en_US.ts` and other language files.

## License

Part of the Filmeto application. See main project license.

## Contributing

When modifying this component:

1. Maintain backward compatibility with existing API
2. Follow Qt naming conventions
3. Update tests for new features
4. Document all public methods
5. Preserve dark theme consistency
6. Test keyboard navigation thoroughly

## Contact

For questions or issues with this component, refer to the main Filmeto project documentation.
