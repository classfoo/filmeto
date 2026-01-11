"""Sub-agents for multi-agent film production system."""

from agent.sub_agents.base import BaseSubAgent, FilmProductionAgent
from agent.sub_agents.production import ProductionAgent
from agent.sub_agents.director import DirectorAgent
from agent.sub_agents.supervisor import SupervisorAgent
from agent.sub_agents.actor import ActorAgent
from agent.sub_agents.screenwriter import ScreenwriterAgent
from agent.sub_agents.sound_mixer import SoundMixerAgent
from agent.sub_agents.makeup_artist import MakeupArtistAgent
from agent.sub_agents.editor import EditorAgent
from agent.sub_agents.registry import SubAgentRegistry

__all__ = [
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
