"""
Base Timeline Scroll Area

Provides common scrolling functionality for all timeline components.
This base class implements:
- Horizontal-only scrolling
- Mouse drag-to-scroll
- Mouse wheel scrolling
- Performance optimizations
"""

from PySide6.QtWidgets import QScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QWheelEvent, QMouseEvent


class BaseTimelineScroll(QScrollArea):
    """
    Base scroll area for timeline components with horizontal scrolling support.
    
    Features:
    - Horizontal-only scrolling (vertical disabled)
    - Mouse drag to scroll
    - Mouse wheel scrolling (converts vertical to horizontal)
    - Performance optimized with cached scrollbar reference
    """
    
    # Signal emitted when scrolling starts (user initiated)
    scroll_started = Signal()
    
    # Signal emitted when scrolling stops
    scroll_stopped = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("base_timeline_scroll")
        self.setWidgetResizable(True)
        
        # Scrollbar policies - horizontal only
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Drag-to-scroll state
        self.drag_start_position = None
        self._is_dragging = False
        
        # Cache scrollbar reference for performance
        self._h_scrollbar = self.horizontalScrollBar()
        
        # Performance optimization: reduce unnecessary repaints
        # Enable opaque painting on viewport
        if self.viewport():
            self.viewport().setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        
        # Scroll state tracking
        self._is_scrolling = False

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press to start drag-to-scroll"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            self._is_dragging = False  # Not dragging yet, just pressed
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move to perform drag-to-scroll"""
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_start_position is not None:
            delta = event.pos() - self.drag_start_position
            
            # Only start scrolling if moved more than a few pixels
            if not self._is_dragging and (abs(delta.x()) > 3 or abs(delta.y()) > 3):
                self._is_dragging = True
                if not self._is_scrolling:
                    self._is_scrolling = True
                    self.scroll_started.emit()
            
            if self._is_dragging:
                # Only allow horizontal scrolling, disable vertical
                self._h_scrollbar.setValue(self._h_scrollbar.value() - delta.x())
                self.drag_start_position = event.pos()
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to end drag-to-scroll"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = None
            if self._is_dragging:
                self._is_dragging = False
                if self._is_scrolling:
                    self._is_scrolling = False
                    self.scroll_stopped.emit()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """
        Handle mouse wheel events for horizontal scrolling.
        Converts vertical wheel movement to horizontal scrolling.
        """
        delta = event.angleDelta()
        
        # Emit scroll started on first wheel event
        if not self._is_scrolling:
            self._is_scrolling = True
            self.scroll_started.emit()
        
        if delta.x() != 0:
            # If there's horizontal scroll delta, use it directly
            self._h_scrollbar.setValue(self._h_scrollbar.value() - delta.x())
        elif delta.y() != 0:
            # Use vertical wheel delta for horizontal scrolling
            # This preserves natural scrolling behavior
            self._h_scrollbar.setValue(self._h_scrollbar.value() - delta.y())
        
        event.accept()  # Consume the event to prevent vertical scrolling
        
        # Note: scroll_stopped signal will be emitted by TimelineContainer
        # when it detects scrollbar has stopped changing
    
    def get_horizontal_scrollbar(self):
        """Get the horizontal scrollbar (cached for performance)"""
        return self._h_scrollbar
