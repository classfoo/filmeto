"""
Subtitle Timeline Scroll Area

Provides horizontal scrolling for the subtitle timeline.
"""

from .base_timeline_scroll import BaseTimelineScroll


class SubtitleTimelineScroll(BaseTimelineScroll):
    """Subtitle timeline scroll area - inherits common scroll behavior from BaseTimelineScroll"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("subtitle_timeline_scroll")
