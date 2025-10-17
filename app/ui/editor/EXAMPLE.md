# EditorWidget Usage Examples

This document provides practical examples of using the `EditorWidget` component in different scenarios.

## Table of Contents

1. [Basic Integration](#basic-integration)
2. [Mode Switching](#mode-switching)
3. [Handling Prompts](#handling-prompts)
4. [Custom Workflows](#custom-workflows)
5. [Task Integration](#task-integration)

---

## Basic Integration

### Example 1: Simple Editor Window

```python
from PySide6.QtWidgets import QApplication, QMainWindow
from app.ui.editor import EditorWidget
from app.data.workspace import Workspace

class MyEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My AI Editor")
        self.resize(1200, 800)
        
        # Create workspace
        workspace = Workspace("/path/to/workspace", "my_project")
        
        # Create and set editor as central widget
        self.editor = EditorWidget(workspace)
        self.setCentralWidget(self.editor)

app = QApplication([])
window = MyEditorWindow()
window.show()
app.exec()
```

### Example 2: Editor in a Tab

```python
from PySide6.QtWidgets import QTabWidget
from app.ui.editor import EditorWidget

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add editor as a tab
        workspace = Workspace("/workspace", "project")
        editor = EditorWidget(workspace)
        self.tabs.addTab(editor, "Editor")
```

---

## Mode Switching

### Example 3: Programmatic Mode Control

```python
editor = EditorWidget(workspace)

# Set initial mode
editor.set_mode(EditorWidget.MODE_TEXT_TO_IMAGE)

# Listen for mode changes
def on_mode_change(mode):
    print(f"Current mode: {mode}")
    
    if mode == EditorWidget.MODE_IMAGE_TO_VIDEO:
        # Load default image for conversion
        editor.get_preview_widget().load_file("default.png")
    elif mode == EditorWidget.MODE_TEXT_TO_IMAGE:
        # Clear preview
        editor.get_preview_widget()._clear_display()

editor.mode_changed.connect(on_mode_change)
```

### Example 4: Mode-Specific Settings

```python
class SmartEditor(EditorWidget):
    def __init__(self, workspace):
        super().__init__(workspace)
        self._setup_mode_configs()
    
    def _setup_mode_configs(self):
        """Configure settings per mode"""
        self.mode_configs = {
            self.MODE_TEXT_TO_IMAGE: {
                'max_chars': 500,
                'default_prompt': 'A beautiful landscape',
                'output_format': 'png'
            },
            self.MODE_IMAGE_TO_VIDEO: {
                'max_chars': 300,
                'default_prompt': 'Gentle camera movement',
                'output_format': 'mp4',
                'duration': 5  # seconds
            },
            # ... other modes
        }
    
    def _on_mode_changed(self, index):
        """Override to apply mode-specific settings"""
        super()._on_mode_changed(index)
        
        mode = self.get_current_mode()
        config = self.mode_configs.get(mode, {})
        
        # Apply configuration
        default_prompt = config.get('default_prompt', '')
        if default_prompt:
            self.prompt_input.set_placeholder(
                f"e.g., {default_prompt}"
            )
```

---

## Handling Prompts

### Example 5: Prompt Processing Pipeline

```python
class AIEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        
        workspace = Workspace("/workspace", "project")
        self.editor = EditorWidget(workspace)
        self.setCentralWidget(self.editor)
        
        # Connect prompt submission
        self.editor.prompt_submitted.connect(self.process_prompt)
    
    def process_prompt(self, mode: str, prompt: str):
        """Process submitted prompt"""
        print(f"Processing: {mode} - {prompt}")
        
        # Step 1: Validate prompt
        if not self.validate_prompt(prompt):
            QMessageBox.warning(self, "Invalid", "Prompt too short")
            return
        
        # Step 2: Pre-process prompt
        processed = self.preprocess_prompt(prompt, mode)
        
        # Step 3: Create task
        task = self.create_ai_task(mode, processed)
        
        # Step 4: Execute
        self.execute_task(task)
        
        # Step 5: Update UI
        self.editor.set_processing(True)
    
    def validate_prompt(self, prompt: str) -> bool:
        return len(prompt.strip()) >= 10
    
    def preprocess_prompt(self, prompt: str, mode: str) -> str:
        # Add mode-specific prefixes/suffixes
        if mode == EditorWidget.MODE_TEXT_TO_IMAGE:
            return f"High quality, detailed: {prompt}"
        return prompt
    
    def create_ai_task(self, mode: str, prompt: str):
        # Create task based on mode
        pass
    
    def execute_task(self, task):
        # Execute the AI task
        pass
```

### Example 6: Prompt Templates Integration

```python
editor = EditorWidget(workspace)

# Add custom templates programmatically
prompt_manager = workspace.get_prompt_manager()

# Add templates
prompt_manager.add_template(
    text="A cinematic shot of [subject], golden hour lighting",
    category="photography",
    tags=["cinematic", "lighting"]
)

prompt_manager.add_template(
    text="Animate [object] with smooth motion",
    category="animation",
    tags=["motion", "smooth"]
)

# Templates will automatically appear in prompt suggestions
```

---

## Custom Workflows

### Example 7: Text-to-Image-to-Video Pipeline

```python
class PipelineEditor(EditorWidget):
    def __init__(self, workspace):
        super().__init__(workspace)
        self.pipeline_mode = False
        self.generated_image = None
        
        # Add pipeline button
        self.add_pipeline_button()
    
    def add_pipeline_button(self):
        from PySide6.QtWidgets import QPushButton
        
        btn = QPushButton("Run Pipeline (Text→Image→Video)")
        btn.clicked.connect(self.run_pipeline)
        
        # Add to control area
        layout = self.control_container.layout()
        layout.insertWidget(0, btn)
    
    async def run_pipeline(self):
        """Execute multi-step pipeline"""
        # Step 1: Text to Image
        self.set_mode(self.MODE_TEXT_TO_IMAGE)
        prompt = self.get_prompt_text()
        
        print("Step 1: Generating image...")
        image_path = await self.generate_image(prompt)
        
        if not image_path:
            return
        
        self.generated_image = image_path
        
        # Step 2: Load generated image
        self.get_preview_widget().load_file(image_path)
        await asyncio.sleep(2)  # Let user see the result
        
        # Step 3: Image to Video
        self.set_mode(self.MODE_IMAGE_TO_VIDEO)
        print("Step 2: Converting to video...")
        
        video_path = await self.generate_video(image_path, prompt)
        
        if video_path:
            self.get_preview_widget().load_file(video_path)
            print("Pipeline complete!")
    
    async def generate_image(self, prompt: str) -> str:
        # Your AI image generation logic
        pass
    
    async def generate_video(self, image_path: str, prompt: str) -> str:
        # Your AI video generation logic
        pass
```

### Example 8: Batch Processing

```python
class BatchEditor(EditorWidget):
    def __init__(self, workspace):
        super().__init__(workspace)
        self.batch_queue = []
    
    def add_to_batch(self, prompt: str):
        """Add prompt to batch queue"""
        mode = self.get_current_mode()
        self.batch_queue.append((mode, prompt))
        print(f"Added to batch: {len(self.batch_queue)} items")
    
    async def process_batch(self):
        """Process all items in batch"""
        for i, (mode, prompt) in enumerate(self.batch_queue):
            print(f"Processing {i+1}/{len(self.batch_queue)}")
            
            self.set_mode(mode)
            await self.process_single(mode, prompt)
            
        self.batch_queue.clear()
        print("Batch complete!")
    
    async def process_single(self, mode: str, prompt: str):
        # Process single item
        pass
```

---

## Task Integration

### Example 9: Task Lifecycle Handling

```python
class TaskAwareEditor(EditorWidget):
    async def on_task_create(self, params):
        """Handle task creation"""
        await super().on_task_create(params)
        
        print(f"Task created with params: {params}")
        
        # Show notification
        self._show_notification("Task Created", "Processing started")
    
    async def on_task_execute(self, task: Task):
        """Handle task execution"""
        await super().on_task_execute(task)
        
        print(f"Executing task: {task.get_type()}")
        
        # Update progress UI
        self._update_progress(0)
    
    async def on_task_finished(self, result: TaskResult):
        """Handle task completion"""
        await super().on_task_finished(result)
        
        print(f"Task finished: {result.get_status()}")
        
        # Update preview with result
        if result.get_image_path():
            self.get_preview_widget().load_file(
                result.get_image_path()
            )
        elif result.get_video_path():
            self.get_preview_widget().load_file(
                result.get_video_path()
            )
        
        # Clear prompt for next task
        self.clear_prompt()
        
        # Show completion notification
        self._show_notification("Complete", "Task finished!")
    
    def _show_notification(self, title: str, message: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)
    
    def _update_progress(self, value: int):
        # Update progress bar if you have one
        pass
```

### Example 10: Timeline Integration

```python
class TimelineEditor(EditorWidget):
    async def on_timeline_switch(self, item: TimelineItem):
        """Handle timeline item selection"""
        await super().on_timeline_switch(item)
        
        print(f"Switched to timeline item: {item.get_index()}")
        
        # Load associated prompt
        if hasattr(item, 'prompt'):
            self.prompt_input.text_edit.setPlainText(item.prompt)
        
        # Set appropriate mode
        if item.has_video():
            self.set_mode(self.MODE_VIDEO_EDIT)
        elif item.has_image():
            self.set_mode(self.MODE_IMAGE_EDIT)
```

---

## Advanced Features

### Example 11: Real-time Preview

```python
class LiveEditor(EditorWidget):
    def __init__(self, workspace):
        super().__init__(workspace)
        
        # Enable live preview mode
        self.live_preview = True
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_live_preview)
        
        # Connect to prompt changes
        self.prompt_input.prompt_changed.connect(
            self.on_prompt_changed_live
        )
    
    def on_prompt_changed_live(self, text: str):
        """Handle real-time prompt changes"""
        if not self.live_preview or len(text) < 20:
            return
        
        # Debounce - restart timer
        self.preview_timer.stop()
        self.preview_timer.start(2000)  # Wait 2s after typing stops
    
    def update_live_preview(self):
        """Generate quick preview"""
        prompt = self.get_prompt_text()
        mode = self.get_current_mode()
        
        # Generate low-quality quick preview
        # (Use faster model or lower resolution)
        preview_path = self.generate_quick_preview(mode, prompt)
        
        if preview_path:
            self.get_preview_widget().load_file(preview_path)
```

### Example 12: Keyboard Shortcuts

```python
class ShortcutEditor(EditorWidget):
    def __init__(self, workspace):
        super().__init__(workspace)
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+1 to Ctrl+5 for mode switching
        modes = [
            self.MODE_TEXT_TO_IMAGE,
            self.MODE_IMAGE_TO_VIDEO,
            self.MODE_TEXT_TO_VIDEO,
            self.MODE_IMAGE_EDIT,
            self.MODE_VIDEO_EDIT,
        ]
        
        for i, mode in enumerate(modes, 1):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(
                lambda m=mode: self.set_mode(m)
            )
        
        # Ctrl+Shift+C to clear
        clear_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        clear_shortcut.activated.connect(self.clear_prompt)
        
        # F11 for fullscreen preview
        fullscreen = QShortcut(QKeySequence("F11"), self)
        fullscreen.activated.connect(self.toggle_fullscreen_preview)
    
    def toggle_fullscreen_preview(self):
        # Toggle fullscreen mode for preview
        pass
```

---

## Tips and Best Practices

1. **Always validate prompts** before processing
2. **Use async/await** for long-running tasks
3. **Provide visual feedback** during processing
4. **Handle errors gracefully** with user-friendly messages
5. **Save user preferences** (last mode, recent prompts, etc.)
6. **Implement undo/redo** for editing operations
7. **Use templates** to guide users
8. **Monitor resource usage** during processing
9. **Implement auto-save** for work in progress
10. **Test with various media formats** and sizes
