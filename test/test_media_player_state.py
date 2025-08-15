import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a minimal mock workspace for testing
class MockWorkspace:
    def connect_task_create(self, func):
        pass
    
    def connect_task_finished(self, func):
        pass
    
    def connect_timeline_switch(self, func):
        pass

from app.ui.preview.preview import MediaPreviewWidget


def test_media_player_state():
    """Test the media player state handling"""
    app = QApplication(sys.argv)
    
    # Create a mock workspace
    mock_workspace = MockWorkspace()
    
    # Create a preview widget
    preview_widget = MediaPreviewWidget(mock_workspace)
    
    # Test media player state handling
    print("Testing media player state management...")
    
    # Check initial state
    print(f"Initial source valid: {preview_widget.media_player.source().isValid()}")
    
    # Set a source
    url = QUrl.fromLocalFile("/path/to/test/video.mp4")
    preview_widget.media_player.setSource(url)
    print(f"After setting source: {preview_widget.media_player.source().isValid()}")
    
    # Clear the source
    preview_widget.media_player.setSource(QUrl())
    print(f"After clearing source: {preview_widget.media_player.source().isValid()}")
    
    print("Media player state test completed successfully")


if __name__ == "__main__":
    test_media_player_state()