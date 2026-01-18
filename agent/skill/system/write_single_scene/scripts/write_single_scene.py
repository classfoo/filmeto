#!/usr/bin/env python3
"""
Single Scene Writing Skill Script
This script writes and updates individual scenes in the project's screenplay manager.
"""
import json
import sys
import argparse
from typing import Dict, Any, Optional
import os
from datetime import datetime

# Add the project root to the Python path to import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from app.data.screen_play import ScreenPlayScene


def write_single_scene(
    scene_id: str,
    title: str,
    content: str,
    project_path: str,
    scene_number: Optional[str] = None,
    location: Optional[str] = None,
    time_of_day: Optional[str] = None,
    genre: Optional[str] = None,
    logline: Optional[str] = None,
    characters: Optional[list] = None,
    story_beat: Optional[str] = None,
    page_count: Optional[int] = None,
    duration_minutes: Optional[int] = None,
    tags: Optional[list] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Write or update a single scene in the project's screenplay manager.
    
    Args:
        scene_id: Unique identifier for the scene
        title: Title of the scene
        content: Content of the scene in screenplay format
        project_path: Path to the project directory
        scene_number: Scene number in the screenplay
        location: Location of the scene
        time_of_day: Time of day for the scene
        genre: Genre of the screenplay
        logline: Logline for the scene
        characters: List of characters appearing in the scene
        story_beat: Story beat or plot point for the scene
        page_count: Estimated page count for the scene
        duration_minutes: Estimated duration in minutes
        tags: Tags for categorizing the scene
        status: Status of the scene (draft, revised, final)
        
    Returns:
        Result dictionary with success status and scene info
    """
    try:
        # Import the project module to access the screenplay manager
        from app.data.project import Project
        
        # Create a mock workspace object for the project
        class MockWorkspace:
            def __init__(self, root_path):
                self.root_path = root_path
                self.settings = {"general.language": "en"}
        
        # Create a project instance
        workspace = MockWorkspace(project_path)
        project_name = os.path.basename(project_path)
        project = Project(workspace, project_path, project_name)
        
        # Try to get the existing scene to preserve unchanged metadata
        existing_scene = project.screenplay_manager.get_scene(scene_id)
        
        # Prepare metadata for the scene
        metadata = {}
        
        # If scene exists, start with its current metadata
        if existing_scene:
            # Update existing scene - use current values as defaults
            metadata = {
                "scene_number": scene_number if scene_number is not None else existing_scene.scene_number,
                "location": location if location is not None else existing_scene.location,
                "time_of_day": time_of_day if time_of_day is not None else existing_scene.time_of_day,
                "genre": genre if genre is not None else existing_scene.genre,
                "logline": logline if logline is not None else existing_scene.logline,
                "characters": characters if characters is not None else existing_scene.characters,
                "story_beat": story_beat if story_beat is not None else existing_scene.story_beat,
                "page_count": page_count if page_count is not None else existing_scene.page_count,
                "duration_minutes": duration_minutes if duration_minutes is not None else existing_scene.duration_minutes,
                "tags": tags if tags is not None else existing_scene.tags,
                "status": status if status is not None else existing_scene.status,
                "revision_number": existing_scene.revision_number + 1,  # Increment revision
                "created_at": existing_scene.created_at,  # Keep original creation time
                "updated_at": datetime.now().isoformat()  # Update with current time
            }
        else:
            # Creating new scene - use provided values or defaults
            metadata = {
                "scene_number": scene_number or "",
                "location": location or "",
                "time_of_day": time_of_day or "",
                "genre": genre or "General",
                "logline": logline or title,
                "characters": characters or [],
                "story_beat": story_beat or "",
                "page_count": page_count or 0,
                "duration_minutes": duration_minutes or 0,
                "tags": tags or [],
                "status": status or "draft",
                "revision_number": 1,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Create a ScreenPlayScene instance with the metadata
        scene = ScreenPlayScene(
            scene_id=scene_id,
            title=title,
            content=content,
            scene_number=metadata["scene_number"],
            location=metadata["location"],
            time_of_day=metadata["time_of_day"],
            genre=metadata["genre"],
            logline=metadata["logline"],
            characters=metadata["characters"],
            story_beat=metadata["story_beat"],
            page_count=metadata["page_count"],
            duration_minutes=metadata["duration_minutes"],
            tags=metadata["tags"],
            status=metadata["status"],
            revision_number=metadata["revision_number"],
            created_at=metadata["created_at"],
            updated_at=metadata["updated_at"]
        )
        
        # Determine if we're creating a new scene or updating an existing one
        if existing_scene:
            # Update the existing scene
            success = project.screenplay_manager.update_scene(
                scene_id=scene_id,
                title=title,
                content=content,
                metadata_updates=scene.to_dict()  # Use to_dict to get all attributes
            )
            action = "updated"
        else:
            # Create a new scene
            success = project.screenplay_manager.create_scene(
                scene_id=scene_id,
                title=title,
                content=content,
                metadata=scene.to_dict()  # Use to_dict to get all attributes
            )
            action = "created"
        
        if success:
            result = {
                "success": True,
                "action": action,
                "scene_id": scene_id,
                "title": title,
                "message": f"Scene '{scene_id}' successfully {action}."
            }
        else:
            result = {
                "success": False,
                "scene_id": scene_id,
                "message": f"Failed to {action} scene '{scene_id}'."
            }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error writing single scene: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(description="Write or update a single scene in the screenplay")
    parser.add_argument("--scene-id", type=str, required=True, help="Unique identifier for the scene")
    parser.add_argument("--title", type=str, required=True, help="Title of the scene")
    parser.add_argument("--content", type=str, required=True, help="Content of the scene in screenplay format")
    parser.add_argument("--project-path", type=str, required=True, help="Path to the project directory")
    parser.add_argument("--scene-number", type=str, help="Scene number in the screenplay")
    parser.add_argument("--location", type=str, help="Location of the scene")
    parser.add_argument("--time-of-day", type=str, help="Time of day for the scene")
    parser.add_argument("--genre", type=str, help="Genre of the screenplay")
    parser.add_argument("--logline", type=str, help="Logline for the scene")
    parser.add_argument("--characters", type=str, nargs='+', help="Characters appearing in the scene")
    parser.add_argument("--story-beat", type=str, help="Story beat or plot point for the scene")
    parser.add_argument("--page-count", type=int, help="Estimated page count for the scene")
    parser.add_argument("--duration-minutes", type=int, help="Estimated duration in minutes")
    parser.add_argument("--tags", type=str, nargs='+', help="Tags for categorizing the scene")
    parser.add_argument("--status", type=str, help="Status of the scene (draft, revised, final)")
    
    args = parser.parse_args()
    
    try:
        result = write_single_scene(
            scene_id=args.scene_id,
            title=args.title,
            content=args.content,
            project_path=args.project_path,
            scene_number=args.scene_number,
            location=args.location,
            time_of_day=args.time_of_day,
            genre=args.genre,
            logline=args.logline,
            characters=args.characters,
            story_beat=args.story_beat,
            page_count=args.page_count,
            duration_minutes=args.duration_minutes,
            tags=args.tags,
            status=args.status
        )
        
        # Print the result as JSON
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "message": f"Error in single scene writing: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()