"""Base skill framework for agent capabilities with script-based execution."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class SkillStatus(str, Enum):
    """Status of skill execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_HELP = "needs_help"
    RETRY = "retry"
    PARTIAL = "partial"  # Partially completed


@dataclass
class SkillResult:
    """Result of skill execution."""
    status: SkillStatus
    output: Any
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_help: Optional[str] = None  # Agent name that could help
    quality_score: Optional[float] = None  # Quality score 0.0-1.0
    artifacts: List[Dict[str, Any]] = field(default_factory=list)  # Generated artifacts
    sub_results: List['SkillResult'] = field(default_factory=list)  # Results from sub-steps
    
    def is_satisfactory(self, threshold: float = 0.7) -> bool:
        """Check if result is satisfactory based on quality score."""
        if self.quality_score is None:
            return self.status == SkillStatus.SUCCESS
        return self.quality_score >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "output": self.output,
            "message": self.message,
            "metadata": self.metadata,
            "requires_help": self.requires_help,
            "quality_score": self.quality_score,
            "artifacts": self.artifacts,
            "sub_results": [r.to_dict() for r in self.sub_results]
        }


@dataclass
class SkillContext:
    """Context for skill execution."""
    workspace: Any
    project: Any
    agent_name: str
    parameters: Dict[str, Any]
    shared_state: Dict[str, Any]  # Shared state between agents
    tool_registry: Any  # Tool registry for tool access
    llm: Any = None  # Optional LLM for intelligent processing
    
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
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Get data from shared state."""
        return self.shared_state.get(key, default)
    
    def set_shared_data(self, key: str, value: Any):
        """Set data in shared state."""
        self.shared_state[key] = value
    
    def get_previous_result(self, agent_name: str, skill_name: str) -> Optional[Any]:
        """Get result from previous agent/skill execution."""
        key = f"{agent_name}_{skill_name}"
        return self.shared_state.get(key)


class SkillStep:
    """
    A single step in a skill script.
    
    Each step represents one operation that can:
    - Execute a tool
    - Call a sub-skill
    - Process data
    - Make decisions
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        action: Callable[[SkillContext, Dict[str, Any]], Any],
        condition: Optional[Callable[[SkillContext, Dict[str, Any]], bool]] = None,
        on_error: Optional[Callable[[Exception, SkillContext], Any]] = None
    ):
        """
        Initialize skill step.
        
        Args:
            name: Step name
            description: Step description
            action: Function to execute for this step
            condition: Optional condition to check before execution
            on_error: Optional error handler
        """
        self.name = name
        self.description = description
        self.action = action
        self.condition = condition
        self.on_error = on_error
    
    async def execute(
        self,
        context: SkillContext,
        step_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute this step.
        
        Args:
            context: Skill execution context
            step_data: Data from previous steps
            
        Returns:
            Updated step data with this step's results
        """
        # Check condition if provided
        if self.condition and not self.condition(context, step_data):
            logger.debug(f"Step '{self.name}' skipped due to condition")
            return step_data
        
        try:
            # Execute action
            if asyncio.iscoroutinefunction(self.action):
                result = await self.action(context, step_data)
            else:
                result = self.action(context, step_data)
            
            step_data[f"{self.name}_result"] = result
            step_data[f"{self.name}_status"] = "success"
            
        except Exception as e:
            logger.error(f"Error in step '{self.name}': {e}")
            step_data[f"{self.name}_error"] = str(e)
            step_data[f"{self.name}_status"] = "failed"
            
            if self.on_error:
                try:
                    error_result = self.on_error(e, context)
                    step_data[f"{self.name}_error_handled"] = error_result
                except Exception as e2:
                    logger.error(f"Error handler failed: {e2}")
        
        return step_data


class BaseSkill(ABC):
    """
    Base class for agent skills.
    
    A skill packages multiple tool calls into a cohesive capability.
    Skills can be executed by agents to perform complex tasks.
    
    Skills support script-based execution through SkillSteps.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        required_tools: Optional[List[str]] = None,
        agent_name: Optional[str] = None,
        category: Optional[str] = None,
        estimated_duration: Optional[float] = None  # In seconds
    ):
        """
        Initialize skill.
        
        Args:
            name: Skill name
            description: Skill description
            required_tools: List of required tool names
            agent_name: Name of agent that owns this skill
            category: Skill category (e.g., "pre_production", "production")
            estimated_duration: Estimated execution duration
        """
        self.name = name
        self.description = description
        self.required_tools = required_tools or []
        self.agent_name = agent_name
        self.category = category
        self.estimated_duration = estimated_duration
        self._steps: List[SkillStep] = []
    
    def add_step(self, step: SkillStep):
        """Add a step to the skill script."""
        self._steps.append(step)
    
    def add_steps(self, steps: List[SkillStep]):
        """Add multiple steps to the skill script."""
        self._steps.extend(steps)
    
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
    
    async def execute_script(self, context: SkillContext) -> SkillResult:
        """
        Execute the skill using defined steps (script-based execution).
        
        This method runs all defined steps in sequence.
        
        Args:
            context: Skill execution context
            
        Returns:
            SkillResult with combined results from all steps
        """
        step_data: Dict[str, Any] = {
            "parameters": context.parameters,
            "agent_name": context.agent_name
        }
        sub_results: List[SkillResult] = []
        
        for step in self._steps:
            try:
                step_data = await step.execute(context, step_data)
                
                # Collect sub-result
                status_key = f"{step.name}_status"
                if step_data.get(status_key) == "success":
                    sub_results.append(SkillResult(
                        status=SkillStatus.SUCCESS,
                        output=step_data.get(f"{step.name}_result"),
                        message=f"Step '{step.name}' completed",
                        metadata={"step": step.name}
                    ))
                elif step_data.get(status_key) == "failed":
                    sub_results.append(SkillResult(
                        status=SkillStatus.FAILED,
                        output=None,
                        message=f"Step '{step.name}' failed: {step_data.get(f'{step.name}_error')}",
                        metadata={"step": step.name}
                    ))
                    
            except Exception as e:
                logger.error(f"Error executing step '{step.name}': {e}")
                sub_results.append(SkillResult(
                    status=SkillStatus.FAILED,
                    output=None,
                    message=f"Step '{step.name}' failed: {str(e)}",
                    metadata={"step": step.name}
                ))
        
        # Determine overall status
        failed_count = sum(1 for r in sub_results if r.status == SkillStatus.FAILED)
        if failed_count == 0:
            overall_status = SkillStatus.SUCCESS
            message = f"Skill '{self.name}' completed successfully with {len(sub_results)} steps"
        elif failed_count < len(sub_results):
            overall_status = SkillStatus.PARTIAL
            message = f"Skill '{self.name}' partially completed ({len(sub_results) - failed_count}/{len(sub_results)} steps)"
        else:
            overall_status = SkillStatus.FAILED
            message = f"Skill '{self.name}' failed (all steps failed)"
        
        return SkillResult(
            status=overall_status,
            output=step_data,
            message=message,
            metadata={"total_steps": len(self._steps), "failed_steps": failed_count},
            sub_results=sub_results
        )
    
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
            "agent_name": self.agent_name,
            "category": self.category,
            "estimated_duration": self.estimated_duration,
            "steps": [{"name": s.name, "description": s.description} for s in self._steps]
        }


class ScriptedSkill(BaseSkill):
    """
    A skill that is entirely defined by a script of steps.
    
    This allows creating skills without subclassing by defining steps.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        steps: List[SkillStep],
        required_tools: Optional[List[str]] = None,
        agent_name: Optional[str] = None,
        category: Optional[str] = None,
        evaluation_func: Optional[Callable[[SkillResult, SkillContext], SkillResult]] = None
    ):
        """
        Initialize scripted skill.
        
        Args:
            name: Skill name
            description: Skill description
            steps: List of skill steps
            required_tools: List of required tool names
            agent_name: Name of agent that owns this skill
            category: Skill category
            evaluation_func: Optional custom evaluation function
        """
        super().__init__(name, description, required_tools, agent_name, category)
        self._steps = steps
        self._evaluation_func = evaluation_func
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the skill using defined steps."""
        return await self.execute_script(context)
    
    async def evaluate(
        self,
        result: SkillResult,
        context: SkillContext
    ) -> SkillResult:
        """Evaluate the skill result."""
        if self._evaluation_func:
            return self._evaluation_func(result, context)
        
        # Default evaluation
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        elif result.status == SkillStatus.PARTIAL:
            result.quality_score = 0.5
        else:
            result.quality_score = 0.0
        
        return result


class SkillBuilder:
    """
    Builder for creating skills with fluent API.
    
    Example:
        skill = (SkillBuilder("my_skill", "My skill description")
            .requires_tools(["tool1", "tool2"])
            .add_step("step1", "First step", lambda ctx, data: do_something())
            .add_step("step2", "Second step", lambda ctx, data: do_more())
            .build())
    """
    
    def __init__(self, name: str, description: str):
        """Initialize builder."""
        self.name = name
        self.description = description
        self.required_tools: List[str] = []
        self.steps: List[SkillStep] = []
        self.category: Optional[str] = None
        self.agent_name: Optional[str] = None
        self.evaluation_func: Optional[Callable] = None
    
    def requires_tools(self, tools: List[str]) -> 'SkillBuilder':
        """Set required tools."""
        self.required_tools = tools
        return self
    
    def in_category(self, category: str) -> 'SkillBuilder':
        """Set skill category."""
        self.category = category
        return self
    
    def for_agent(self, agent_name: str) -> 'SkillBuilder':
        """Set owning agent."""
        self.agent_name = agent_name
        return self
    
    def add_step(
        self,
        name: str,
        description: str,
        action: Callable[[SkillContext, Dict[str, Any]], Any],
        condition: Optional[Callable[[SkillContext, Dict[str, Any]], bool]] = None,
        on_error: Optional[Callable[[Exception, SkillContext], Any]] = None
    ) -> 'SkillBuilder':
        """Add a step."""
        self.steps.append(SkillStep(name, description, action, condition, on_error))
        return self
    
    def with_evaluation(
        self,
        func: Callable[[SkillResult, SkillContext], SkillResult]
    ) -> 'SkillBuilder':
        """Set custom evaluation function."""
        self.evaluation_func = func
        return self
    
    def build(self) -> ScriptedSkill:
        """Build the skill."""
        return ScriptedSkill(
            name=self.name,
            description=self.description,
            steps=self.steps,
            required_tools=self.required_tools,
            agent_name=self.agent_name,
            category=self.category,
            evaluation_func=self.evaluation_func
        )


# ============================================================================
# LLM-Enhanced Skill
# ============================================================================

class LLMEnhancedSkill(BaseSkill):
    """
    A skill that uses LLM for intelligent processing.
    
    This skill type can use LLM to:
    - Generate creative content
    - Make decisions
    - Analyze results
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        required_tools: Optional[List[str]] = None,
        agent_name: Optional[str] = None,
        category: Optional[str] = None,
        output_format: Optional[str] = None  # "json", "text", "structured"
    ):
        """
        Initialize LLM-enhanced skill.
        
        Args:
            name: Skill name
            description: Skill description
            system_prompt: System prompt for LLM
            required_tools: List of required tool names
            agent_name: Name of agent that owns this skill
            category: Skill category
            output_format: Expected output format
        """
        super().__init__(name, description, required_tools, agent_name, category)
        self.system_prompt = system_prompt
        self.output_format = output_format
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute with LLM assistance."""
        if not context.llm:
            return SkillResult(
                status=SkillStatus.FAILED,
                output=None,
                message="LLM not available for LLM-enhanced skill",
                metadata={}
            )
        
        try:
            # Build prompt with context
            prompt = self._build_prompt(context)
            
            # Call LLM
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = context.llm.invoke(messages)
            output = response.content
            
            # Parse output if needed
            if self.output_format == "json":
                import json
                import re
                json_match = re.search(r'\{[\s\S]*\}', output)
                if json_match:
                    output = json.loads(json_match.group())
            
            return SkillResult(
                status=SkillStatus.SUCCESS,
                output=output,
                message=f"LLM-enhanced skill '{self.name}' completed",
                metadata={"output_format": self.output_format}
            )
            
        except Exception as e:
            logger.error(f"Error in LLM-enhanced skill: {e}")
            return SkillResult(
                status=SkillStatus.FAILED,
                output=None,
                message=f"Error: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def _build_prompt(self, context: SkillContext) -> str:
        """Build prompt from context parameters."""
        parts = [f"Task: {self.description}"]
        parts.append(f"\nParameters:")
        for key, value in context.parameters.items():
            parts.append(f"- {key}: {value}")
        return "\n".join(parts)
    
    async def evaluate(
        self,
        result: SkillResult,
        context: SkillContext
    ) -> SkillResult:
        """Evaluate using LLM."""
        if result.status == SkillStatus.SUCCESS:
            result.quality_score = 0.8
        return result
