"""
Utilities for handling markdown files with metadata (frontmatter).

This module provides functions for reading and writing markdown files
that contain YAML metadata enclosed between --- markers at the beginning
of the file.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """
    Parse the frontmatter from a markdown file content.
    
    Args:
        content: The content of the markdown file
        
    Returns:
        A tuple containing (metadata_dict, content_without_frontmatter)
    """
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            meta_str = content[3:end_idx].strip()
            try:
                metadata = yaml.safe_load(meta_str) or {}
            except yaml.YAMLError:
                metadata = {}
            body_content = content[end_idx + 3 :].strip()
            return metadata, body_content
    
    # If no frontmatter found, return empty metadata and full content
    return {}, content.strip()


def read_md_with_meta(file_path: Union[str, Path]) -> tuple[Dict[str, Any], str]:
    """
    Read a markdown file and extract its metadata and content.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        A tuple containing (metadata_dict, content)
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    return parse_frontmatter(content)


def write_md_with_meta(file_path: Union[str, Path], metadata: Dict[str, Any], content: str = "") -> None:
    """
    Write a markdown file with metadata (frontmatter).
    
    Args:
        file_path: Path where the markdown file should be written
        metadata: Dictionary containing the metadata to write
        content: The main content of the markdown file
    """
    # Convert metadata to YAML string
    yaml_str = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    
    # Create content with frontmatter
    full_content = f"---\n{yaml_str}\n---\n{content}"
    
    # Ensure the directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write the content to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(full_content)


def update_md_with_meta(file_path: Union[str, Path], metadata_updates: Dict[str, Any], content: Optional[str] = None) -> bool:
    """
    Update an existing markdown file with new metadata and/or content.
    
    Args:
        file_path: Path to the markdown file to update
        metadata_updates: Dictionary containing metadata fields to update/add
        content: New content to replace the existing content (None to keep current content)
        
    Returns:
        True if the file was updated successfully, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            return False
            
        current_metadata, current_content = read_md_with_meta(file_path)
        
        # Update metadata with new values
        current_metadata.update(metadata_updates)
        
        # Use new content if provided, otherwise keep current content
        updated_content = content if content is not None else current_content
        
        # Write the updated file
        write_md_with_meta(file_path, current_metadata, updated_content)
        
        return True
    except Exception:
        return False


def get_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get only the metadata from a markdown file with frontmatter.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Dictionary containing the metadata
    """
    metadata, _ = read_md_with_meta(file_path)
    return metadata


def get_content(file_path: Union[str, Path]) -> str:
    """
    Get only the content from a markdown file with frontmatter.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        The content without frontmatter
    """
    _, content = read_md_with_meta(file_path)
    return content