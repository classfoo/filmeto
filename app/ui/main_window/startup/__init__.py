# -*- coding: utf-8 -*-
"""
Startup Mode Package

This package contains components for the application's startup/home mode,
which is displayed when the application opens and allows users to browse
and manage projects.
"""

from .startup_widget import StartupWidget
from .project_list_widget import ProjectListWidget
from .project_info_widget import ProjectInfoWidget
from .startup_prompt_widget import StartupPromptWidget

__all__ = [
    'StartupWidget',
    'ProjectListWidget',
    'ProjectInfoWidget',
    'StartupPromptWidget',
]
