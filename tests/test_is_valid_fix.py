#!/usr/bin/env python3
"""Quick test for is_valid_title fix"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.crew.crew_title import CrewTitle

# Test the is_valid_title method
is_valid = CrewTitle.is_valid_title('director')
print(f'Is "director" valid? {is_valid}')

is_invalid = CrewTitle.is_valid_title('nonexistent_title')
print(f'Is "nonexistent_title" valid? {is_invalid}')