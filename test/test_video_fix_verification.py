#!/usr/bin/env python3
"""
Test to verify the fixes for MediaPreviewWidget video functionality
"""
import sys
import os
import tempfile
from pathlib import Path

# Add the project root to the path so we can import the modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer
from app.ui.preview.preview import MediaPreviewWidget
from app.data.workspace import Workspace


def create_test_video():
    """Create a test video file using OpenCV or fallback to empty file"""
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, "test_video_simple.mp4")
    
    try:
        import cv2
        import numpy as np
        
        # Create a simple video file for testing
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 10  # Lower fps for faster testing
        frame_size = (160, 120)  # Smaller size for faster testing
        
        out = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
        
        # Create 20 frames (2 seconds at 10fps)
        for i in range(20):
            # Create a frame with changing colors
            frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
            
            # Add a moving rectangle
            rect_x = int((i / 20) * (frame_size[0] - 30))
            frame[30:60, rect_x:rect_x+30] = [i % 255, (i*2) % 255, (i*3) % 255]
            
            out.write(frame)
        
        out.release()
        
        # Check if the file was created successfully
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            print(f"Created simple test video at: {video_path}")
            return video_path
        else:
            print(f"Failed to properly create video file, attempting fallback")
    except ImportError:
        print("OpenCV not available, skipping video creation")
    except Exception as e:
        print(f"Could not create test video with OpenCV: {e}")
    
    # Fallback: create an empty file with .mp4 extension to test loading mechanism
    try:
        with open(video_path, 'w') as f:
            f.write('')  # Create empty file
        print(f"Created empty test video file at: {video_path} (fallback)")
        return video_path
    except Exception as e:
        print(f"Could not create fallback test video: {e}")
        return None


def test_video_functionality_with_qt_loop():
    """Test video functionality within Qt event loop"""
    print("Testing MediaPreviewWidget video functionality with Qt event processing...")
    
    # Create QApplication instance (required for Qt widgets)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    def run_test():
        # Create temporary video file
        test_video_path = create_test_video()
        if not test_video_path:
            print("ERROR: Could not create test video file")
            QTimer.singleShot(100, app.quit)
            return
        
        if not os.path.exists(test_video_path):
            print(f"ERROR: Created test video does not exist at: {test_video_path}")
            QTimer.singleShot(100, app.quit)
            return
        
        # Create workspace
        workspace = Workspace(tempfile.mkdtemp(), "test_video_project")
        
        # Create the preview widget
        preview_widget = MediaPreviewWidget(workspace)
        
        print(f"Loading video: {test_video_path}")
        print(f"File exists: {os.path.exists(test_video_path)}")
        
        # Load the video file
        preview_widget.switch_file(test_video_path)
        
        # Check initial state immediately after loading
        print(f"\\nInitial state after switch_file:")
        print(f"Current file: {preview_widget.current_file}")
        print(f"Video widget visible: {preview_widget.video_widget.isVisible()}")
        print(f"Image label visible: {preview_widget.image_label.isVisible()}")
        print(f"Media player source valid: {not preview_widget.media_player.source().isEmpty()}")
        print(f"Play button enabled: {preview_widget.play_pause_btn.isEnabled()}")
        print(f"Play button text: {preview_widget.play_pause_btn.text()}")
        print(f"Total frames: {preview_widget.total_frames}")
        
        # Wait a bit for Qt events to process and then check again
        def check_after_events():
            print(f"\\nState after Qt event processing:")
            print(f"Video widget visible: {preview_widget.video_widget.isVisible()}")
            print(f"Image label visible: {preview_widget.image_label.isVisible()}")
            print(f"Media player source valid: {not preview_widget.media_player.source().isEmpty()}")
            print(f"Play button enabled: {preview_widget.play_pause_btn.isEnabled()}")
            print(f"Play button text: {preview_widget.play_pause_btn.text()}")
            print(f"Total frames: {preview_widget.total_frames}")
            
            # Test playback functionality
            print(f"\\nTesting playback functionality...")
            print(f"Initial playing state: {preview_widget.is_playing}")
            
            # Try to play the video if possible
            preview_widget.toggle_playback()
            print(f"After toggle (play): playing state = {preview_widget.is_playing}")
            
            # Try to pause
            preview_widget.toggle_playback()
            print(f"After toggle (pause): playing state = {preview_widget.is_playing}")
            
            print(f"\\n✓ Video functionality test completed within Qt event loop")
            
            # Clean up
            preview_widget.deleteLater()
            
            # Exit after the test
            QTimer.singleShot(100, app.quit)
        
        QTimer.singleShot(500, check_after_events)  # Wait 500ms for events to process
    
    # Start the test
    QTimer.singleShot(0, run_test)
    
    print("Starting Qt event loop for testing...")
    return app.exec()


def main():
    print("MediaPreviewWidget Video Test - With Qt Event Loop")
    print("=" * 50)
    
    result = test_video_functionality_with_qt_loop()
    
    print("\\nTest completed with Qt event loop.")
    print("This test properly processes Qt events which is necessary for")
    print("asynchronous video loading to complete.")
    
    return result


if __name__ == "__main__":
    sys.exit(main())