#!/usr/bin/env python3
"""
Simple test to check language detection in CrewService
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n_utils import translation_manager
from pathlib import Path

# Check language detection
print(f"Current language: {translation_manager.get_current_language()}")

# Simulate the logic from CrewService
current_language = translation_manager.get_current_language()
system_base_dir = Path(__file__).parent / "agent" / "crew" / "system"

print(f"System base dir: {system_base_dir}")

# Use language-specific directory if available, otherwise fallback to base directory
if current_language == "zh_CN":
    system_dir = system_base_dir / "zh_CN"
elif current_language == "en_US":
    system_dir = system_base_dir / "en_US"
else:
    # Default to English if language not supported
    system_dir = system_base_dir / "en_US"

# Fallback to base directory if language-specific directory doesn't exist
if not system_dir.exists():
    system_dir = system_base_dir

print(f"Selected system dir for {current_language}: {system_dir}")

# List files in the selected directory
if system_dir.exists():
    print("Files in selected directory:")
    for file in system_dir.glob("*.md"):
        print(f"  {file.name}")
        
        # Read first few lines to check content
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read(200)  # Read first 200 chars
            print(f"    Content preview: {content[:100]}...")
else:
    print("Selected directory does not exist!")

# Now switch to English and repeat
print("\n--- Switching to English ---")
translation_manager.switch_language("en_US")
current_language = translation_manager.get_current_language()
print(f"Current language: {current_language}")

# Use language-specific directory if available, otherwise fallback to base directory
if current_language == "zh_CN":
    system_dir = system_base_dir / "zh_CN"
elif current_language == "en_US":
    system_dir = system_base_dir / "en_US"
else:
    # Default to English if language not supported
    system_dir = system_base_dir / "en_US"

# Fallback to base directory if language-specific directory doesn't exist
if not system_dir.exists():
    system_dir = system_base_dir

print(f"Selected system dir for {current_language}: {system_dir}")

# List files in the selected directory
if system_dir.exists():
    print("Files in selected directory:")
    for file in system_dir.glob("*.md"):
        print(f"  {file.name}")
        
        # Read first few lines to check content
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read(200)  # Read first 200 chars
            print(f"    Content preview: {content[:100]}...")
else:
    print("Selected directory does not exist!")