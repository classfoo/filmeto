"""Sub-agent registry for managing available sub-agents."""

from typing import Dict, List, Optional, Any
from agent.sub_agents.base import BaseSubAgent
from agent.sub_agents.production import ProductionAgent
from agent.sub_agents.director import DirectorAgent
from agent.sub_agents.supervisor import SupervisorAgent
from agent.sub_agents.actor import ActorAgent
from agent.sub_agents.screenwriter import ScreenwriterAgent
from agent.sub_agents.sound_mixer import SoundMixerAgent
from agent.sub_agents.makeup_artist import MakeupArtistAgent
from agent.sub_agents.editor import EditorAgent
from agent.skills.registry import SkillRegistry


class SubAgentRegistry:
    """Registry for managing available sub-agents."""
    
    def __init__(self, llm: Any = None):
        """
        Initialize sub-agent registry.
        
        Args:
            llm: Optional LLM for agent reasoning
        """
        self.llm = llm
        self._agents: Dict[str, BaseSubAgent] = {}
        self.skill_registry = SkillRegistry()
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register default sub-agents."""
        agents = [
            ProductionAgent(llm=self.llm),
            DirectorAgent(llm=self.llm),
            SupervisorAgent(llm=self.llm),
            ActorAgent(llm=self.llm),
            ScreenwriterAgent(llm=self.llm),
            SoundMixerAgent(llm=self.llm),
            MakeupArtistAgent(llm=self.llm),
            EditorAgent(llm=self.llm),
        ]
        
        for agent in agents:
            self.register_agent(agent)
    
    def register_agent(self, agent: BaseSubAgent):
        """Register a sub-agent."""
        self._agents[agent.name] = agent
        
        # Register all agent skills in skill registry
        for skill in agent.skills.values():
            self.skill_registry.register_skill(skill, agent.name)
    
    def get_agent(self, agent_name: str) -> Optional[BaseSubAgent]:
        """Get an agent by name."""
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[BaseSubAgent]:
        """List all registered agents."""
        return list(self._agents.values())
    
    def list_agent_names(self) -> List[str]:
        """List all agent names."""
        return list(self._agents.keys())
    
    def get_agent_capabilities(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get capabilities of all agents.
        
        Returns:
            Dictionary mapping agent names to their skill descriptions
        """
        capabilities = {}
        for agent_name, agent in self._agents.items():
            capabilities[agent_name] = agent.get_skill_descriptions()
        return capabilities
    
    def find_agents_for_skill(self, skill_name: str) -> List[str]:
        """Find agents that can perform a specific skill."""
        matching_agents = []
        for agent_name, agent in self._agents.items():
            if agent.can_help_with(skill_name):
                matching_agents.append(agent_name)
        return matching_agents
