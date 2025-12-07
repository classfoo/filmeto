from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QWheelEvent
from .base_timeline_scroll import BaseTimelineScroll

class VideoTimelineScroll(BaseTimelineScroll):
    """Video timeline scroll area - inherits common scroll behavior from BaseTimelineScroll"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("video_timeline_scroll")