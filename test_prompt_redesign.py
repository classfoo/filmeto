#!/usr/bin/env python3
"""Test script for redesigned PromptInputWidget"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

from app.ui.prompt_input.prompt_input_widget import PromptInputWidget
from app.data.workspace import Workspace

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PromptInputWidget Redesign Test")
        self.setGeometry(100, 100, 800, 200)
        
        # Create workspace
        workspace_path = os.path.join(os.path.dirname(__file__), "test_workspace")
        os.makedirs(workspace_path, exist_ok=True)
        project_name = "test_project"
        project_path = os.path.join(workspace_path, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        self.workspace = Workspace(workspace_path, project_name)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)
        
        # Prompt input widget
        self.prompt_input = PromptInputWidget(self.workspace)
        self.prompt_input.prompt_submitted.connect(self.on_prompt_submitted)
        self.prompt_input.prompt_changed.connect(self.on_prompt_changed)
        layout.addWidget(self.prompt_input)
        
        # Test with a sample config widget
        self.test_config_widget()
        
    def test_config_widget(self):
        """Test setting a config widget"""
        from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QPushButton
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Test Configuration"))
        layout.addWidget(QPushButton("Test Button"))
        
        self.prompt_input.set_config_panel_widget(widget)
        self.status_label.setText("Status: Config widget loaded")
    
    def on_prompt_submitted(self, text):
        self.status_label.setText(f"Submitted: {text[:50]}...")
    
    def on_prompt_changed(self, text):
        token_count = max(1, len(text) // 4) if text else 0
        self.status_label.setText(f"Tokens: {token_count}, Length: {len(text)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("✓ PromptInputWidget redesign test window opened")
    print("✓ Testing horizontal layout with left config panel")
    print("✓ Testing token badge on send button")
    
    sys.exit(app.exec())
