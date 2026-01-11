"""Base skill framework for agent capabilities."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class SkillStatus(str, Enum):
    """Status of skill execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_HELP = "needs_help"
    RETRY = "retry"


@dataclass
class SkillResult:
    """Result of skill execution."""
    status: SkillStatus
    output: Any
    message: str
    metadata: Dict[str, Any]
    requires_help: Optional[str] = None  # Agent name that could help
    quality_score: Optional[float] = None  # Quality score 0.0-1.0
    
    def is_satisfactory(self, threshold: float = 0.7) -> bool:
        """Check if result is satisfactory based on quality score."""
        if self.quality_score is None:
            return self.status == SkillStatus.SUCCESS
        return self.quality_score >= threshold


@dataclass
class SkillContext:
    """Context for skill execution."""
    workspace: Any
    project: Any
    agent_name: str
    parameters: Dict[str, Any]
    shared_state: Dict[str, Any]  # Shared state between agents
    tool_registry: Any  # Tool registry for tool access
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a tool from the registry."""
        if self.tool_registry:
            return self.tool_registry.get_tool(tool_name)
        return None
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool."""
        tool = self.get_tool(tool_name)
        if tool:
            return tool._run(**kwargs)
        raise ValueError(f"Tool '{tool_name}' not found")


class BaseSkill(ABC):
    """
    Base class for agent skills.
    
    A skill packages multiple tool calls into a cohesive capability.
    Skills can be executed by agents to perform complex tasks.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        required_tools: Optional[List[str]] = None,
        agent_name: Optional[str] = None
    ):
        """
        Initialize skill.
        
        Args:
            name: Skill name
            description: Skill description
            required_tools: List of required tool names
            agent_name: Name of agent that owns this skill
        """
        self.name = name
        self.description = description
        self.required_tools = required_tools or []
        self.agent_name = agent_name
    
    @abstractmethod
    async def execute(
        self,
        context: SkillContext
    ) -> SkillResult:
        """
        Execute the skill.
        
        This method should:
        1. Use context.execute_tool() or context.get_tool() to call tools
        2. Coordinate multiple tool calls as needed
        3. Evaluate the results
        4. Return a SkillResult with status and output
        
        Args:
            context: Skill execution context
            
        Returns:
            SkillResult with execution status and output
        """
        pass
    
    @abstractmethod
    async def evaluate(
        self,
        result: SkillResult,
        context: SkillContext
    ) -> SkillResult:
        """
        Evaluate the quality of skill execution result.
        
        This method should:
        1. Check if the result meets requirements
        2. Assign a quality score (0.0-1.0)
        3. Determine if help from other agents is needed
        4. Decide if retry is necessary
        
        Args:
            result: Previous execution result
            context: Skill execution context
            
        Returns:
            Updated SkillResult with evaluation
        """
        pass
    
    def get_help_request(self, result: SkillResult) -> Optional[str]:
        """
        Determine which agent could help if result is unsatisfactory.
        
        Args:
            result: Skill execution result
            
        Returns:
            Name of agent that could help, or None
        """
        return result.requires_help
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "required_tools": self.required_tools,
            "agent_name": self.agent_name
        }
