# Prompt Input Component - Usage Examples

## Example 1: Basic Integration

```python
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from app.data.workspace import Workspace
from app.ui.prompt import CanvasPromptWidget


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create workspace
        workspace = Workspace("./workspace", "my_project")

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Create layout
        layout = QVBoxLayout(central)

        # Add prompt input widget
        self.prompt_input = CanvasPromptWidget(workspace)
        self.prompt_input.prompt_submitted.connect(self.on_prompt_submit)
        layout.addWidget(self.prompt_input)

    def on_prompt_submit(self, prompt: str):
        print(f"Received prompt: {prompt}")
        # Process the prompt here
        self.prompt_input.clear_prompt()
```

## Example 2: Custom Placeholder

```python
# Set custom placeholder text
prompt_widget = PromptInputWidget(workspace)
prompt_widget.set_placeholder("Describe your scene in detail...")
```

## Example 3: Adding Templates Programmatically

```python
# Get prompt manager
prompt_manager = workspace.get_prompt_manager()

# Add multiple templates
templates = [
    {
        "icon": "textures/icons/scene.png",
        "text": "Create a cinematic wide shot of a futuristic city at night"
    },
    {
        "icon": "textures/icons/portrait.png",
        "text": "Generate a close-up portrait with dramatic lighting"
    },
    {
        "icon": "textures/icons/landscape.png",
        "text": "Produce a panoramic landscape with golden hour lighting"
    }
]

for template in templates:
    success = prompt_manager.add_template(
        template["icon"], 
        template["text"]
    )
    if success:
        print(f"Added template: {template['text'][:50]}...")
    else:
        print(f"Template already exists or failed to add")
```

## Example 4: Searching Templates

```python
# Search for templates containing "landscape"
prompt_manager = workspace.get_prompt_manager()
results = prompt_manager.search_templates("landscape")

print(f"Found {len(results)} templates:")
for template in results:
    print(f"- {template.text}")
    print(f"  Used {template.usage_count} times")
```

## Example 5: Monitoring Text Changes

```python
class MyWidget(QWidget):
    def __init__(self, workspace):
        super().__init__()
        
        self.prompt_input = PromptInputWidget(workspace)
        
        # Connect to prompt_changed signal
        self.prompt_input.prompt_changed.connect(self.on_text_change)
    
    def on_text_change(self, text: str):
        # Real-time validation or preview
        word_count = len(text.split())
        print(f"Word count: {word_count}")
        
        # Show warning if too short
        if len(text) < 10 and len(text) > 0:
            print("Warning: Prompt too short")
```

## Example 6: Task Creation Dialog

```python
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton

class TaskCreationDialog(QDialog):
    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.setWindowTitle("Create New Task")
        
        layout = QVBoxLayout(self)
        
        # Add prompt input
        self.prompt_input = PromptInputWidget(workspace)
        self.prompt_input.set_placeholder("Enter task description...")
        self.prompt_input.prompt_submitted.connect(self.create_task)
        layout.addWidget(self.prompt_input)
        
        # Add create button (alternative to Enter key)
        create_btn = QPushButton("Create Task")
        create_btn.clicked.connect(lambda: self.create_task(
            self.prompt_input.get_prompt_text()
        ))
        layout.addWidget(create_btn)
    
    def create_task(self, prompt: str):
        if not prompt.strip():
            return
        
        # Submit task to workspace
        self.workspace.submit_task({
            'type': 'generation',
            'prompt': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        # Clear and close
        self.prompt_input.clear_prompt()
        self.accept()
```

## Example 7: Loading and Displaying Templates

```python
from app.ui.prompt import TemplateItemWidget


class TemplateManagerWidget(QWidget):
    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace

        layout = QVBoxLayout(self)

        # Load all templates
        prompt_manager = workspace.get_prompt_manager()
        templates = prompt_manager.load_templates()

        # Display each template
        for template in templates:
            item = TemplateItemWidget(template)
            item.clicked.connect(self.on_template_click)
            layout.addWidget(item)

    def on_template_click(self, template):
        print(f"Clicked: {template.text}")
        print(f"Icon: {template.icon}")
        print(f"Usage: {template.usage_count}")
```

## Example 8: Template Management with UI

```python
from PySide6.QtWidgets import QFileDialog, QMessageBox

class TemplateEditor(QWidget):
    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Prompt input for creating templates
        self.prompt_input = PromptInputWidget(self.workspace)
        layout.addWidget(self.prompt_input)
        
        # Add template button
        add_btn = QPushButton("Save as Template")
        add_btn.clicked.connect(self.save_template)
        layout.addWidget(add_btn)
    
    def save_template(self):
        text = self.prompt_input.get_prompt_text()
        if not text.strip():
            QMessageBox.warning(self, "Empty", "Enter text first")
            return
        
        # Let user choose icon
        icon_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            "textures/icons",
            "Images (*.png *.jpg *.svg)"
        )
        
        if not icon_path:
            return
        
        # Add template
        pm = self.workspace.get_prompt_manager()
        if pm.add_template(icon_path, text):
            QMessageBox.information(
                self, 
                "Success", 
                "Template saved successfully"
            )
            self.prompt_input.clear_prompt()
        else:
            QMessageBox.warning(
                self,
                "Duplicate",
                "This template already exists"
            )
```

## Example 9: Getting Template Statistics

```python
def print_template_stats(workspace):
    pm = workspace.get_prompt_manager()
    templates = pm.load_templates()
    
    print(f"Total templates: {len(templates)}")
    
    if templates:
        # Most used template
        most_used = max(templates, key=lambda t: t.usage_count)
        print(f"Most used: {most_used.text[:50]}... ({most_used.usage_count} uses)")
        
        # Recently added
        newest = max(templates, key=lambda t: t.created_at)
        print(f"Newest: {newest.text[:50]}...")
        
        # Average usage
        avg_usage = sum(t.usage_count for t in templates) / len(templates)
        print(f"Average usage: {avg_usage:.2f}")
```

## Example 10: Deleting Templates

```python
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton

class TemplateManager(QWidget):
    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.setup_ui()
        self.load_templates()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        layout.addWidget(delete_btn)
    
    def load_templates(self):
        pm = self.workspace.get_prompt_manager()
        templates = pm.load_templates()
        
        self.list_widget.clear()
        for template in templates:
            item = QListWidgetItem(template.text)
            item.setData(Qt.UserRole, template.id)
            self.list_widget.addItem(item)
    
    def delete_selected(self):
        current = self.list_widget.currentItem()
        if not current:
            return
        
        template_id = current.data(Qt.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this template?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            pm = self.workspace.get_prompt_manager()
            if pm.delete_template(template_id):
                self.load_templates()
                QMessageBox.information(self, "Success", "Template deleted")
```

## Best Practices

1. **Always clear after submission**: Call `clear_prompt()` after processing to provide better UX
2. **Handle empty input**: Check for empty/whitespace-only prompts before processing
3. **Provide feedback**: Use status labels or messages to show what's happening
4. **Connect early**: Connect signals in `__init__` before adding to layout
5. **Test templates**: Add a few sample templates for testing during development
6. **Icon management**: Keep icons in a centralized directory (e.g., `textures/icons/`)
7. **Error handling**: Wrap workspace operations in try-except blocks
8. **Keyboard shortcuts**: Document keyboard shortcuts in your UI
9. **Placeholder text**: Use descriptive placeholders to guide users
10. **Signal usage**: Use `prompt_submitted` for actions, `prompt_changed` for validation

## Common Patterns

### Pattern 1: Validation Before Submission

```python
def on_prompt_submit(self, prompt: str):
    # Validate length
    if len(prompt) < 10:
        QMessageBox.warning(self, "Too Short", "Please enter at least 10 characters")
        return
    
    if len(prompt) > 10000:
        QMessageBox.warning(self, "Too Long", "Please keep prompt under 10,000 characters")
        return
    
    # Process valid prompt
    self.process_prompt(prompt)
    self.prompt_input.clear_prompt()
```

### Pattern 2: Real-time Preview

```python
def on_prompt_changed(self, text: str):
    # Update preview as user types
    self.preview_label.setText(f"Preview: {text[:100]}...")
    
    # Update word/char count
    words = len(text.split())
    chars = len(text)
    self.stats_label.setText(f"{words} words, {chars} characters")
```

### Pattern 3: Template Auto-Complete

```python
# The component already includes template filtering!
# Just add templates and they'll be searchable automatically
pm = workspace.get_prompt_manager()
pm.add_template("icon.png", "Your template text")
```
