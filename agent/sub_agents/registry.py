"""Sub-agent registry for managing available sub-agents."""

from typing import Dict, List, Optional, Any
from agent.sub_agents.base import BaseSubAgent
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
        # Import here to avoid circular imports
        from agent.sub_agents.production import ProductionAgent
        from agent.sub_agents.director import DirectorAgent
        from agent.sub_agents.supervisor import SupervisorAgent
        from agent.sub_agents.actor import ActorAgent
        from agent.sub_agents.screenwriter import ScreenwriterAgent
        from agent.sub_agents.sound_mixer import SoundMixerAgent
        from agent.sub_agents.makeup_artist import MakeupArtistAgent
        from agent.sub_agents.editor import EditorAgent
        
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
    
    def unregister_agent(self, agent_name: str) -> bool:
        """Unregister a sub-agent."""
        if agent_name in self._agents:
            agent = self._agents.pop(agent_name)
            for skill in agent.skills.values():
                self.skill_registry.unregister_skill(skill.name, agent_name)
            return True
        return False
    
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
    
    def get_agents_by_specialty(self, specialty: str) -> List[BaseSubAgent]:
        """Get agents with a specific specialty."""
        return [
            agent for agent in self._agents.values()
            if agent.specialty == specialty
        ]
    
    def get_collaborators(self, agent_name: str) -> List[BaseSubAgent]:
        """Get agents that typically collaborate with the specified agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            return []
        
        collaborators = []
        for collab_name in agent.collaborates_with:
            collab = self.get_agent(collab_name)
            if collab:
                collaborators.append(collab)
        return collaborators
    
    def get_workflow_agents(self, phase: str) -> List[BaseSubAgent]:
        """
        Get agents relevant for a specific production phase.
        
        Args:
            phase: Production phase ("pre_production", "production", "post_production")
            
        Returns:
            List of agents for that phase
        """
        phase_mapping = {
            "pre_production": ["Screenwriter", "Director", "MakeupArtist", "Production"],
            "production": ["Director", "Actor", "Supervisor", "MakeupArtist"],
            "post_production": ["Editor", "SoundMixer", "Supervisor"],
            "management": ["Production"]
        }
        
        agent_names = phase_mapping.get(phase, self.list_agent_names())
        return [self.get_agent(name) for name in agent_names if self.get_agent(name)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary."""
        return {
            "agents": {name: agent.to_dict() for name, agent in self._agents.items()},
            "total_agents": len(self._agents),
            "total_skills": len(self.skill_registry.list_all_skills())
        }
