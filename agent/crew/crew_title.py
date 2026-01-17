"""
Module for managing crew titles and their importance in film production.
"""

from enum import Enum
from typing import List, Optional


class CrewTitle(Enum):
    """
    Enum representing different crew titles in film production with their importance levels.
    The order of declaration indicates importance, with earlier entries being more important.
    """
    PRODUCER = "producer"
    DIRECTOR = "director"
    SCREENWRITER = "screenwriter"
    CINEMATOGRAPHER = "cinematographer"
    EDITOR = "editor"
    SOUND_DESIGNER = "sound_designer"
    VFX_SUPERVISOR = "vfx_supervisor"
    STORYBOARD_ARTIST = "storyboard_artist"
    OTHER = "other"

    @classmethod
    def get_importance_order(cls) -> List[str]:
        """
        Get the importance order of crew titles as a list of strings.
        
        Returns:
            List of crew title strings in order of importance (most important first)
        """
        return [title.value for title in cls]

    @classmethod
    def get_title_importance_rank(cls, title: str) -> int:
        """
        Get the importance rank of a crew title (lower number means higher importance).
        
        Args:
            title: The crew title string to check
            
        Returns:
            Integer rank (0 for most important, higher numbers for less important)
            Returns len(get_importance_order()) for unknown titles
        """
        importance_order = cls.get_importance_order()
        try:
            return importance_order.index(title)
        except ValueError:
            # If the title is not in our predefined list, assign lowest importance
            return len(importance_order)

    @classmethod
    def from_string(cls, title: str) -> Optional['CrewTitle']:
        """
        Create a CrewTitle from a string representation.
        
        Args:
            title: String representation of the crew title
            
        Returns:
            CrewTitle enum value or None if not found
        """
        for crew_title in cls:
            if crew_title.value == title:
                return crew_title
        return None

    @classmethod
    def is_valid_title(cls, title: str) -> bool:
        """
        Check if a given string is a valid crew title.
        
        Args:
            title: String to check
            
        Returns:
            True if the title is valid, False otherwise
        """
        return cls.from_string(title) is not None


def sort_crew_members_by_title_importance(crew_members) -> List:
    """
    Sort crew members based on the importance of their crew titles.
    
    Args:
        crew_members: List or dictionary of crew members to sort
        
    Returns:
        Sorted list of crew members based on title importance
    """
    def get_importance_rank(crew_member):
        # Get the crew title from the crew member's metadata
        crew_title = getattr(crew_member, 'config', {}).metadata.get('crew_title', 'other')
        return CrewTitle.get_title_importance_rank(crew_title)
    
    # If it's a dictionary, convert to list of values
    if isinstance(crew_members, dict):
        crew_list = list(crew_members.values())
    else:
        crew_list = list(crew_members)
    
    # Sort based on importance rank
    sorted_crew = sorted(crew_list, key=get_importance_rank)
    return sorted_crew