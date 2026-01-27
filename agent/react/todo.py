"""TODO data structures for ReAct pattern."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class TodoStatus(str, Enum):
    """Status of a TODO item."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TodoPatchType(str, Enum):
    """Type of patch operation."""
    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"
    REPLACE = "replace"


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
class TodoPatch:
    """
    A patch operation for TODO list.

    Attributes:
        type: Type of patch operation (add, update, remove, replace)
        item: The TODO item to add/update (for add/update)
        item_id: ID of the item to update/remove (for update/remove)
        items: Full list of items for replace operation
        reason: Reason for this patch (optional)
    """
    type: TodoPatchType
    item: Optional[TodoItem] = None
    item_id: Optional[str] = None
    items: Optional[List[TodoItem]] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "type": self.type.value,
            "reason": self.reason,
        }
        if self.item:
            result["item"] = self.item.to_dict()
        if self.item_id:
            result["item_id"] = self.item_id
        if self.items:
            result["items"] = [item.to_dict() for item in self.items]
        return result

    @classmethod
    def add(cls, item: TodoItem, reason: Optional[str] = None) -> "TodoPatch":
        """Create an ADD patch."""
        return cls(type=TodoPatchType.ADD, item=item, reason=reason)

    @classmethod
    def update(cls, item_id: str, item: TodoItem, reason: Optional[str] = None) -> "TodoPatch":
        """Create an UPDATE patch."""
        return cls(type=TodoPatchType.UPDATE, item_id=item_id, item=item, reason=reason)

    @classmethod
    def remove(cls, item_id: str, reason: Optional[str] = None) -> "TodoPatch":
        """Create a REMOVE patch."""
        return cls(type=TodoPatchType.REMOVE, item_id=item_id, reason=reason)

    @classmethod
    def replace(cls, items: List[TodoItem], reason: Optional[str] = None) -> "TodoPatch":
        """Create a REPLACE patch."""
        return cls(type=TodoPatchType.REPLACE, items=items, reason=reason)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoPatch":
        """Create from dictionary representation."""
        patch_type = TodoPatchType(data.get("type", TodoPatchType.ADD.value))

        item = None
        if data.get("item"):
            item = TodoItem.from_dict(data["item"])

        items = None
        if data.get("items"):
            items = [TodoItem.from_dict(item_data) for item_data in data["items"]]

        return cls(
            type=patch_type,
            item=item,
            item_id=data.get("item_id"),
            items=items,
            reason=data.get("reason"),
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

    def apply_patch(self, patch: TodoPatch) -> "TodoState":
        """Apply a patch and return a new state."""
        import copy

        # Create a shallow copy of the state
        new_state = copy.copy(self)
        new_state.items = copy.copy(self.items)
        new_state.version += 1
        new_state.updated_at = datetime.now().timestamp()

        if patch.type == TodoPatchType.ADD:
            if patch.item:
                # Check if item already exists
                existing_ids = {item.id for item in new_state.items}
                if patch.item.id not in existing_ids:
                    new_state.items.append(patch.item)
                else:
                    # Update existing item
                    new_state.items = [
                        patch.item if item.id == patch.item.id else item
                        for item in new_state.items
                    ]

        elif patch.type == TodoPatchType.UPDATE:
            if patch.item_id and patch.item:
                new_state.items = [
                    patch.item if item.id == patch.item_id else item
                    for item in new_state.items
                ]

        elif patch.type == TodoPatchType.REMOVE:
            if patch.item_id:
                new_state.items = [
                    item for item in new_state.items
                    if item.id != patch.item_id
                ]

        elif patch.type == TodoPatchType.REPLACE:
            if patch.items is not None:
                new_state.items = patch.items

        return new_state

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
