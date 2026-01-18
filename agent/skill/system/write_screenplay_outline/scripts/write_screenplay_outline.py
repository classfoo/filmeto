#!/usr/bin/env python3
"""
Screenplay Outline Writing Skill Script
This script generates screenplay outlines and creates scenes in the project's screenplay manager.
"""
import json
import sys
import argparse
from typing import Dict, List, Any
import os
import yaml
from datetime import datetime

# Add the project root to the Python path to import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from app.data.screen_play import ScreenPlayScene


def generate_screenplay_outline(concept: str, genre: str = "General", num_scenes: int = 10) -> List[Dict[str, Any]]:
    """
    Generate a screenplay outline based on the provided concept.

    Args:
        concept: The basic concept or idea for the screenplay
        genre: The genre of the screenplay
        num_scenes: Number of scenes to generate in the outline

    Returns:
        A list of scene dictionaries with structure information
    """
    # This is a simplified implementation - in a real system, this would use an LLM
    # to generate a more sophisticated outline based on the concept

    # Sample outline generation logic
    outline = []

    # Define some common scene types and locations for variety
    scene_types = [
        "establishing shot", "character introduction", "conflict setup",
        "rising action", "subplot development", "character development",
        "plot twist", "climax setup", "climactic scene", "resolution"
    ]

    locations = [
        "INT. MAIN CHARACTER'S APARTMENT - DAY",
        "EXT. CITY STREET - DAY",
        "INT. OFFICE BUILDING - DAY",
        "EXT. PARK - DAY",
        "INT. RESTAURANT - NIGHT",
        "EXT. SUBURBAN HOME - DAY",
        "INT. POLICE STATION - DAY",
        "EXT. INDUSTRIAL AREA - NIGHT"
    ]

    characters = [
        "ALEX", "JORDAN", "MAYA", "RILEY", "QUINN",
        "CAMERON", "PAYER", "DREW", "CASEY", "FINLEY"
    ]

    # Generate scenes based on the concept
    for i in range(min(num_scenes, len(scene_types))):
        scene_type = scene_types[i % len(scene_types)]
        location = locations[i % len(locations)]
        character_set = [characters[j % len(characters)] for j in range((i % 3) + 1)]

        scene = {
            "scene_number": f"{i+1:02d}",
            "location": location.split(" - ")[0][5:],  # Extract location without INT./EXT.
            "time_of_day": location.split(" - ")[1],  # Extract time of day
            "setup": f"{scene_type.replace('_', ' ').title()} scene",
            "characters": character_set,
            "logline": f"Scene {i+1}: {scene_type.replace('_', ' ').title()} in {location.split(' - ')[0][5:]}",
            "story_beat": scene_type,
            "content": f"# {location}\n\n% The {scene_type.replace('_', ' ')} scene unfolds here.\n\n**{character_set[0]}**\nWhat brings us to this moment?\n\n% More scene content would be developed here based on the concept...",
            "duration_minutes": 2 + (i % 3),  # Vary duration between 2-4 minutes
            "tags": [genre.lower(), scene_type.replace(" ", "_")]
        }

        outline.append(scene)

    return outline


def write_screenplay_scenes(outline: List[Dict[str, Any]], project_path: str) -> Dict[str, Any]:
    """
    Write screenplay scenes to the project's screenplay manager based on the outline.

    Args:
        outline: The screenplay outline to convert to scenes
        project_path: Path to the project directory

    Returns:
        Result dictionary with success status and created scene IDs
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

        created_scenes = []
        failed_scenes = []

        # Create scenes from the outline
        for i, scene_data in enumerate(outline):
            scene_id = f"scene_{scene_data['scene_number'].zfill(3)}"

            try:
                # Create a ScreenPlayScene instance
                scene = ScreenPlayScene(
                    scene_id=scene_id,
                    title=scene_data['logline'],
                    content=scene_data['content'],
                    scene_number=scene_data['scene_number'],
                    location=scene_data['location'],
                    time_of_day=scene_data['time_of_day'],
                    genre=scene_data.get('genre', 'General'),
                    logline=scene_data['logline'],
                    characters=scene_data['characters'],
                    story_beat=scene_data['story_beat'],
                    page_count=len(scene_data['content'].split('\n')) // 10,  # Rough estimate
                    duration_minutes=scene_data['duration_minutes'],
                    tags=scene_data['tags'],
                    status="draft",
                    revision_number=1,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )

                # Use the project's screenplay manager to create the scene
                success = project.screenplay_manager.create_scene(
                    scene_id=scene_id,
                    title=scene.title,
                    content=scene.content,
                    metadata=scene.to_dict()  # Use the to_dict method to get all attributes
                )

                if success:
                    created_scenes.append(scene_id)
                else:
                    failed_scenes.append(scene_id)

            except Exception as e:
                failed_scenes.append(scene_id)

        result = {
            "success": len(failed_scenes) == 0,
            "total_scenes": len(outline),
            "created_scenes": created_scenes,
            "failed_scenes": failed_scenes,
            "message": f"Successfully created {len(created_scenes)} out of {len(outline)} scenes."
        }

        if failed_scenes:
            result["message"] += f" Failed to create {len(failed_scenes)} scenes: {failed_scenes}."

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error writing screenplay scenes: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(description="Generate screenplay outline and create scenes in project")
    parser.add_argument("--concept", type=str, required=True, help="The screenplay concept or idea")
    parser.add_argument("--genre", type=str, default="General", help="The genre of the screenplay")
    parser.add_argument("--num-scenes", type=int, default=10, help="Number of scenes to generate")
    parser.add_argument("--project-path", type=str, required=True, help="Path to the project directory")
    
    args = parser.parse_args()
    
    try:
        # Generate the screenplay outline
        outline = generate_screenplay_outline(args.concept, args.genre, args.num_scenes)
        
        # Write the scenes to the project's screenplay manager
        result = write_screenplay_scenes(outline, args.project_path)
        
        # Print the result as JSON
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "message": f"Error in screenplay outline generation: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()