"""
CanvasPreview - Timeline preview playback overlay widget

This widget displays timeline media content during playback, overlaying the canvas area.
It synchronizes with timeline position and handles smooth transitions between items.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from app.data.workspace import Workspace
from app.data.timeline import TimelineItem


class PreviewPreloader:
    """
    Background media loader for smooth timeline item transitions.
    
    Preloads the next timeline item's media content to enable seamless playback.
    """
    
    def __init__(self):
        self.preloaded_item_index: Optional[int] = None
        self.preloaded_media_type: Optional[str] = None
        self.preloaded_pixmap: Optional[QPixmap] = None
        self.preload_status: str = "idle"  # idle, loading, ready, cancelled
        
    def preload_item(self, timeline_item: TimelineItem):
        """
        Preload media content for the specified timeline item.
        
        Args:
            timeline_item: The timeline item to preload
        """
        if not timeline_item:
            return
            
        self.preloaded_item_index = timeline_item.get_index()
        self.preload_status = "loading"
        
        # Determine media type and load content
        import os
        video_path = timeline_item.get_video_path()
        image_path = timeline_item.get_image_path()
        
        if os.path.exists(video_path):
            self.preloaded_media_type = "video"
            # For videos, we'll prepare the player when transitioning
            # Just mark as ready with the path
            self.preload_status = "ready"
        elif os.path.exists(image_path):
            self.preloaded_media_type = "image"
            # Load the image pixmap
            self.preloaded_pixmap = QPixmap(image_path)
            self.preload_status = "ready"
        else:
            self.preload_status = "cancelled"
    
    def get_preloaded_content(self):
        """
        Retrieve preloaded content if ready.
        
        Returns:
            tuple: (media_type, content) where content is QPixmap for images or None for videos
        """
        if self.preload_status == "ready":
            return (self.preloaded_media_type, self.preloaded_pixmap)
        return (None, None)
    
    def clear(self):
        """Clear preloaded content and reset state."""
        self.preloaded_item_index = None
        self.preloaded_media_type = None
        self.preloaded_pixmap = None
        self.preload_status = "idle"


class CanvasPreview(QWidget):
    """
    Preview overlay widget that displays timeline content during playback.
    
    Features:
    - Positioned and sized to match CanvasLayer dimensions
    - Displays images and videos from timeline items
    - Tracks timeline position for automatic item switching
    - Preloads next item for smooth transitions
    - Shows/hides based on playback state
    """
    
    # Signal emitted when current item changes
    item_changed = Signal(int)  # item_index
    
    def __init__(self, workspace: Workspace, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.canvas_widget = parent
        
        # State tracking
        self._is_visible = False
        self._is_playing = False
        self._current_item_index: Optional[int] = None
        self._current_item_start_time: float = 0.0  # Timeline position where current item starts
        
        # Preloader
        self.preloader = PreviewPreloader()
        
        # Layer dimensions (will be set from canvas)
        self.layer_width = 720
        self.layer_height = 1280
        self.scale_factor = 1.0
        
        # Media display widgets
        self._setup_media_widgets()
        
        # Widget configuration
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setVisible(False)
        
        # Connect to project signals
        self._connect_signals()
    
    def _setup_media_widgets(self):
        """Initialize media display widgets for images and videos."""
        # Image display widget
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: transparent; }")
        self.image_label.hide()
        
        # Video display widget
        self.video_widget = QVideoWidget(self)
        self.video_widget.setStyleSheet("QVideoWidget { background-color: transparent; }")
        self.video_widget.hide()
        
        # Media player for videos
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Connect media player signals
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
    
    def _connect_signals(self):
        """Connect to workspace and project signals."""
        project = self.workspace.get_project()
        if project:
            # Connect to timeline position updates
            project.connect_timeline_position(self._on_timeline_position_changed)
    
    def set_layer_dimensions(self, width: int, height: int):
        """
        Set the layer dimensions that this preview should match.
        
        Args:
            width: Layer width in pixels
            height: Layer height in pixels
        """
        self.layer_width = width
        self.layer_height = height
        self._update_geometry()
    
    def _update_geometry(self):
        """Update preview widget size and position to match canvas layer."""
        if not self.canvas_widget:
            return
        
        # Calculate scale factor to fit within canvas
        canvas_width = self.canvas_widget.width()
        canvas_height = self.canvas_widget.height()
        
        if self.layer_width > 0 and self.layer_height > 0:
            width_scale = canvas_width / self.layer_width
            height_scale = canvas_height / self.layer_height
            self.scale_factor = min(width_scale, height_scale)
        else:
            self.scale_factor = 1.0
        
        # Calculate widget size
        widget_width = int(self.layer_width * self.scale_factor)
        widget_height = int(self.layer_height * self.scale_factor)
        
        # Center position
        center_x = max(0, (canvas_width - widget_width) // 2)
        center_y = max(0, (canvas_height - widget_height) // 2)
        
        # Apply geometry
        self.setGeometry(center_x, center_y, widget_width, widget_height)
        
        # Update child widget sizes
        self.image_label.setGeometry(0, 0, widget_width, widget_height)
        self.video_widget.setGeometry(0, 0, widget_width, widget_height)
    
    def on_playback_state_changed(self, is_playing: bool):
        """
        Handle playback state changes from PlayControl.
        
        Args:
            is_playing: True if playback started, False if stopped/paused
        """
        self._is_playing = is_playing
        
        if is_playing:
            # Show preview and load current item
            self._show_preview()
            # Load item at current timeline position
            project = self.workspace.get_project()
            if project:
                current_position = project.get_timeline_position()
                self._load_item_at_position(current_position)
        else:
            # Hide preview and stop playback
            self._hide_preview()
    
    def _show_preview(self):
        """Show the preview overlay."""
        self._is_visible = True
        self._update_geometry()
        self.show()
        self.raise_()  # Ensure preview is on top
    
    def _hide_preview(self):
        """Hide the preview overlay and stop media playback."""
        self._is_visible = False
        self.hide()
        
        # Stop any active media playback
        if self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.media_player.stop()
        
        # Clear preloader
        self.preloader.clear()
    
    def _on_timeline_position_changed(self, position: float):
        """
        Handle timeline position updates during playback.
        
        Args:
            position: Current timeline position in seconds
        """
        if not self._is_playing or not self._is_visible:
            return
        
        # Load item at this position if needed
        self._load_item_at_position(position)
    
    def _load_item_at_position(self, position: float):
        """
        Load and display the timeline item at the specified position.
        
        Args:
            position: Timeline position in seconds
        """
        # Get project and timeline
        project = self.workspace.get_project()
        if not project:
            return
        
        timeline = project.get_timeline()
        if not timeline:
            return
        
        # Map position to item index
        item_index, item_offset = self._position_to_item(position)
        
        if item_index is None or item_offset is None:
            return
        
        # Check if we need to switch items
        if item_index != self._current_item_index:
            self._switch_to_item(item_index, item_offset)
    
    def _position_to_item(self, position: float):
        """
        Map timeline position to timeline item index and offset.
        
        Args:
            position: Timeline position in seconds
            
        Returns:
            tuple: (item_index, item_offset) where item_offset is position within the item
                   Returns (None, None) if position is invalid
        """
        project = self.workspace.get_project()
        if not project:
            return (None, None)
        
        timeline = project.get_timeline()
        if not timeline:
            return (None, None)
        
        # Clamp position to valid range
        if position < 0:
            position = 0.0
        
        total_duration = project.get_timeline_duration()
        if position >= total_duration and total_duration > 0:
            # Loop back to start
            position = position % total_duration
        
        # Iterate through items to find the one containing this position
        accumulated_time = 0.0
        item_count = timeline.get_item_count()
        
        for i in range(1, item_count + 1):
            item_duration = project.get_item_duration(i)
            
            if position < accumulated_time + item_duration:
                # Found the item
                item_offset = position - accumulated_time
                return (i, item_offset)
            
            accumulated_time += item_duration
        
        # Position is beyond all items, return last item
        if item_count > 0:
            last_item_duration = project.get_item_duration(item_count)
            return (item_count, last_item_duration)
        
        return (None, None)
    
    def _switch_to_item(self, item_index: int, item_offset: float):
        """
        Switch display to the specified timeline item.
        
        Args:
            item_index: Index of the item to display (1-based)
            item_offset: Playback offset within the item in seconds
        """
        project = self.workspace.get_project()
        if not project:
            return
        
        timeline = project.get_timeline()
        if not timeline:
            return
        
        # Get the timeline item
        try:
            timeline_item = timeline.get_item(item_index)
        except Exception as e:
            print(f"Error getting timeline item {item_index}: {e}")
            return
        
        # Check if we have preloaded content for this item
        preload_type, preload_content = self.preloader.get_preloaded_content()
        
        if preload_type and self.preloader.preloaded_item_index == item_index:
            # Use preloaded content
            self._display_preloaded_item(preload_type, preload_content, timeline_item, item_offset)
        else:
            # Load item directly
            self._load_and_display_item(timeline_item, item_offset)
        
        # Update current item tracking
        self._current_item_index = item_index
        
        # Calculate start time of this item
        accumulated_time = 0.0
        for i in range(1, item_index):
            accumulated_time += project.get_item_duration(i)
        self._current_item_start_time = accumulated_time
        
        # Emit item changed signal
        self.item_changed.emit(item_index)
        
        # Preload next item
        self._preload_next_item(item_index)
    
    def _load_and_display_item(self, timeline_item: TimelineItem, item_offset: float):
        """
        Load and display a timeline item's media content.
        
        Args:
            timeline_item: The timeline item to display
            item_offset: Playback offset within the item in seconds
        """
        import os
        
        video_path = timeline_item.get_video_path()
        image_path = timeline_item.get_image_path()
        
        # Determine media type and display
        if os.path.exists(video_path):
            self._display_video(video_path, item_offset)
        elif os.path.exists(image_path):
            self._display_image(image_path)
        else:
            print(f"No media found for timeline item {timeline_item.get_index()}")
    
    def _display_preloaded_item(self, media_type: str, content, timeline_item: TimelineItem, item_offset: float):
        """
        Display preloaded media content.
        
        Args:
            media_type: "image" or "video"
            content: Preloaded content (QPixmap for images, None for videos)
            timeline_item: The timeline item being displayed
            item_offset: Playback offset within the item in seconds
        """
        if media_type == "image" and content:
            self._display_image_pixmap(content)
        elif media_type == "video":
            # Load video normally since we can't fully preload video players
            video_path = timeline_item.get_video_path()
            self._display_video(video_path, item_offset)
        
        # Clear preloader after using content
        self.preloader.clear()
    
    def _display_image(self, image_path: str):
        """
        Display an image file.
        
        Args:
            image_path: Path to the image file
        """
        pixmap = QPixmap(image_path)
        self._display_image_pixmap(pixmap)
    
    def _display_image_pixmap(self, pixmap: QPixmap):
        """
        Display a QPixmap image.
        
        Args:
            pixmap: The pixmap to display
        """
        # Hide video, show image
        self.video_widget.hide()
        if self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.media_player.stop()
        
        # Scale pixmap to match preview dimensions
        scaled_pixmap = pixmap.scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.show()
    
    def _display_video(self, video_path: str, offset: float):
        """
        Display and play a video file.
        
        Args:
            video_path: Path to the video file
            offset: Starting position in seconds
        """
        from PySide6.QtCore import QUrl
        
        # Hide image, show video
        self.image_label.hide()
        
        # Stop current playback if any
        if self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.media_player.stop()
        
        # Set new video source
        url = QUrl.fromLocalFile(video_path)
        self.media_player.setSource(url)
        
        # Set starting position (will be applied when media is loaded)
        self._pending_video_offset = offset
        
        self.video_widget.show()
    
    def _on_media_status_changed(self, status):
        """Handle media player status changes."""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Media is loaded, set position and start playback
            if hasattr(self, '_pending_video_offset'):
                offset_ms = int(self._pending_video_offset * 1000)
                self.media_player.setPosition(offset_ms)
                delattr(self, '_pending_video_offset')
            
            # Start playback
            if self._is_playing:
                self.media_player.play()
    
    def _preload_next_item(self, current_item_index: int):
        """
        Preload the next timeline item for smooth transitions.
        
        Args:
            current_item_index: Index of the current item
        """
        project = self.workspace.get_project()
        if not project:
            return
        
        timeline = project.get_timeline()
        if not timeline:
            return
        
        item_count = timeline.get_item_count()
        next_item_index = current_item_index + 1
        
        # Check if there's a next item (handle looping)
        if next_item_index > item_count:
            # Loop to first item if timeline loops
            next_item_index = 1
        
        # Get next item
        try:
            next_item = timeline.get_item(next_item_index)
            self.preloader.preload_item(next_item)
        except Exception as e:
            print(f"Error preloading item {next_item_index}: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events to update preview geometry."""
        super().resizeEvent(event)
        if self._is_visible:
            self._update_geometry()
