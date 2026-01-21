from typing import List, Dict, Any, Optional
import os
import yaml


class Soul:
    """
    Represents a Soul with name, skills, and detailed information from an MD file.
    """
    
    def __init__(self, name: str, skills: List[str], description_file: str):
        """
        Initialize a Soul instance.
        
        Args:
            name: The name of the soul
            skills: A list of skills the soul is proficient in
            description_file: Path to the MD file containing detailed information
        """
        self.name = name
        self.skills = skills
        self.description_file = description_file
        self._metadata: Optional[Dict[str, Any]] = None
        self._knowledge: Optional[str] = None
        
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """Get the metadata from the description file."""
        if self._metadata is None:
            self._parse_description_file()
        return self._metadata
    
    @property
    def knowledge(self) -> Optional[str]:
        """Get the knowledge section from the description file."""
        if self._knowledge is None:
            self._parse_description_file()
        return self._knowledge
    
    def _parse_description_file(self):
        """Parse the description MD file to extract metadata and knowledge."""
        if not os.path.exists(self.description_file):
            return

        # Use md_with_meta_utils to read the file
        from utils.md_with_meta_utils import read_md_with_meta
        self._metadata, self._knowledge = read_md_with_meta(self.description_file)
    
    def __repr__(self):
        return f"Soul(name='{self.name}', skills={self.skills}, description_file='{self.description_file}')"
    
    def __eq__(self, other):
        if not isinstance(other, Soul):
            return False
        return (
            self.name == other.name
            and self.skills == other.skills
            and self.description_file == other.description_file
        )