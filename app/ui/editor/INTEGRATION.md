# Integration Guide - EditorWidget

This guide shows how to integrate `EditorWidget` into the Filmeto main application.

## Quick Integration

### Step 1: Import the Component

```python
# In app/ui/main_window.py or wherever you build your UI
from app.ui.editor import EditorWidget
```

### Step 2: Add to Main Window

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ... existing setup ...
        
        # Create editor widget
        self.editor = EditorWidget(self.workspace)
        
        # Add to your layout
        # Option A: As central widget
        self.setCentralWidget(self.editor)
        
        # Option B: In a tab widget
        self.tabs.addTab(self.editor, "Editor")
        
        # Option C: In a dock widget
        dock = QDockWidget("Editor", self)
        dock.setWidget(self.editor)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
```

### Step 3: Connect to Application Logic

```python
# Connect editor signals to your application handlers
self.editor.mode_changed.connect(self.on_editor_mode_changed)
self.editor.prompt_submitted.connect(self.on_prompt_submitted)

def on_editor_mode_changed(self, mode: str):
    """Handle mode change in your app"""
    print(f"Editor mode changed to: {mode}")
    # Update UI, save preferences, etc.

def on_prompt_submitted(self, mode: str, prompt: str):
    """Process AI generation request"""
    # Create and execute AI task based on mode
    if mode == EditorWidget.MODE_TEXT_TO_IMAGE:
        self.generate_image(prompt)
    elif mode == EditorWidget.MODE_IMAGE_TO_VIDEO:
        self.generate_video(prompt)
    # ... etc.
```

## Full Example Integration

```python
# app/ui/main_window.py (simplified example)

from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Slot

from app.ui.editor import EditorWidget
from app.ui.timeline import TimelineWidget
from app.ui.task_list import TaskListWidget
from app.data.workspace import Workspace


class FilmetoMainWindow(QMainWindow):
    """Main application window with integrated editor"""
    
    def __init__(self, workspace: Workspace):
        super().__init__()
        self.workspace = workspace
        self.setWindowTitle("Filmeto - AI Video Editor")
        self.resize(1600, 900)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup main window UI"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main splitter (horizontal)
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Task list (20%)
        self.task_list = TaskListWidget(self.workspace)
        self.task_list.setMinimumWidth(250)
        
        # Center: Editor (60%)
        self.editor = EditorWidget(self.workspace)
        
        # Right: Properties panel (20%)
        self.properties_panel = self._create_properties_panel()
        
        # Add to splitter
        main_splitter.addWidget(self.task_list)
        main_splitter.addWidget(self.editor)
        main_splitter.addWidget(self.properties_panel)
        
        # Set stretch factors
        main_splitter.setStretchFactor(0, 2)  # Task list
        main_splitter.setStretchFactor(1, 6)  # Editor (largest)
        main_splitter.setStretchFactor(2, 2)  # Properties
        
        # Bottom: Timeline
        self.timeline = TimelineWidget(self.workspace)
        self.timeline.setFixedHeight(200)
        
        # Add to main layout
        main_layout.addWidget(main_splitter, 1)  # Editor area takes most space
        main_layout.addWidget(self.timeline)     # Timeline at bottom
    
    def _create_properties_panel(self):
        """Create properties/settings panel"""
        from PySide6.QtWidgets import QFrame, QLabel
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Properties"))
        # Add property controls here
        return panel
    
    def _connect_signals(self):
        """Connect all component signals"""
        # Editor signals
        self.editor.mode_changed.connect(self._on_mode_changed)
        self.editor.prompt_submitted.connect(self._on_prompt_submitted)
        
        # Timeline signals
        self.timeline.item_selected.connect(self._on_timeline_selected)
        
        # Task list signals
        self.task_list.task_clicked.connect(self._on_task_clicked)
    
    @Slot(str)
    def _on_mode_changed(self, mode: str):
        """Handle editor mode change"""
        print(f"Mode changed: {mode}")
        # Update properties panel based on mode
        self._update_properties_for_mode(mode)
    
    @Slot(str, str)
    def _on_prompt_submitted(self, mode: str, prompt: str):
        """Handle prompt submission - create AI task"""
        print(f"Creating task: {mode} with prompt: {prompt}")
        
        # Set editor to processing state
        self.editor.set_processing(True)
        
        # Create task based on mode
        task = self._create_task(mode, prompt)
        
        # Add to task queue
        self.workspace.add_task(task)
        
        # Task will complete async and trigger on_task_finished
    
    def _on_timeline_selected(self, item):
        """Handle timeline item selection"""
        # Preview widget will auto-update via workspace signals
        pass
    
    def _on_task_clicked(self, task):
        """Handle task list item click"""
        # Show task details in properties panel
        pass
    
    def _create_task(self, mode: str, prompt: str):
        """Create appropriate task based on mode"""
        from app.data.task import Task
        
        if mode == EditorWidget.MODE_TEXT_TO_IMAGE:
            return Task(
                task_type="text_to_image",
                params={"prompt": prompt},
                workspace=self.workspace
            )
        elif mode == EditorWidget.MODE_IMAGE_TO_VIDEO:
            # Get current image from preview
            current_file = self.editor.get_preview_widget().current_file
            return Task(
                task_type="image_to_video",
                params={
                    "prompt": prompt,
                    "image_path": current_file
                },
                workspace=self.workspace
            )
        # ... handle other modes
    
    def _update_properties_for_mode(self, mode: str):
        """Update properties panel based on current mode"""
        # Show/hide relevant controls
        # Update default values
        # etc.
        pass


# Application entry point
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create workspace
    workspace = Workspace("/path/to/workspace", "my_project")
    
    # Create and show main window
    window = FilmetoMainWindow(workspace)
    window.show()
    
    sys.exit(app.exec())
```

## Layout Examples

### Option 1: Editor-Centric Layout

```
┌────────────────────────────────────────────────────────┐
│  Menu Bar                                              │
├───────┬────────────────────────────────────┬──────────┤
│       │                                    │          │
│ Task  │         EditorWidget               │ Props    │
│ List  │  ┌──────────────────────────────┐  │ Panel    │
│       │  │    Preview Area              │  │          │
│       │  │                              │  │          │
│       │  ├──────────────────────────────┤  │          │
│       │  │    Control Area              │  │          │
│       │  │  Mode │ Prompt Input         │  │          │
│       │  └──────────────────────────────┘  │          │
├───────┴────────────────────────────────────┴──────────┤
│  Timeline Widget                                       │
└────────────────────────────────────────────────────────┘
```

### Option 2: Tabbed Interface

```
┌────────────────────────────────────────────────────────┐
│  ┌─────┬────────┬─────────┬────────┐                  │
│  │ Edit│ Export │ Preview │ Tasks  │                   │
├──┴─────┴────────┴─────────┴────────┴──────────────────┤
│                                                        │
│              EditorWidget (Full Screen)                │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Preview Area                        │ │
│  │                                                  │ │
│  ├──────────────────────────────────────────────────┤ │
│  │              Control Area                        │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### Option 3: Side-by-Side with Timeline

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  ┌──────────────────────┬──────────────────────────┐  │
│  │                      │                          │  │
│  │   EditorWidget       │  Timeline (Vertical)     │  │
│  │                      │                          │  │
│  │                      │  [Item 1]                │  │
│  │   ┌────────────┐     │  [Item 2]                │  │
│  │   │  Preview   │     │  [Item 3]                │  │
│  │   └────────────┘     │  [Item 4]                │  │
│  │   ┌────────────┐     │  [Item 5]                │  │
│  │   │  Controls  │     │  [Item 6]                │  │
│  │   └────────────┘     │                          │  │
│  └──────────────────────┴──────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

## Workspace Integration

The editor automatically connects to workspace signals:

```python
# In your workspace setup
workspace = Workspace(path, name)

# When tasks complete, editor receives updates
workspace.connect_task_finished(editor.on_task_finished)
workspace.connect_timeline_switch(editor.on_timeline_switch)

# Editor's preview widget will automatically update
```

## State Management

```python
# Save editor state
def save_editor_state(self):
    state = {
        'mode': self.editor.get_current_mode(),
        'prompt': self.editor.get_prompt_text(),
        'splitter_sizes': self.editor.splitter.sizes()
    }
    # Save to workspace or settings
    self.workspace.save_editor_state(state)

# Restore editor state
def restore_editor_state(self):
    state = self.workspace.load_editor_state()
    if state:
        self.editor.set_mode(state['mode'])
        self.editor.splitter.setSizes(state['splitter_sizes'])
        # Note: Don't restore prompt text to avoid confusion
```

## Menu Integration

```python
# Add editor actions to menu bar
def _setup_menus(self):
    # Edit menu
    edit_menu = self.menuBar().addMenu("Edit")
    
    # Mode actions
    mode_menu = edit_menu.addMenu("Mode")
    
    text_to_image_action = QAction("Text to Image", self)
    text_to_image_action.triggered.connect(
        lambda: self.editor.set_mode(EditorWidget.MODE_TEXT_TO_IMAGE)
    )
    mode_menu.addAction(text_to_image_action)
    
    # ... add other modes
    
    # Clear prompt action
    clear_action = QAction("Clear Prompt", self)
    clear_action.setShortcut("Ctrl+Shift+C")
    clear_action.triggered.connect(self.editor.clear_prompt)
    edit_menu.addAction(clear_action)
```

## Tips

1. **Preserve Aspect Ratio**: The editor automatically maintains preview aspect ratios
2. **Async Operations**: All task operations are async - use proper async/await
3. **Signal Timing**: Connect signals before loading any data
4. **Resource Cleanup**: Editor handles cleanup automatically when destroyed
5. **State Persistence**: Save splitter positions and mode for better UX
6. **Keyboard Shortcuts**: Consider adding shortcuts for common operations
7. **Error Handling**: Wrap task creation in try/except blocks

## Common Issues

### Issue: RuntimeError: Cannot send to a coroutine function
**Solution**: The `on_timeline_switch` method must be non-async (sync) because it's called via blinker signals which don't support coroutines. The other task event handlers (`on_task_create`, `on_task_execute`, `on_task_finished`) can be async.

### Issue: Preview not updating
**Solution**: Ensure workspace signals are properly connected

### Issue: Prompt not clearing after submission
**Solution**: Call `editor.clear_prompt()` after task creation

### Issue: Mode change not reflected
**Solution**: Check signal connections and event loop

### Issue: Splitter not resizing
**Solution**: Ensure minimum sizes are set and parent layout allows expansion

## Next Steps

After integration:
1. Test all editing modes with real AI models
2. Add progress indicators for long-running tasks
3. Implement undo/redo for prompt history
4. Add export functionality
5. Create user preferences for default modes
6. Add keyboard shortcuts
7. Implement batch processing UI
