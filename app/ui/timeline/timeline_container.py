"""
Timeline Container Widget

This widget provides a container for the timeline that draws a vertical cursor line
following the mouse position. The line is drawn on top of all timeline content
including cards, and mouse tracking works across all child widgets.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPoint, QEvent, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QHoverEvent, QPolygonF

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget

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

    def paintEvent(self, event):
        if self.timeline_x is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw the vertical line
            pen = QPen(QColor(255, 255, 255, 200))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(self.timeline_x, 0, self.timeline_x, self.height())
            
            # Draw solid triangles at both ends
            # Triangle size
            triangle_size = 6
            
            # Set brush for filled triangles
            painter.setBrush(QColor(255, 255, 255, 200))
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
            
            painter.end()

    def on_timeline_position(self, timeline_position, timeline_x):
        self.timeline_position = timeline_position
        self.timeline_x = timeline_x
        self.update()

class TimelineCursorLineOverlay(QWidget):
    """
    Transparent overlay widget that draws the cursor line on top of all content.
    This widget sits above the timeline and draws the line while being transparent
    to mouse events for clicks, but tracks mouse position via hover events.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Current mouse position (None when mouse is not over)
        self._mouse_x = None
        
        # Set transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Don't accept focus to avoid interfering with timeline
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # This widget should not block mouse events for clicking
        # but we'll track position via parent's event filter
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        """Draw the vertical cursor line"""
        if self._mouse_x is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            pen = QPen(QColor(255, 255, 255, 200))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            
            painter.drawLine(self._mouse_x, 0, self._mouse_x, self.height())
            painter.end()
    
    def set_cursor_position(self, x):
        """Update cursor line position"""
        if self._mouse_x != x:
            self._mouse_x = x
            self.update()
    
    def clear_cursor(self):
        """Hide the cursor line"""
        if self._mouse_x is not None:
            self._mouse_x = None
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

    def __init__(self, timeline_widget, parent, workspace:Workspace):
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

        # Store reference to the timeline widget
        self.timeline_widget = timeline_widget
        
        # Create layouts for subtitle and voiceover timelines
        self.subtitle_timeline = None
        self.voiceover_timeline = None
        
        # Setup the layout to hold the timelines
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        # Subtitle timeline will be added here if needed
        # Main timeline is added here
        self.main_layout.addWidget(self.timeline_widget)
        # Voiceover timeline will be added here if needed

        # Create the overlay widget for drawing the cursor line
        self.cursor_overlay = TimelineCursorLineOverlay(self)
        self.cursor_overlay.hide()  # Hidden initially

        # Create the overlay widget for drawing divider lines
        self.divider_overlay = TimelineDividerLinesOverlay(self)

        # Create the overlay widget for drawing divider lines
        timeline_position = self.workspace.get_project().get_timeline_position()
        timeline_x = self.calculate_timeline_x(timeline_position)
        self.timeline_position_overlay = TimelinePositionLineOverlay(self, timeline_position,timeline_x)

        # Enable hover events to track mouse globally
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setMouseTracking(True)

    def set_subtitle_timeline(self, subtitle_timeline):
        """
        设置字幕时间线组件
        
        Args:
            subtitle_timeline: SubtitleTimeline 实例
        """
        if self.subtitle_timeline:
            self.main_layout.removeWidget(self.subtitle_timeline)
            self.subtitle_timeline.deleteLater()
            
        self.subtitle_timeline = subtitle_timeline
        self.main_layout.insertWidget(0, self.subtitle_timeline)
        self._update_divider_positions()
    
    def set_voiceover_timeline(self, voiceover_timeline):
        """
        设置配音时间线组件
        
        Args:
            voiceover_timeline: VoiceoverTimeline 实例
        """
        if self.voiceover_timeline:
            self.main_layout.removeWidget(self.voiceover_timeline)
            self.voiceover_timeline.deleteLater()
            
        self.voiceover_timeline = voiceover_timeline
        self.main_layout.addWidget(self.voiceover_timeline)
        self._update_divider_positions()

    def on_timeline_position(self, timeline_position):
        self.timeline_position_overlay.on_timeline_position(timeline_position, self.calculate_timeline_x(timeline_position))

    def calculate_timeline_position(self, mouse_x: int) -> float:
        """
        Calculate the playback position in seconds based on mouse X coordinate.
        
        Args:
            mouse_x: Mouse X coordinate in the container
            
        Returns:
            float: Playback position in seconds (with millisecond precision)
        """
        # Get the timeline widget's cards
        timeline = self.timeline_widget
        if not hasattr(timeline, 'cards') or not timeline.cards:
            return 0.0
        
        # Get the workspace and project to access timeline items
        workspace = timeline.workspace
        if not workspace:
            return 0.0
            
        project = workspace.get_project()
        if not project:
            return 0.0
            
        timeline_data = project.get_timeline()
        if not timeline_data:
            return 0.0
        
        # Account for scroll position
        scroll_area = timeline.scroll_area
        scroll_offset = scroll_area.horizontalScrollBar().value()
        
        # Adjust mouse position for scroll offset and left margin
        adjusted_x = mouse_x + scroll_offset - self.content_margin_left
        
        # If mouse is before the first card, position is 0
        if adjusted_x < 0:
            return 0.0
        
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
                return round(position_in_seconds, 3)
            
            # Move to next card
            accumulated_time += item_duration
            current_x = card_end_x + self.card_spacing
        
        # If mouse is after all cards, return the total duration
        return round(accumulated_time, 3)
    
    def calculate_timeline_x(self, timeline_position: float) -> int:
        """
        Calculate the X coordinate based on timeline position in seconds (reverse of calculate_timeline_position).
        
        Args:
            timeline_position: Playback position in seconds
            
        Returns:
            int: X coordinate in the container (accounting for scroll and margin)
        """
        # Get the timeline widget's cards
        timeline = self.timeline_widget
        if not hasattr(timeline, 'cards') or not timeline.cards:
            return self.content_margin_left
        
        # Get the workspace and project to access timeline items
        workspace = timeline.workspace
        if not workspace:
            return self.content_margin_left
            
        project = workspace.get_project()
        if not project:
            return self.content_margin_left
            
        timeline_data = project.get_timeline()
        if not timeline_data:
            return self.content_margin_left
        
        # If position is negative or zero, return the start position
        if timeline_position <= 0:
            return self.content_margin_left
        
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
                return int(container_x)
            
            # Move to next card
            accumulated_time += item_duration
            current_x += self.card_width + self.card_spacing
        
        # If position is after all cards, return the position at the end
        final_x = current_x + self.content_margin_left
        return int(final_x)

    def _update_divider_positions(self):
        """Update divider line positions based on component heights"""
        subtitle_height = 0
        voiceover_top = 0
        
        if self.subtitle_timeline and not self.subtitle_timeline.isHidden():
            subtitle_height = self.subtitle_timeline.height()
            
        if self.voiceover_timeline and not self.voiceover_timeline.isHidden():
            # Calculate position of voiceover timeline
            voiceover_top = self.height() - self.voiceover_timeline.height()
            
        self.divider_overlay.set_divider_positions(subtitle_height, voiceover_top)
    
    def resizeEvent(self, event):
        """Update overlay size and position when container is resized"""
        super().resizeEvent(event)
        # Position overlay to cover the entire container
        self.timeline_position_overlay.setGeometry(self.rect())
        self.cursor_overlay.setGeometry(self.rect())
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
                self.cursor_overlay.set_cursor_position(pos.x())
                if not self.cursor_overlay.isVisible():
                    self.cursor_overlay.show()
                    self.cursor_overlay.raise_()  # Ensure overlay is on top
        elif event_type == QEvent.Type.HoverEnter:
            # Mouse entered the container
            self.cursor_overlay.show()
            self.cursor_overlay.raise_()
            
        elif event_type == QEvent.Type.HoverLeave:
            # Mouse left the container
            self.cursor_overlay.hide()
            self.cursor_overlay.clear_cursor()
            
        elif event_type == QEvent.Type.Leave:
            # Additional leave event handling
            self.cursor_overlay.hide()
            self.cursor_overlay.clear_cursor()
            
        return super().event(event)