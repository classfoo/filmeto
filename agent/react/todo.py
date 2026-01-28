"""TODO data structures for ReAct pattern."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class TodoStatus(str, Enum):
    """Status of a TODO item."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class TodoItem:
    """
    A single TODO item.

    Attributes:
        id: Unique identifier for the TODO item
        title: Brief title of the TODO
        description: Detailed description (optional)
        status: Current status of the TODO
        priority: Priority level (1-5, 5 being highest)
        dependencies: List of TODO IDs that this TODO depends on
        metadata: Additional information about the TODO
        created_at: Creation timestamp
        updated_at: Last update timestamp
        completed_at: Completion timestamp (if completed)
    """
    id: str
    title: str
    description: Optional[str] = None
    status: TodoStatus = TodoStatus.PENDING
    priority: int = 3
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoItem":
        """Create from dictionary representation."""
        status = TodoStatus(data.get("status", TodoStatus.PENDING.value))
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=status,
            priority=data.get("priority", 3),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
            completed_at=data.get("completed_at"),
        )


@dataclass
class TodoState:
    """
    Complete TODO state.

    Attributes:
        items: List of all TODO items
        version: Monotonically increasing version number
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    items: List[TodoItem] = field(default_factory=list)
    version: int = 0
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "items": [item.to_dict() for item in self.items],
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoState":
        """Create from dictionary representation."""
        items = [TodoItem.from_dict(item_data) for item_data in data.get("items", [])]
        return cls(
            items=items,
            version=data.get("version", 0),
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
        )

    def get_item_by_id(self, item_id: str) -> Optional[TodoItem]:
        """Get a TODO item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def get_pending_items(self) -> List[TodoItem]:
        """Get all pending TODO items."""
        return [item for item in self.items if item.status == TodoStatus.PENDING]

    def get_in_progress_items(self) -> List[TodoItem]:
        """Get all in-progress TODO items."""
        return [item for item in self.items if item.status == TodoStatus.IN_PROGRESS]

    def get_completed_items(self) -> List[TodoItem]:
        """Get all completed TODO items."""
        return [item for item in self.items if item.status == TodoStatus.COMPLETED]

    def is_completed(self) -> bool:
        """Check if all TODOs are completed."""
        if not self.items:
            return True
        return all(item.status == TodoStatus.COMPLETED for item in self.items)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the TODO state."""
        return {
            "total": len(self.items),
            "pending": len([i for i in self.items if i.status == TodoStatus.PENDING]),
            "in_progress": len([i for i in self.items if i.status == TodoStatus.IN_PROGRESS]),
            "completed": len([i for i in self.items if i.status == TodoStatus.COMPLETED]),
            "failed": len([i for i in self.items if i.status == TodoStatus.FAILED]),
            "blocked": len([i for i in self.items if i.status == TodoStatus.BLOCKED]),
            "version": self.version,
        }
