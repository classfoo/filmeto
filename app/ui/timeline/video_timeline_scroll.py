from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QWheelEvent

class VideoTimelineScroll(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("draggable_scroll_area")
        self.setWidgetResizable(True)
        self.drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_start_position is not None:
            delta = event.pos() - self.drag_start_position
            # Only allow horizontal scrolling, disable vertical
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.drag_start_position = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        # Convert vertical wheel scrolling to horizontal scrolling
        # Ignore vertical scrolling completely
        delta = event.angleDelta()
        if delta.y() != 0:
            # Use vertical wheel delta for horizontal scrolling
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.y()
            )
        event.accept()  # Consume the event to prevent vertical scrolling