"""
Voice Timeline Scroll Area

Provides horizontal scrolling for the voice timeline.
"""

from .base_timeline_scroll import BaseTimelineScroll


class VoiceTimelineScroll(BaseTimelineScroll):
    """Voice timeline scroll area - inherits common scroll behavior from BaseTimelineScroll"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("voice_timeline_scroll")
