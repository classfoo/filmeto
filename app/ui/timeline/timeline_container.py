"""
Timeline Container Widget

This widget provides a container for the timeline that draws a vertical cursor line
following the mouse position. The line is drawn on top of all timeline content
including cards, and mouse tracking works across all child widgets.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPoint, QEvent, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QHoverEvent, QPolygonF, QMouseEvent
from typing import Tuple

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from app.ui.signals import Signals
from app.ui.timeline.video_timeline import VideoTimeline
from app.ui.timeline.subtitle_timeline import SubtitleTimeline
from app.ui.timeline.voice_timeline import VoiceTimeline


class TimelinePositionLineOverlay(QWidget):

    def __init__(self, parent, timeline_position, timeline_x):
        super().__init__(parent)

        # Set transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Don't accept focus to avoid interfering with timeline
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # This widget should not block mouse events for clicking
        # but we'll track position via parent's event filter
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.timeline_position=timeline_position
        self.timeline_x = timeline_x
        self._mouse_x = None
        
        # Throttle timer for cursor updates (limits update frequency while staying responsive)
        self._cursor_update_timer = QTimer(self)
        self._cursor_update_timer.setSingleShot(True)
        self._cursor_update_timer.setInterval(8)  # ~120 FPS max (8ms)
        self._cursor_update_timer.timeout.connect(self._reset_cursor_throttle)
        self._cursor_throttle_active = False
        
        # Separate flags to track what needs updating
        self._cursor_dirty = False
        self._timeline_dirty = False

    def paintEvent(self, event):
        if self._mouse_x is None and self.timeline_x is None:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw timeline position line (higher priority, drawn first so cursor can overlay)
        if self.timeline_x is not None:
            # Draw the vertical line
            pen = QPen(QColor(255, 255, 255, 255))
            pen.setWidth(4)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(self.timeline_x, 0, self.timeline_x, self.height())
            
            # Draw solid triangles at both ends
            # Triangle size
            triangle_size = 8
            
            # Set brush for filled triangles
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.setPen(Qt.PenStyle.NoPen)  # No outline
            
            # Top triangle (pointing up)
            top_triangle = QPolygonF([
                QPointF(self.timeline_x, triangle_size),  # Bottom center point
                QPointF(self.timeline_x - triangle_size, 0),  # Top left
                QPointF(self.timeline_x + triangle_size, 0)   # Top right
            ])
            painter.drawPolygon(top_triangle)
            
            # Bottom triangle (pointing down)
            bottom_y = self.height()
            bottom_triangle = QPolygonF([
                QPointF(self.timeline_x, bottom_y - triangle_size),  # Top center point
                QPointF(self.timeline_x - triangle_size, bottom_y),  # Bottom left
                QPointF(self.timeline_x + triangle_size, bottom_y)   # Bottom right
            ])
            painter.drawPolygon(bottom_triangle)
        
        # Draw mouse cursor line (drawn second to overlay on top if needed)
        if self._mouse_x is not None:
            pen = QPen(QColor(255, 255, 255, 200))
            pen.setWidth(1)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(self._mouse_x, 0, self._mouse_x, self.height())
        
        painter.end()
        
        # Reset dirty flags after painting
        self._cursor_dirty = False
        self._timeline_dirty = False

    def on_timeline_position(self, timeline_position, timeline_x):
        """Update timeline position - immediate update for accuracy"""
        self.timeline_position = timeline_position
        self.timeline_x = timeline_x
        self._timeline_dirty = True
        
        # Timeline updates are critical, apply immediately
        self.update()

    def set_cursor_position(self, x):
        """Update cursor line position - throttled to limit update frequency"""
        if self._mouse_x != x:
            self._mouse_x = x
            self._cursor_dirty = True
            
            # Throttle: Update immediately if not throttled, otherwise skip
            if not self._cursor_throttle_active:
                self.update()
                self._cursor_throttle_active = True
                self._cursor_update_timer.start()
    
    def _reset_cursor_throttle(self):
        """Reset throttle flag to allow next cursor update"""
        self._cursor_throttle_active = False

    def clear_cursor(self):
        """Hide the cursor line - immediate update"""
        if self._mouse_x is not None:
            # Reset throttle state
            self._cursor_update_timer.stop()
            self._cursor_throttle_active = False
            
            self._mouse_x = None
            self._cursor_dirty = True
            self.update()

class TimelineDividerLinesOverlay(QWidget):
    """
    Transparent overlay widget that draws divider lines between the three timeline sections.
    This helps visually distinguish between subtitle, main timeline, and voiceover sections.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # This widget should not block mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Store positions for the divider lines
        self._subtitle_height = 0
        self._voiceover_top = 0
        
    def set_divider_positions(self, subtitle_height, voiceover_top):
        """Update divider line positions"""
        self._subtitle_height = subtitle_height
        self._voiceover_top = voiceover_top
        self.update()
    
    def paintEvent(self, event):
        """Draw the divider lines"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw dashed lines
        pen = QPen(QColor(100, 100, 100, 150))
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Draw line below subtitle timeline
        if self._subtitle_height > 0:
            painter.drawLine(0, self._subtitle_height, self.width(), self._subtitle_height)
            
        # Draw line above voiceover timeline
        if self._voiceover_top > 0:
            painter.drawLine(0, self._voiceover_top, self.width(), self._voiceover_top)
            
        painter.end()


class TimelineContainer(BaseWidget):
    """
    Container widget for the timeline that displays a vertical cursor line.
    
    Uses a transparent overlay to draw the cursor line on top of all timeline
    content while preserving all timeline functionality. Mouse events are tracked
    globally across the container and all child widgets.
    """

    def __init__(self, parent, workspace:Workspace):
        """
        Initialize the timeline container.
        
        Args:
            timeline_widget: The HorizontalTimeline widget to wrap
            parent: Parent widget
        """
        super(TimelineContainer, self).__init__(workspace)
        self.workspace = workspace
        # Timeline card dimensions (from HoverZoomFrame)
        self.card_width = 90  # Fixed width of each card
        self.card_spacing = 5  # Spacing between cards (from timeline_layout.setSpacing(5))
        self.content_margin_left = 5  # Left margin from timeline_layout.setContentsMargins(5, 5, 5, 5)
        # Create the timeline widget
        self.video_timeline = VideoTimeline(self, workspace)
        self.subtitle_timeline = SubtitleTimeline(self, workspace)
        self.voice_timeline = VoiceTimeline(self, workspace)
        
        # Setup the layout to hold the timelines
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        # Subtitle timeline will be added here if needed
        # Main timeline is added here
        self.main_layout.addWidget(self.subtitle_timeline)
        self.main_layout.addWidget(self.video_timeline)
        self.main_layout.addWidget(self.voice_timeline)

        # Create the overlay widget for drawing divider lines
        timeline_position = self.workspace.get_project().get_timeline_position()
        timeline_x, card_index = self.calculate_timeline_x(timeline_position)
        self.timeline_position_overlay = TimelinePositionLineOverlay(self, timeline_position,timeline_x)

        # Create the overlay widget for drawing divider lines
        self.divider_overlay = TimelineDividerLinesOverlay(self)

        # Enable hover events to track mouse globally
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMouseTracking(True)
        
        # Enable mouse press events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Connect to signals for card selection
        Signals().connect(Signals.TIMELINE_POSITION_CLICKED, self._on_timeline_position_signal)
        Signals().connect(Signals.TIMELINE_POSITION_STOPPED, self._on_timeline_position_signal)
        
        # Install event filter to intercept mouse clicks from child widgets
        self.installEventFilter(self)
        self._install_event_filters_recursively(self.video_timeline)
        if self.subtitle_timeline:
            self._install_event_filters_recursively(self.subtitle_timeline)
        if self.voice_timeline:
            self._install_event_filters_recursively(self.voice_timeline)

    def _install_event_filters_recursively(self, widget):
        """Install event filter on widget and all its children recursively"""
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)
    
    def eventFilter(self, watched, event):
        """Filter events from all child widgets to handle timeline position clicks"""
        if event.type() == QEvent.Type.MouseButtonPress:
            mouse_event = event
            if isinstance(mouse_event, QMouseEvent) and mouse_event.button() == Qt.MouseButton.LeftButton:
                # Map the click position to container coordinates
                container_pos = watched.mapTo(self, mouse_event.pos())
                
                # Calculate timeline position and card number from the mapped X coordinate
                timeline_position, card_number = self.calculate_timeline_position(container_pos.x())
                
                # Update the timeline position in project
                # Boundary validation (< 0 or > duration) is handled in set_timeline_position
                project = self.workspace.get_project()
                if project:
                    # Set position in data layer
                    project.set_timeline_position(timeline_position)
                    
                    # Emit UI signal for UI components (like play control) to react
                    Signals().send(Signals.TIMELINE_POSITION_CLICKED, params=timeline_position)
                
                # Don't consume the event - let child widgets handle it for their own logic
                # This allows cards to be selected, subtitle/voiceover cards to be dragged, etc.
        
        # Pass the event to the base class for normal processing
        return super().eventFilter(watched, event)

    def on_timeline_position(self, timeline_position):
        timeline_x, card_index = self.calculate_timeline_x(timeline_position)
        self.timeline_position_overlay.on_timeline_position(timeline_position, timeline_x)
    
    def _on_timeline_position_signal(self, sender, params=None, **kwargs):
        """
        Handle TIMELINE_POSITION_CLICKED and TIMELINE_POSITION_STOPPED signals.
        Calculate card number from timeline position and trigger card selection in data layer.
        
        Args:
            sender: The signal sender
            params: Signal parameters - either:
                   - timeline_position (float) for TIMELINE_POSITION_CLICKED
                   - dict with timeline_position, timeline_x, card_number for TIMELINE_POSITION_STOPPED
            **kwargs: Additional keyword arguments
        """
        if params is None:
            return
        
        # Get timeline_position and card_number from params
        if isinstance(params, dict):
            timeline_position = params.get('timeline_position')
            card_number = params.get('card_number', None)
        else:
            # For TIMELINE_POSITION_CLICKED, params is the position directly
            timeline_position = params
            card_number = None
        
        if timeline_position is None:
            return
        
        # If card_number is not provided, calculate it from timeline_position
        if card_number is None:
            _, card_number = self.calculate_timeline_x(timeline_position)
        
        # Only set item index if card_number is valid (> 0)
        if card_number > 0:
            self.workspace.get_project().get_timeline().set_item_index(card_number)

    def calculate_timeline_position(self, mouse_x: int) -> Tuple[float, int]:
        """
        Calculate the playback position in seconds and card number based on mouse X coordinate.
        
        Args:
            mouse_x: Mouse X coordinate in the container
            
        Returns:
            tuple[float, int]: (Playback position in seconds with millisecond precision, Card number/index)
                              Card number is 1-indexed. Returns 0 if before first card or no cards exist.
        """
        # Get the timeline widget's cards
        timeline = self.video_timeline
        if not hasattr(timeline, 'cards') or not timeline.cards:
            return 0.0, 0
        
        # Get the workspace and project to access timeline items
        workspace = timeline.workspace
        if not workspace:
            return 0.0, 0
            
        project = workspace.get_project()
        if not project:
            return 0.0, 0
            
        timeline_data = project.get_timeline()
        if not timeline_data:
            return 0.0, 0
        
        # Account for scroll position
        scroll_area = timeline.scroll_area
        scroll_offset = scroll_area.horizontalScrollBar().value()
        
        # Adjust mouse position for scroll offset and left margin
        adjusted_x = mouse_x + scroll_offset - self.content_margin_left
        
        # If mouse is before the first card, position is 0
        if adjusted_x < 0:
            return 0.0, 0
        
        # Calculate which card the mouse is over and position within that card
        accumulated_time = 0.0
        current_x = 0
        
        for i, card in enumerate(timeline.cards):
            card_index = i + 1  # Cards are 1-indexed
            
            # Get duration for this card directly from project
            try:
                item_duration = project.get_item_duration(card_index)
            except Exception as e:
                print(f"Error getting duration for card {card_index}: {e}")
                item_duration = 1.0  # Default to 1 second if error
            
            # Calculate card boundaries
            card_start_x = current_x
            card_end_x = current_x + self.card_width
            
            # Check if mouse is within this card
            if adjusted_x >= card_start_x and adjusted_x < card_end_x:
                # Calculate position within the card
                position_in_card = adjusted_x - card_start_x
                # Calculate time fraction within this card
                time_fraction = position_in_card / self.card_width
                # Calculate absolute time position
                position_in_seconds = accumulated_time + (time_fraction * item_duration)
                # Round to millisecond precision (3 decimal places)
                return round(position_in_seconds, 3), card_index
            
            # Move to next card
            accumulated_time += item_duration
            current_x = card_end_x + self.card_spacing
        
        # If mouse is after all cards, return the total duration and last card index
        last_card_index = len(timeline.cards)
        return round(accumulated_time, 3), last_card_index
    
    def calculate_timeline_x(self, timeline_position: float) -> Tuple[int, int]:
        """
        Calculate the X coordinate and card number based on timeline position in seconds (reverse of calculate_timeline_position).
        
        Args:
            timeline_position: Playback position in seconds
            
        Returns:
            tuple[int, int]: (X coordinate in the container, Card number/index)
                            Card number is 1-indexed. Returns 0 if before first card or no cards exist.
        """
        # Get the timeline widget's cards
        timeline = self.video_timeline
        if not hasattr(timeline, 'cards') or not timeline.cards:
            return self.content_margin_left, 0
        
        # Get the workspace and project to access timeline items
        workspace = timeline.workspace
        if not workspace:
            return self.content_margin_left, 0
            
        project = workspace.get_project()
        if not project:
            return self.content_margin_left, 0
            
        timeline_data = project.get_timeline()
        if not timeline_data:
            return self.content_margin_left, 0
        
        # If position is negative or zero, return the start position
        if timeline_position <= 0:
            return self.content_margin_left, 0
        
        # Calculate which card the position falls into
        accumulated_time = 0.0
        current_x = 0
        
        for i, card in enumerate(timeline.cards):
            card_index = i + 1  # Cards are 1-indexed
            
            # Get duration for this card directly from project
            try:
                item_duration = project.get_item_duration(card_index)
            except Exception as e:
                print(f"Error getting duration for card {card_index}: {e}")
                item_duration = 1.0  # Default to 1 second if error
            
            # Calculate card boundaries in time
            card_start_time = accumulated_time
            card_end_time = accumulated_time + item_duration
            
            # Check if position falls within this card's time range
            if timeline_position >= card_start_time and timeline_position < card_end_time:
                # Calculate time offset within this card
                time_in_card = timeline_position - card_start_time
                # Calculate position fraction within this card
                time_fraction = time_in_card / item_duration if item_duration > 0 else 0
                # Calculate X position within the card
                position_in_card = time_fraction * self.card_width
                # Calculate absolute X position (before adjusting for scroll)
                adjusted_x = current_x + position_in_card
                # Convert to container coordinate (add margin, no scroll adjustment for display)
                container_x = adjusted_x + self.content_margin_left
                return int(container_x), card_index
            
            # Move to next card
            accumulated_time += item_duration
            current_x += self.card_width + self.card_spacing
        
        # If position is after all cards, return the position at the end and last card index
        final_x = current_x + self.content_margin_left
        last_card_index = len(timeline.cards)
        return int(final_x), last_card_index

    def _update_divider_positions(self):
        """Update divider line positions based on component heights"""
        subtitle_height = 0
        voiceover_top = 0
        
        if self.subtitle_timeline and not self.subtitle_timeline.isHidden():
            subtitle_height = self.subtitle_timeline.height()
            
        if self.voice_timeline and not self.voice_timeline.isHidden():
            # Calculate position of voiceover timeline
            voiceover_top = self.height() - self.voice_timeline.height()
            
        self.divider_overlay.set_divider_positions(subtitle_height, voiceover_top)
    
    def resizeEvent(self, event):
        """Update overlay size and position when container is resized"""
        super().resizeEvent(event)
        # Position overlay to cover the entire container
        self.timeline_position_overlay.setGeometry(self.rect())
        #self.cursor_overlay.setGeometry(self.rect())
        self.divider_overlay.setGeometry(self.rect())
        self._update_divider_positions()
    
    def event(self, event):
        """
        Override event to track mouse position globally across all child widgets.
        Using HoverMove events allows tracking even when mouse is over cards.
        """
        event_type = event.type()
        
        if event_type == QEvent.Type.HoverMove:
            # Track mouse position anywhere in the container (including over cards)
            hover_event = event
            if isinstance(hover_event, QHoverEvent):
                pos = hover_event.position().toPoint()
                self.timeline_position_overlay.set_cursor_position(pos.x())
        elif event_type == QEvent.Type.HoverEnter:
            # Mouse entered the container
            pos = event.position().toPoint()
            self.timeline_position_overlay.set_cursor_position(pos.x())
            
        elif event_type == QEvent.Type.HoverLeave:
            self.timeline_position_overlay.clear_cursor()
            
        elif event_type == QEvent.Type.Leave:
            self.timeline_position_overlay.clear_cursor()
            
        return super().event(event)