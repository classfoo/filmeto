"""
ReAct (Reasoning and Acting) module for the Filmeto Agent system.

This module provides a generic ReAct processor that can be used across different
agents and scenarios. It handles the ReAct loop (think -> act -> observe -> repeat)
and provides features like streaming events, checkpointing, and resumption.
"""

from .react import React
from .types import ReactEvent, ReactEventType, ReactStatus, CheckpointData

__all__ = [
    'React',
    'ReactEvent',
    'ReactEventType',
    'ReactStatus',
    'CheckpointData'
]