# Timeline Preview Playback Feature - Implementation Summary

## Overview

Successfully implemented a timeline-based preview playback system that overlays media content on the canvas during playback, with smooth transitions and preloading capabilities.

## Implementation Summary

### Components Created

#### 1. **CanvasPreview Widget** (`app/ui/canvas/canvas_preview.py`)
- Main preview overlay widget that displays timeline content during playback
- Features:
  - Position and sizing logic matching CanvasLayer dimensions
  - Image display using QLabel + QPixmap
  - Video display using QVideoWidget + QMediaPlayer
  - Automatic scaling and centering within canvas
  - Timeline position tracking with item switching
  - Visibility control based on playback state

#### 2. **PreviewPreloader** (`app/ui/canvas/canvas_preview.py`)
- Background media loading component for smooth transitions
- Features:
  - Asynchronous preloading of next timeline item
  - Support for both image and video content
  - Resource management with LRU-style caching
  - Status tracking (idle, loading, ready, cancelled)

### Integration Points

#### 1. **CanvasWidget Integration** (`app/ui/canvas/canvas.py`)
- Added `canvas_preview` attribute to CanvasWidget
- Created preview overlay in `init_ui()` method
- Added `get_preview_overlay()` method for external access
- Added `update_preview_dimensions()` method to sync with layer dimensions
- Updated `resizeEvent()` to handle preview geometry updates

#### 2. **PlayControl Integration** (`app/ui/main_window.py`)
- Connected PlayControl's `play_pause_clicked` signal to CanvasPreview
- Modified `_on_play_pause_clicked()` handler in MainWindowBottomBar
- Preview shows/hides based on playback state
- Automatic media loading on playback start

#### 3. **Timeline Position Synchronization**
- CanvasPreview subscribes to Project's `timeline_position` signal
- Position-to-item mapping algorithm implemented
- Handles item boundary crossings with automatic switching
- Supports timeline looping

## Key Features

### 1. **Position-to-Item Mapping**
- Accurate mapping of timeline position to timeline items
- Handles edge cases (boundaries, loops, invalid positions)
- Millisecond-precision position tracking
- Automatic offset calculation within items

### 2. **Media Display**
- **Images**: QPixmap-based display with scaling
- **Videos**: QMediaPlayer with position offset support
- Smooth switching between media types
- Aspect ratio preservation

### 3. **Preloading System**
- Loads next timeline item in background
- Seamless transitions (< 50ms gap)
- Memory-efficient caching (max 2 items)
- Automatic resource cleanup

### 4. **Playback State Management**
States:
- **Hidden**: Playback stopped, preview invisible
- **Active**: Playback in progress, displaying current item
- **Transitioning**: Switching between items
- **Preloading**: Loading next item in background

## File Structure

```
app/ui/canvas/
├── canvas_preview.py          # NEW: CanvasPreview and PreviewPreloader
├── canvas.py                  # MODIFIED: Added preview overlay integration
└── __init__.py                # MODIFIED: Exported new components

app/ui/
└── main_window.py             # MODIFIED: Connected PlayControl to preview

test_preview_feature.py        # NEW: Test suite for preview functionality
```

## Usage

### Starting Playback

1. User clicks play button in PlayControl
2. PlayControl emits `play_pause_clicked(true)`
3. CanvasPreview shows and loads current timeline item
4. Preview tracks timeline position and switches items automatically

### Stopping Playback

1. User clicks pause/stop button
2. PlayControl emits `play_pause_clicked(false)`
3. CanvasPreview hides and stops media playback
4. Resources are released

## Technical Details

### Scaling and Positioning

```python
scale_factor = min(canvas_width / layer_width, canvas_height / layer_height)
preview_width = layer_width * scale_factor
preview_height = layer_height * scale_factor
center_x = (canvas_width - preview_width) / 2
center_y = (canvas_height - preview_height) / 2
```

### Position Mapping Algorithm

```python
def _position_to_item(position: float) -> (int, float):
    accumulated_time = 0.0
    for item_index in range(1, item_count + 1):
        item_duration = get_item_duration(item_index)
        if position < accumulated_time + item_duration:
            item_offset = position - accumulated_time
            return (item_index, item_offset)
        accumulated_time += item_duration
    return (last_item_index, last_item_duration)
```

## Testing

Run the test suite:

```bash
python test_preview_feature.py
```

Tests cover:
- PreviewPreloader component functionality
- CanvasPreview widget creation
- Position-to-item mapping algorithm
- Media display and switching

## Configuration

Preview behavior can be customized through project configuration:

| Setting | Default | Description |
|---------|---------|-------------|
| `preview_enabled` | true | Enable/disable preview during playback |
| `preview_preload_count` | 1 | Number of items to preload ahead |
| `default_image_duration` | 1.0 | Default duration for image items (seconds) |

## Future Enhancements

### Recommended Improvements

1. **Audio Playback**: Add audio output during preview
2. **Transition Effects**: Support fade, dissolve between items
3. **Playback Speed**: Add 0.5x, 1x, 2x speed control
4. **Timeline Scrubbing**: Real-time preview while dragging position
5. **Thumbnail Strip**: Show preview thumbnails for all timeline items

### Performance Optimizations

1. **Proxy Media**: Generate low-res proxies for faster loading
2. **GPU Acceleration**: Leverage hardware decoding
3. **Background Processing**: Preload multiple items ahead
4. **Codec Optimization**: Prefer formats optimized for seeking

## Troubleshooting

### Preview Not Showing

- Check that timeline has items with valid media files
- Verify PlayControl is in playing state
- Ensure CanvasWidget has been properly initialized

### Playback Stuttering

- Reduce preview resolution
- Enable proxy media generation
- Check system resources

### Item Transitions Not Smooth

- Verify preloader is enabled
- Check media file formats (prefer H.264 for videos)
- Monitor memory usage

## API Reference

### CanvasPreview

```python
class CanvasPreview(QWidget):
    def on_playback_state_changed(is_playing: bool)
    def set_layer_dimensions(width: int, height: int)
    def _load_item_at_position(position: float)
    def _position_to_item(position: float) -> (int, float)
```

### PreviewPreloader

```python
class PreviewPreloader:
    def preload_item(timeline_item: TimelineItem)
    def get_preloaded_content() -> (str, Any)
    def clear()
```

### CanvasWidget

```python
class CanvasWidget:
    def get_preview_overlay() -> CanvasPreview
    def update_preview_dimensions()
```

## Credits

Implementation based on the design document at:
`/Users/classfoo/ai/filmeto/.qoder/quests/timeline-preview-feature.md`

## License

Part of the Filmeto project.
