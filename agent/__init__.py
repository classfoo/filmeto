"""Filmeto Agent Module - AI Agent with Multi-Agent LangGraph Architecture.

This module provides a multi-agent system for AI-powered film production.

Architecture:
- FilmetoAgent: Main agent class with multi-agent workflow
- Sub-agents: Specialized agents for different film production roles
  - Production (Producer): Project planning and coordination
  - Director: Creative vision and scene direction
  - Screenwriter: Script writing and story development
  - Actor: Character portrayal and performance
  - MakeupArtist: Costume, makeup, and styling
  - Supervisor: Continuity and script supervision
  - SoundMixer: Audio mixing and sound design
  - Editor: Video editing and final assembly
- Skills: Packaged capabilities that coordinate multiple tools
- Tools: Individual operations for project management

Workflow:
1. Question Understanding: Analyze user request
2. Planning: Create execution plan with sub-agent tasks (if complex)
3. Execution: Sub-agents execute tasks with their skills
4. Review: Check results and refine if needed
5. Synthesis: Combine results into coherent response
"""

from agent.filmeto_agent import FilmetoAgent
from agent.tools import ToolRegistry, FilmetoBaseTool
from agent.nodes import (
    AgentState,
    QuestionUnderstandingNode,
    PlannerNode,
    CoordinatorNode,
    ExecutorNode,
    ResponseNode,
    PlanRefinementNode
)
from agent.skills import (
    BaseSkill,
    ScriptedSkill,
    LLMEnhancedSkill,
    SkillResult,
    SkillContext,
    SkillStatus,
    SkillStep,
    SkillBuilder,
    SkillRegistry,
    SkillFactory
)
from agent.sub_agents import (
    BaseSubAgent,
    FilmProductionAgent,
    ProductionAgent,
    DirectorAgent,
    SupervisorAgent,
    ActorAgent,
    ScreenwriterAgent,
    SoundMixerAgent,
    MakeupArtistAgent,
    EditorAgent,
    SubAgentRegistry
)

__all__ = [
    # Main agent
    'FilmetoAgent',
    
    # Tool framework
    'ToolRegistry',
    'FilmetoBaseTool',
    
    # Node classes
    'AgentState',
    'QuestionUnderstandingNode',
    'PlannerNode',
    'CoordinatorNode',
    'ExecutorNode',
    'ResponseNode',
    'PlanRefinementNode',
    
    # Skill framework
    'BaseSkill',
    'ScriptedSkill',
    'LLMEnhancedSkill',
    'SkillResult',
    'SkillContext',
    'SkillStatus',
    'SkillStep',
    'SkillBuilder',
    'SkillRegistry',
    'SkillFactory',
    
    # Sub-agents
    'BaseSubAgent',
    'FilmProductionAgent',
    'ProductionAgent',
    'DirectorAgent',
    'SupervisorAgent',
    'ActorAgent',
    'ScreenwriterAgent',
    'SoundMixerAgent',
    'MakeupArtistAgent',
    'EditorAgent',
    'SubAgentRegistry',
]
