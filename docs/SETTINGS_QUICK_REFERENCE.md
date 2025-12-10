# Settings System - Quick Reference Guide

## For Developers

### Adding New Settings

To add new settings to the application, simply edit the `settings_template.yaml` file:

```yaml
groups:
  - name: my_new_group
    label: My New Settings
    icon: ""
    fields:
      - name: my_field
        label: My Setting
        type: text  # or number, boolean, select, color, slider
        default: "default value"
        description: Help text shown to users
        validation:  # Optional
          max_length: 100
```

### Using Settings in Code

```python
# Get settings instance
settings = workspace.get_settings()

# Read a setting
value = settings.get("group_name.field_name")
value_with_default = settings.get("group.field", "fallback_value")

# Update a setting
success = settings.set("group_name.field_name", new_value)

# Save changes to disk
settings.save()

# Reload from file (discard unsaved changes)
settings.reload()

# Reset all to defaults
settings.reset_to_defaults()
```

### Field Types Reference

| Type | Widget | Validation Options | Example |
|------|--------|-------------------|---------|
| `text` | Line edit | `min_length`, `max_length`, `pattern` | Username, path |
| `number` | Spin box | `min`, `max` | Thread count, timeout |
| `boolean` | Checkbox | None | Enable/disable flags |
| `select` | Dropdown | Defined by `options` array | Language, format |
| `color` | Color picker | `format: hex` | Theme color |
| `slider` | Slider | `min`, `max`, `step` | Quality, volume |

### Example: Adding a Theme Setting

1. Edit `app/data/settings_template.yaml`:

```yaml
groups:
  - name: appearance
    label: Appearance
    icon: ""
    fields:
      - name: theme
        label: Color Theme
        type: select
        default: dark
        description: Application color scheme
        options:
          - value: dark
            label: Dark Theme
          - value: light
            label: Light Theme
```

2. Use in your code:

```python
settings = workspace.get_settings()
theme = settings.get("appearance.theme")

if theme == "dark":
    apply_dark_theme()
else:
    apply_light_theme()
```

### Showing Settings UI

```python
from app.ui.settings import SettingsWidget

# Create settings widget
settings_widget = SettingsWidget(workspace)

# Show as dialog
settings_widget.show()

# Connect to settings changed signal
settings_widget.settings_changed.connect(on_settings_updated)
```

### Validation Examples

**Number with range:**
```yaml
validation:
  min: 1
  max: 100
```

**Text with length limit:**
```yaml
validation:
  min_length: 3
  max_length: 50
```

**Text with pattern:**
```yaml
validation:
  pattern: "^[a-zA-Z0-9_]+$"  # Alphanumeric and underscore only
```

**Slider with step:**
```yaml
validation:
  min: 0
  max: 100
  step: 5  # Values: 0, 5, 10, 15...
```

## For Users

### Accessing Settings

1. **Menu**: File → Settings (future implementation)
2. **Keyboard**: Cmd+, (Mac) or Ctrl+, (Windows) (future implementation)
3. **Via test script**: `python test_settings.py`

### Using the Settings Interface

**Header:**
- Title shows current status
- Search box for filtering settings (future)

**Tabs:**
- Click tabs to switch between setting groups
- Blue underline shows active tab

**Fields:**
- Each field has a label and input control
- Gray text below shows description
- Modified settings enable Save button

**Actions:**
- **Save**: Save changes to disk
- **Revert**: Discard unsaved changes
- **Reset to Default**: Restore all settings to defaults (requires confirmation)

### Understanding Field Types

- **Text boxes**: Type freely, subject to length limits
- **Number boxes**: Use arrows or type numbers
- **Checkboxes**: Click to toggle on/off
- **Dropdowns**: Click to see and select options
- **Color pickers**: Click to open color selector
- **Sliders**: Drag or click to set value

## Settings File Location

Settings are stored as YAML:
```
workspace_path/
└── settings.yaml
```

You can manually edit this file, but changes require app restart to take effect.

## Troubleshooting

**Settings not saving:**
- Check file permissions on workspace directory
- Verify settings.yaml is not read-only

**Invalid settings:**
- Settings widget shows validation errors
- Check constraints in settings_template.yaml

**Settings reset on startup:**
- Verify settings.yaml exists in workspace directory
- Check for errors in YAML syntax

**Missing settings:**
- App creates settings.yaml from template if missing
- Corrupted file is backed up and recreated

## Advanced: Custom Field Types

To add a custom field type:

1. Extend `FieldWidgetFactory` with new widget type
2. Add validation logic in `Settings._validate_*` method
3. Update factory mapping in `create_widget()`

Example for a file picker:
```python
@staticmethod
def _create_file_widget(field: SettingField, current_value: Any):
    container = QWidget()
    layout = QHBoxLayout(container)
    
    line_edit = QLineEdit(str(current_value))
    browse_btn = QPushButton("Browse...")
    browse_btn.clicked.connect(lambda: show_file_dialog(line_edit))
    
    layout.addWidget(line_edit)
    layout.addWidget(browse_btn)
    
    return container
```

## Best Practices

1. **Group related settings** together
2. **Use clear, descriptive labels**
3. **Provide helpful descriptions** for complex options
4. **Set sensible defaults** for new settings
5. **Validate input** to prevent invalid configurations
6. **Test settings changes** before committing
7. **Document new settings** in this guide
