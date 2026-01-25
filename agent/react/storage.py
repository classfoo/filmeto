import json
import os
import time
from pathlib import Path
from typing import Optional
from .types import CheckpointData


class ReactStorage:
    """
    Handles file-based storage for ReAct checkpoints and related data.
    """
    
    def __init__(self, project_name: str, react_type: str, workspace_root: str = "workspace"):
        self.project_name = project_name
        self.react_type = react_type
        self.workspace_root = Path(workspace_root)
        
        # Define the storage path
        self.storage_path = (
            self.workspace_root / "projects" / project_name / "agent" / "react" / react_type
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Define file paths
        self.checkpoint_file = self.storage_path / "checkpoint.json"
        self.history_file = self.storage_path / "history.jsonl"
        self.config_file = self.storage_path / "config.json"
    
    def save_checkpoint(self, checkpoint_data: CheckpointData) -> None:
        """
        Save checkpoint data to file.
        """
        checkpoint_data.updated_at = time.time()
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data.__dict__, f, indent=2, ensure_ascii=False)
    
    def load_checkpoint(self) -> Optional[CheckpointData]:
        """
        Load checkpoint data from file.
        """
        if not self.checkpoint_file.exists():
            return None
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create CheckpointData instance from loaded data
            return CheckpointData(
                run_id=data['run_id'],
                step_id=data['step_id'],
                status=data['status'],
                messages=data['messages'],
                pending_user_messages=data['pending_user_messages'],
                last_tool_calls=data.get('last_tool_calls'),
                last_tool_results=data.get('last_tool_results'),
                created_at=data.get('created_at', time.time()),
                updated_at=data.get('updated_at', time.time())
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            # If there's an issue with the checkpoint file, return None
            return None
    
    def append_to_history(self, event: dict) -> None:
        """
        Append an event to the history file.
        """
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')
    
    def clear_history(self) -> None:
        """
        Clear the history file.
        """
        if self.history_file.exists():
            self.history_file.unlink()
    
    def save_config(self, config: dict) -> None:
        """
        Save configuration to file.
        """
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def load_config(self) -> Optional[dict]:
        """
        Load configuration from file.
        """
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            return None
