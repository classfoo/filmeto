# Timeline Cursor Line - Visual Guide

## What You'll See

When you move your mouse over the timeline component, a **vertical white line** will follow your cursor position. This provides precise visual feedback for cursor positioning on the timeline.

## Visual Characteristics

### Line Properties
- **Color**: White (RGB: 255, 255, 255)
- **Opacity**: ~78% (200/255) - slightly transparent
- **Width**: 2 pixels
- **Style**: Solid line
- **Height**: Full height of the timeline area
- **Antialiasing**: Enabled for smooth rendering

### Behavior
```
┌─────────────────────────────────────────────────┐
│  Timeline Area                                   │
│                                                  │
│  ┌────┐  ┌────┐  ┌────│  ┌────┐  ┌────┐       │
│  │ #1 │  │ #2 │  │ #3 │  │ #4 │  │ #5 │       │
│  │    │  │    │  │    │  │    │  │    │       │
│  └────┘  └────┘  └────│  └────┘  └────┘       │
│                       │                         │
│                       │← White cursor line      │
│                       │   (follows mouse)       │
└───────────────────────│─────────────────────────┘
                        ↑
                  Mouse position
```

## States

### 1. Mouse Outside Timeline
- **Line visible**: ❌ No
- **State**: Hidden
- **Cursor**: Default

### 2. Mouse Inside Timeline
- **Line visible**: ✅ Yes
- **State**: Active, following cursor
- **Cursor**: Default (no change)

### 3. Hover Over Card
- **Line visible**: ✅ Yes
- **Card hover effect**: ✅ Visible (blue border)
- **Both effects**: Work simultaneously

## Testing the Feature

### Quick Test Steps

1. **Launch the application**:
   ```bash
   cd /Users/classfoo/ai/filmeto
   python main.py
   ```

2. **Locate the timeline**:
   - Look at the bottom section of the window
   - You should see horizontal cards with images

3. **Move your mouse**:
   - Hover your mouse over the timeline area
   - A vertical white line should appear
   - Move left and right - the line follows

4. **Test edge cases**:
   - Move to the very left edge - line appears
   - Move to the very right edge - line appears
   - Move outside the timeline - line disappears
   - Hover over cards - both line and card hover work

### Standalone Test

Run the dedicated test script:

```bash
cd /Users/classfoo/ai/filmeto
python test/test_timeline_cursor.py
```

This opens a minimal window showing just the timeline with the cursor line feature.

## Visual Comparison

### Before (Without Cursor Line)
```
┌───────────────────────────────┐
│  ┌────┐  ┌────┐  ┌────┐      │
│  │ #1 │  │ #2 │  │ #3 │      │
│  └────┘  └────┘  └────┘      │
│                               │
│  (No visual cursor indicator) │
└───────────────────────────────┘
```

### After (With Cursor Line)
```
┌───────────────────────────────┐
│  ┌────┐  ┌────│  ┌────┐      │
│  │ #1 │  │ #2 │  │ #3 │      │
│  └────┘  └────│  └────┘      │
│               │               │
│               │← Clear visual │
│               │   indicator   │
└───────────────│───────────────┘
```

## Integration Points

### Where to Find It

1. **Main Application**:
   - File: `main_window.py`
   - Class: `MainWindowWorkspaceBottom`
   - Component: Timeline at bottom of window

2. **Standalone Timeline**:
   - File: `timeline.py`
   - Class: `HorizontalTimeline`
   - Can be wrapped in `TimelineContainer`

## Customization Examples

### Change Line Color

Edit `timeline_container.py`, line ~114:

```python
# Red line
pen = QPen(QColor(255, 0, 0, 200))

# Blue line
pen = QPen(QColor(0, 120, 255, 200))

# Green line
pen = QPen(QColor(0, 255, 0, 200))
```

### Change Line Width

```python
# Thicker line (4px)
pen.setWidth(4)

# Thinner line (1px)
pen.setWidth(1)
```

### Change Line Style

```python
# Dashed line
pen.setStyle(Qt.PenStyle.DashLine)

# Dotted line
pen.setStyle(Qt.PenStyle.DotLine)

# Dash-dot line
pen.setStyle(Qt.PenStyle.DashDotLine)
```

### Change Opacity

```python
# Fully opaque
pen = QPen(QColor(255, 255, 255, 255))

# More transparent
pen = QPen(QColor(255, 255, 255, 100))
```

## Expected User Experience

### Smooth Interaction
- ✅ Line appears instantly when mouse enters
- ✅ Line moves smoothly with cursor
- ✅ No lag or jitter
- ✅ Disappears cleanly when mouse leaves

### Non-Intrusive
- ✅ Doesn't block clicks on cards
- ✅ Doesn't interfere with drag scrolling
- ✅ Doesn't affect card hover effects
- ✅ Renders on top but events pass through

### Visual Clarity
- ✅ Clearly visible against timeline background
- ✅ Subtle enough not to distract
- ✅ Precise positioning feedback
- ✅ Consistent appearance

## Troubleshooting Visual Issues

### Line Not Visible

**Possible causes:**
1. Background too bright (white line on white background)
2. Opacity too low
3. Width too thin

**Solutions:**
```python
# Increase opacity
pen = QPen(QColor(255, 255, 255, 255))  # Fully opaque

# Increase width
pen.setWidth(3)

# Change color for contrast
pen = QPen(QColor(255, 0, 0, 255))  # Red, fully opaque
```

### Line Appears Jagged

**Cause:** Antialiasing disabled

**Solution:**
```python
# Ensure this line exists in paintEvent
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
```

### Line Position Offset

**Cause:** Coordinate system mismatch

**Check:**
- Mouse coordinates are relative to container
- Line is drawn in container's coordinate space
- No transformations applied to painter

## Performance Notes

### Rendering Performance
- **Update frequency**: On every mouse move (~60 Hz typical)
- **Rendering cost**: Minimal (single line draw)
- **Hardware acceleration**: Enabled via Qt
- **CPU impact**: Negligible

### Memory Footprint
- **Additional memory**: ~1KB for container widget
- **No image buffers**: Direct painting
- **No caching needed**: Line is simple primitive

## Accessibility Considerations

### Current Implementation
- ✅ Visual feedback provided
- ⚠️ Not accessible to screen readers (visual only)
- ⚠️ No keyboard-based cursor positioning

### Future Enhancements
- Add keyboard navigation support
- Provide audio cues for position
- Add text labels showing position/time
- Support high-contrast modes

## Related Documentation

- [Main README](../README_CURSOR_LINE.md) - Complete technical documentation
- [Timeline Component](../app/ui/timeline/timeline.py) - Timeline implementation
- [Container Widget](../app/ui/timeline/timeline_container.py) - Container implementation
- [Test Script](../test/test_timeline_cursor.py) - Testing code
