"""
Crew member package for Filmeto.
"""
from enum import Enum
from .crew_member import CrewMember, CrewMemberConfig
from .crew_service import CrewService


class CrewTitle(Enum):
    """Enum for crew member titles with internationalization support."""

    DIRECTOR = "director"
    CINEMATOGRAPHER = "cinematographer"
    EDITOR = "editor"
    PRODUCER = "producer"
    SCREENWRITER = "screenwriter"
    STORYBOARD_ARTIST = "storyboard_artist"
    VFX_SUPERVISOR = "vfx_supervisor"
    SOUND_DESIGNER = "sound_designer"

    def get_title_display(self, lang_code: str = "en") -> str:
        """Get the display title for the crew position in the specified language."""
        titles = {
            "director": {
                "en": "Director",
                "zh": "导演"
            },
            "cinematographer": {
                "en": "Cinematographer",
                "zh": "摄影师"
            },
            "editor": {
                "en": "Editor",
                "zh": "剪辑师"
            },
            "producer": {
                "en": "Producer",
                "zh": "制片人"
            },
            "screenwriter": {
                "en": "Screenwriter",
                "zh": "编剧"
            },
            "storyboard_artist": {
                "en": "Storyboard Artist",
                "zh": "故事板艺术家"
            },
            "vfx_supervisor": {
                "en": "VFX Supervisor",
                "zh": "视觉特效总监"
            },
            "sound_designer": {
                "en": "Sound Designer",
                "zh": "声音设计师"
            }
        }

        return titles[self.value].get(lang_code, titles[self.value]["en"])


__all__ = [
    "CrewMember",
    "CrewMemberConfig",
    "CrewService",
    "CrewTitle",
]
