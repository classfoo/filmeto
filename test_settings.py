"""
Test script for Settings Management System

Tests the Settings data layer and SettingsWidget UI.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from app.data.workspace import Workspace
from app.ui.settings import SettingsWidget


class TestWindow(QWidget):
    """Test window to launch settings"""
    
    def __init__(self, workspace: Workspace):
        super().__init__()
        self.workspace = workspace
        self.settings_widget = None
        
        self.setWindowTitle("Settings Test")
        self.setGeometry(100, 100, 400, 200)
        
        layout = QVBoxLayout(self)
        
        # Test settings data layer
        self._test_settings_class()
        
        # Button to open settings
        open_btn = QPushButton("Open Settings")
        open_btn.clicked.connect(self.open_settings)
        layout.addWidget(open_btn)
        
        # Button to test get/set
        test_btn = QPushButton("Test Get/Set")
        test_btn.clicked.connect(self.test_get_set)
        layout.addWidget(test_btn)
        
        # Button to print current settings
        print_btn = QPushButton("Print Settings")
        print_btn.clicked.connect(self.print_settings)
        layout.addWidget(print_btn)
    
    def _test_settings_class(self):
        """Test Settings class functionality"""
        print("\n" + "="*50)
        print("Testing Settings Class")
        print("="*50)
        
        settings = self.workspace.get_settings()
        
        # Test get
        language = settings.get("general.language")
        print(f"✓ Get language: {language}")
        
        quality = settings.get("rendering.quality")
        print(f"✓ Get quality: {quality}")
        
        # Test get with default
        unknown = settings.get("unknown.field", "default_value")
        print(f"✓ Get unknown field: {unknown}")
        
        # Test get_groups
        groups = settings.get_groups()
        print(f"✓ Found {len(groups)} groups:")
        for group in groups:
            print(f"  - {group.label} ({len(group.fields)} fields)")
        
        # Test validation
        valid = settings.validate("general.language", "en")
        print(f"✓ Validate valid value: {valid}")
        
        invalid = settings.validate("general.language", "invalid_lang")
        print(f"✓ Validate invalid value: {invalid}")
        
        print("="*50 + "\n")
    
    def open_settings(self):
        """Open settings widget"""
        if self.settings_widget is None:
            self.settings_widget = SettingsWidget(self.workspace)
            self.settings_widget.settings_changed.connect(self.on_settings_changed)
        
        self.settings_widget.show()
        self.settings_widget.raise_()
        self.settings_widget.activateWindow()
    
    def test_get_set(self):
        """Test get and set operations"""
        settings = self.workspace.get_settings()
        
        print("\n" + "="*50)
        print("Testing Get/Set Operations")
        print("="*50)
        
        # Get current value
        current = settings.get("general.auto_save_interval")
        print(f"Current auto_save_interval: {current}")
        
        # Set new value
        new_value = 30
        success = settings.set("general.auto_save_interval", new_value)
        print(f"Set to {new_value}: {success}")
        
        # Verify
        updated = settings.get("general.auto_save_interval")
        print(f"Updated value: {updated}")
        
        # Test invalid value
        invalid_success = settings.set("general.auto_save_interval", 999)  # Max is 60
        print(f"Set invalid value (999): {invalid_success}")
        
        print("="*50 + "\n")
    
    def print_settings(self):
        """Print all current settings"""
        settings = self.workspace.get_settings()
        
        print("\n" + "="*50)
        print("Current Settings")
        print("="*50)
        
        groups = settings.get_groups()
        for group in groups:
            print(f"\n[{group.label}]")
            for field in group.fields:
                key = f"{group.name}.{field.name}"
                value = settings.get(key)
                print(f"  {field.label}: {value}")
        
        print("="*50 + "\n")
    
    def on_settings_changed(self):
        """Handle settings changed signal"""
        print("✓ Settings have been changed and saved!")


def main():
    """Main test function"""
    app = QApplication(sys.argv)
    
    # Create test workspace directory
    test_workspace = os.path.join(os.path.dirname(__file__), "test_workspace")
    os.makedirs(test_workspace, exist_ok=True)
    
    # Create test project directory
    test_project = os.path.join(test_workspace, "test_project")
    os.makedirs(test_project, exist_ok=True)
    
    # Create minimal project.yaml
    project_yaml = os.path.join(test_project, "project.yaml")
    if not os.path.exists(project_yaml):
        with open(project_yaml, 'w') as f:
            f.write("name: test_project\n")
    
    print(f"Test workspace: {test_workspace}")
    print(f"Test project: {test_project}")
    
    # Create workspace
    workspace = Workspace(test_workspace, "test_project")
    
    # Create and show test window
    window = TestWindow(workspace)
    window.show()
    
    print("\n" + "="*50)
    print("Settings Management System Test")
    print("="*50)
    print("1. Click 'Open Settings' to test the UI")
    print("2. Click 'Test Get/Set' to test data operations")
    print("3. Click 'Print Settings' to see current values")
    print("="*50 + "\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
