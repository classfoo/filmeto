# Timeline Cursor Line Feature

## Overview

The timeline cursor line feature provides a vertical white line that follows the mouse cursor when hovering over the timeline component. This visual feedback helps users precisely identify their cursor position on the timeline.

## Architecture

### Components

1. **TimelineContainer** (`timeline_container.py`)
   - Container widget that wraps the HorizontalTimeline
   - Handles mouse tracking and cursor line rendering
   - Ensures mouse events propagate through to child components

2. **HorizontalTimeline** (`timeline.py`)
   - The main timeline component with cards
   - Receives mouse events through the container

3. **Integration** (`main_window.py`)
   - MainWindowWorkspaceBottom uses TimelineContainer to wrap the timeline

## Key Features

### 1. Auto-fill Parent Space
The `TimelineContainer` uses a `QVBoxLayout` with zero margins and spacing, ensuring it fills the entire parent widget space:

```python
layout = QVBoxLayout(self)
layout.setContentsMargins(0, 0, 0, 0)
layout.setSpacing(0)
layout.addWidget(self.timeline_widget)
```

### 2. Non-intrusive Mouse Event Handling
Mouse events are properly propagated to child widgets:

```python
def mouseMoveEvent(self, event):
    self._mouse_x = event.pos().x()
    self.update()
    # Pass event to underlying timeline
    super().mouseMoveEvent(event)
```

This ensures:
- Timeline cards still receive hover effects
- Click events work normally
- Drag scrolling functionality is preserved

### 3. Elegant Rendering
The cursor line is rendered using QPainter with antialiasing:

```python
painter = QPainter(self)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)

pen = QPen(QColor(255, 255, 255, 200))  # White with transparency
pen.setWidth(2)
pen.setStyle(Qt.PenStyle.SolidLine)
painter.setPen(pen)

painter.drawLine(self._mouse_x, 0, self._mouse_x, self.height())
```

Features:
- 2px width for visibility
- Slight transparency (200/255) for subtle appearance
- Antialiasing for smooth rendering
- Full height vertical line

## Usage

### Basic Integration

```python
from app.ui.timeline.timeline import VideoTimeline
from app.ui.timeline.timeline_container import TimelineContainer

# Create timeline
timeline = VideoTimeline(parent, workspace)

# Wrap in container
timeline_container = TimelineContainer(timeline, parent)

# Add to layout
layout.addWidget(timeline_container)
```

### Testing

Run the test script to see the feature in action:

```bash
cd /Users/classfoo/ai/filmeto
python test/test_timeline_cursor.py
```

## Implementation Details

### Mouse Tracking

Mouse tracking is enabled on both the container and the timeline:

```python
self.setMouseTracking(True)
self.timeline_widget.setMouseTracking(True)
```

This ensures mouse move events are received even when no buttons are pressed.

### Event Lifecycle

1. **Mouse Enter**: User's cursor enters the timeline area
2. **Mouse Move**: Cursor position is tracked, line is redrawn
3. **Mouse Leave**: Line is hidden by clearing the position

### Performance Considerations

- Only redraws when mouse position changes
- Uses hardware-accelerated QPainter rendering
- Minimal overhead on mouse events

## Customization

### Line Appearance

To customize the cursor line appearance, modify the `paintEvent` method in `TimelineContainer`:

```python
# Example: Change to red line with 3px width
pen = QPen(QColor(255, 0, 0, 255))  # Solid red
pen.setWidth(3)
```

### Line Style

```python
# Dashed line
pen.setStyle(Qt.PenStyle.DashLine)

# Dotted line
pen.setStyle(Qt.PenStyle.DotLine)
```

## Best Practices

1. **Keep container transparent**: Don't set background colors on TimelineContainer
2. **Preserve event propagation**: Always call `super()` methods in event handlers
3. **Update efficiently**: Only call `update()` when the line position changes
4. **Maintain mouse tracking**: Ensure all relevant widgets have mouse tracking enabled

## Troubleshooting

### Line not appearing
- Verify mouse tracking is enabled
- Check that `_mouse_x` is being set in `mouseMoveEvent`
- Ensure `paintEvent` is being called (add debug print)

### Mouse events not working on cards
- Verify `super().mouseMoveEvent(event)` is called
- Check that card widgets are not being blocked by z-order issues

### Line appears jumpy
- Ensure antialiasing is enabled
- Check that widget updates are not being throttled

## Future Enhancements

Potential improvements to consider:

1. **Snap to frame boundaries**: Align line to frame positions
2. **Time display**: Show timestamp at cursor position
3. **Customizable appearance**: Add settings for line color, width, style
4. **Multi-line support**: Show multiple reference lines
5. **Magnetic cursor**: Snap to important timeline positions

## Related Files

- [`timeline_container.py`](file:///Users/classfoo/ai/filmeto/app/ui/timeline/timeline_container.py) - Container implementation
- [`timeline.py`](file:///Users/classfoo/ai/filmeto/app/ui/timeline/timeline.py) - Timeline component
- [`main_window.py`](file:///Users/classfoo/ai/filmeto/app/ui/main_window.py) - Integration point
- [`test_timeline_cursor.py`](file:///Users/classfoo/ai/filmeto/test/test_timeline_cursor.py) - Test script
