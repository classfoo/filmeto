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
    
    Preloads the next 3 timeline items' media content to enable seamless playback.
    """
    
    def __init__(self):
        # Store preloaded items in a dict: {item_index: {"type": str, "pixmap": QPixmap, "status": str}}
        self.preloaded_items: dict = {}
        self.max_preload_count: int = 3  # Preload next 3 items
        
    def preload_item(self, timeline_item: TimelineItem):
        """
        Preload media content for the specified timeline item.
        
        Args:
            timeline_item: The timeline item to preload
        """
        if not timeline_item:
            return
        
        item_index = timeline_item.get_index()
        
        # Skip if already preloaded
        if item_index in self.preloaded_items:
            return
        
        # Determine media type and load content
        import os
        video_path = timeline_item.get_video_path()
        image_path = timeline_item.get_image_path()
        
        if os.path.exists(video_path):
            # For videos, just store metadata (actual loading happens during playback)
            self.preloaded_items[item_index] = {
                "type": "video",
                "pixmap": None,
                "path": video_path,
                "status": "ready"
            }
        elif os.path.exists(image_path):
            # Load the image pixmap immediately
            pixmap = QPixmap(image_path)
            self.preloaded_items[item_index] = {
                "type": "image",
                "pixmap": pixmap,
                "path": image_path,
                "status": "ready"
            }
        else:
            self.preloaded_items[item_index] = {
                "type": None,
                "pixmap": None,
                "path": None,
                "status": "cancelled"
            }
    
    def get_preloaded_content(self, item_index: int):
        """
        Retrieve preloaded content for a specific item if ready.
        
        Args:
            item_index: The index of the item to retrieve
            
        Returns:
            tuple: (media_type, content) where content is QPixmap for images or None for videos
        """
        if item_index in self.preloaded_items:
            item_data = self.preloaded_items[item_index]
            if item_data["status"] == "ready":
                return (item_data["type"], item_data["pixmap"])
        return (None, None)
    
    def clear(self):
        """Clear all preloaded content and reset state."""
        self.preloaded_items.clear()
    
    def remove_item(self, item_index: int):
        """Remove a specific preloaded item to free memory."""
        if item_index in self.preloaded_items:
            del self.preloaded_items[item_index]
    
    def cleanup_old_items(self, current_index: int, keep_count: int = 3):
        """
        Clean up preloaded items that are no longer needed.
        Keeps only items within range [current_index, current_index + keep_count].
        
        Args:
            current_index: Current playing item index
            keep_count: Number of future items to keep preloaded
        """
        items_to_remove = []
        for item_index in self.preloaded_items.keys():
            # Remove items that are behind current position or too far ahead
            if item_index < current_index or item_index > current_index + keep_count:
                items_to_remove.append(item_index)
        
        for item_index in items_to_remove:
            del self.preloaded_items[item_index]


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
        
        # Double buffering state
        self._active_player: str = "primary"  # "primary" or "secondary"
        self._next_item_prepared: Optional[int] = None  # Index of item prepared in secondary player
        
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
        """Initialize media display widgets for images and videos with double buffering."""
        # Image display widget
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: transparent; }")
        self.image_label.hide()
        
        # Primary video display widget and player
        self.primary_video_widget = QVideoWidget(self)
        self.primary_video_widget.setStyleSheet("QVideoWidget { background-color: transparent; }")
        self.primary_video_widget.hide()
        
        self.primary_player = QMediaPlayer(self)
        self.primary_audio_output = QAudioOutput(self)
        self.primary_player.setAudioOutput(self.primary_audio_output)
        self.primary_player.setVideoOutput(self.primary_video_widget)
        self.primary_player.mediaStatusChanged.connect(
            lambda status: self._on_media_status_changed(status, "primary")
        )
        
        # Secondary video display widget and player (for seamless transitions)
        self.secondary_video_widget = QVideoWidget(self)
        self.secondary_video_widget.setStyleSheet("QVideoWidget { background-color: transparent; }")
        self.secondary_video_widget.hide()
        
        self.secondary_player = QMediaPlayer(self)
        self.secondary_audio_output = QAudioOutput(self)
        self.secondary_player.setAudioOutput(self.secondary_audio_output)
        self.secondary_player.setVideoOutput(self.secondary_video_widget)
        self.secondary_player.mediaStatusChanged.connect(
            lambda status: self._on_media_status_changed(status, "secondary")
        )
        
        # Keep backward compatibility references
        self.video_widget = self.primary_video_widget
        self.media_player = self.primary_player
        self.audio_output = self.primary_audio_output
    
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
        self.primary_video_widget.setGeometry(0, 0, widget_width, widget_height)
        self.secondary_video_widget.setGeometry(0, 0, widget_width, widget_height)
    
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
        
        # Stop both media players
        if self.primary_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.primary_player.stop()
        if self.secondary_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.secondary_player.stop()
        
        # Reset double buffering state
        self._active_player = "primary"
        self._next_item_prepared = None
        
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
        Switch display to the specified timeline item with seamless transition.
        
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
        
        # Check if next item is already prepared in secondary player
        if self._next_item_prepared == item_index:
            # Seamless transition: swap to secondary player
            self._swap_active_player()
            # Start playback from prepared position if needed
            self._resume_secondary_player(item_offset)
        else:
            # Normal transition: load in current active player
            # Check if we have preloaded content for this item
            preload_type, preload_content = self.preloader.get_preloaded_content(item_index)
            
            if preload_type:
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
        
        # Cleanup old preloaded items and preload next items
        self.preloader.cleanup_old_items(item_index, self.preloader.max_preload_count)
        self._preload_next_items(item_index)
        
        # Prepare next item in secondary player for seamless transition
        self._prepare_next_item_in_secondary_player(item_index)
    
    def _load_and_display_item(self, timeline_item: TimelineItem, item_offset: float):
        """
        Load and display a timeline item's media content.
        
        Args:
            timeline_item: The timeline item to display
            item_offset: Playback offset within the item in seconds
        """
        import os
        
        # Prefer composite outputs over legacy files
        video_path = timeline_item.get_composite_video_path()
        image_path = timeline_item.get_composite_image_path()
        
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
            # Prefer composite video over legacy
            video_path = timeline_item.get_composite_video_path()
            self._display_video(video_path, item_offset)
        
        # Note: Don't clear preloader here, we keep preloaded items for smooth transitions
    
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
    
    def _on_media_status_changed(self, status, player_id="primary"):
        """Handle media player status changes.
        
        Args:
            status: Media status from QMediaPlayer
            player_id: Identifier for which player emitted the signal ("primary" or "secondary")
        """
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Determine which player to operate on
            player = self.primary_player if player_id == "primary" else self.secondary_player
            
            # Media is loaded, set position and start playback
            if hasattr(self, '_pending_video_offset'):
                offset_ms = int(self._pending_video_offset * 1000)
                player.setPosition(offset_ms)
                delattr(self, '_pending_video_offset')
            
            # Start playback only if this is the active player
            if self._is_playing and player_id == self._active_player:
                player.play()
    
    def _preload_next_items(self, current_item_index: int):
        """
        Preload the next 3 timeline items for smooth transitions.
        
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
        if item_count == 0:
            return
        
        # Preload next N items (where N = max_preload_count)
        for i in range(1, self.preloader.max_preload_count + 1):
            next_item_index = current_item_index + i
            
            # Handle looping
            if next_item_index > item_count:
                # Loop to beginning if needed
                next_item_index = ((next_item_index - 1) % item_count) + 1
            
            # Get and preload the item
            try:
                next_item = timeline.get_item(next_item_index)
                self.preloader.preload_item(next_item)
            except Exception as e:
                print(f"Error preloading item {next_item_index}: {e}")
                break  # Stop preloading if we encounter an error
    
    def _swap_active_player(self):
        """Swap the active and secondary players for seamless transitions."""
        if self._active_player == "primary":
            # Hide primary, show secondary
            self.primary_video_widget.hide()
            self.secondary_video_widget.show()
            self._active_player = "secondary"
            # Update backward compatibility references
            self.video_widget = self.secondary_video_widget
            self.media_player = self.secondary_player
            self.audio_output = self.secondary_audio_output
        else:
            # Hide secondary, show primary
            self.secondary_video_widget.hide()
            self.primary_video_widget.show()
            self._active_player = "primary"
            # Update backward compatibility references
            self.video_widget = self.primary_video_widget
            self.media_player = self.primary_player
            self.audio_output = self.primary_audio_output
        
        # Clear prepared item since we've consumed it
        self._next_item_prepared = None
    
    def _resume_secondary_player(self, item_offset: float):
        """Resume playback on the secondary player after swapping.
        
        Args:
            item_offset: Playback offset within the item in seconds
        """
        # The secondary player should already be loaded and ready
        # Just set position and start playing if needed
        active_player = self.secondary_player if self._active_player == "secondary" else self.primary_player
        
        if active_player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia:
            # Set position
            offset_ms = int(item_offset * 1000)
            active_player.setPosition(offset_ms)
            
            # Start playback if in playing state
            if self._is_playing:
                active_player.play()
    
    def _prepare_next_item_in_secondary_player(self, current_item_index: int):
        """Prepare the next timeline item in the secondary player for seamless transition.
        
        Args:
            current_item_index: Index of the currently playing item
        """
        project = self.workspace.get_project()
        if not project:
            return
        
        timeline = project.get_timeline()
        if not timeline:
            return
        
        item_count = timeline.get_item_count()
        if item_count == 0:
            return
        
        # Calculate next item index (with looping)
        next_item_index = current_item_index + 1
        if next_item_index > item_count:
            next_item_index = 1  # Loop to beginning
        
        # Get the next timeline item
        try:
            next_item = timeline.get_item(next_item_index)
        except Exception as e:
            print(f"Error getting next timeline item {next_item_index}: {e}")
            return
        
        # Determine which player is secondary (not currently active)
        secondary_player = self.secondary_player if self._active_player == "primary" else self.primary_player
        
        # Prefer composite outputs over legacy files
        import os
        video_path = next_item.get_composite_video_path()
        
        if os.path.exists(video_path):
            # Prepare video in secondary player
            from PySide6.QtCore import QUrl
            url = QUrl.fromLocalFile(video_path)
            secondary_player.setSource(url)
            # Don't start playback yet, just prepare
            self._next_item_prepared = next_item_index
            print(f"Prepared next item {next_item_index} in secondary player")
    
    def resizeEvent(self, event):
        """Handle resize events to update preview geometry."""
        super().resizeEvent(event)
        if self._is_visible:
            self._update_geometry()
