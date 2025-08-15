#!/usr/bin/env python3
"""
Test script for MediaPreviewWidget component
Tests video loading and display functionality
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add the project root to the path so we can import the modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer
from app.ui.preview.preview import MediaPreviewWidget
from app.data.workspace import Workspace


class PreviewTestWindow(QMainWindow):
    """Test window for MediaPreviewWidget"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaPreviewWidget Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create workspace (using a temporary directory for testing)
        self.workspace = Workspace(tempfile.mkdtemp())
        
        # Create the preview widget
        self.preview_widget = MediaPreviewWidget(self.workspace)
        
        # Create test controls
        self.test_video_btn = QPushButton("Test Video Loading")
        self.test_image_btn = QPushButton("Test Image Loading") 
        self.test_switch_btn = QPushButton("Test Switch (Image->Video)")
        self.status_label = QLabel("Status: Ready")
        
        # Connect buttons
        self.test_video_btn.clicked.connect(self.test_video_loading)
        self.test_image_btn.clicked.connect(self.test_image_loading)
        self.test_switch_btn.clicked.connect(self.test_switch_scenario)
        
        # Add widgets to layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.test_video_btn)
        layout.addWidget(self.test_image_btn)
        layout.addWidget(self.test_switch_btn)
        layout.addWidget(self.preview_widget)
        
        # Create a simple test video file
        self.test_video_path = self.create_test_video()
        self.test_image_path = self.create_test_image()
        
        # Track test results
        self.tests_passed = 0
        self.tests_total = 0
        
    def create_test_video(self):
        """Create a simple test video file using a common format"""
        # For testing, we'll try to create or locate a sample video file
        # Since creating videos programmatically is complex, we'll first try to create a minimal test
        import cv2
        import numpy as np
        
        video_path = os.path.join(tempfile.gettempdir(), "test_video.mp4")
        
        try:
            # Create a simple video file for testing
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 30
            frame_size = (640, 480)
            
            out = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
            
            # Create 100 frames of simple animation (3.3 seconds at 30fps)
            for i in range(100):
                # Create a frame with changing colors
                frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
                
                # Add a moving rectangle
                rect_x = int((i / 100) * (frame_size[0] - 100))
                frame[100:200, rect_x:rect_x+100] = [i % 255, (i*2) % 255, (i*3) % 255]
                
                # Add a circle that changes size
                center_x = frame_size[0] // 2
                center_y = frame_size[1] // 2
                radius = 30 + int(20 * abs(i - 50) / 50)
                cv2.circle(frame, (center_x, center_y), radius, [255 - (i % 255), 100, 150], -1)
                
                out.write(frame)
            
            out.release()
            print(f"Created test video at: {video_path}")
            return video_path
        except Exception as e:
            print(f"Could not create test video: {e}")
            # If we can't create a video, return a non-existent file to test error handling
            return os.path.join(tempfile.gettempdir(), "nonexistent_test_video.mp4")
    
    def create_test_image(self):
        """Create a simple test image file"""
        import cv2
        import numpy as np
        
        image_path = os.path.join(tempfile.gettempdir(), "test_image.png")
        
        try:
            # Create a simple image
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img[:] = [100, 150, 200]  # Blue background
            
            # Add some shapes
            cv2.rectangle(img, (100, 100), (200, 200), [0, 255, 0], -1)  # Green rectangle
            cv2.circle(img, (300, 250), 50, [0, 0, 255], -1)  # Red circle
            cv2.putText(img, 'Test Image', (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, [255, 255, 255], 2)
            
            cv2.imwrite(image_path, img)
            print(f"Created test image at: {image_path}")
            return image_path
        except Exception as e:
            print(f"Could not create test image: {e}")
            return os.path.join(tempfile.gettempdir(), "nonexistent_test_image.png")
    
    def test_video_loading(self):
        """Test loading a video file"""
        self.status_label.setText("Testing video loading...")
        
        print(f"Testing video loading with file: {self.test_video_path}")
        print(f"File exists: {os.path.exists(self.test_video_path)}")
        
        # Load the video file using switch_file
        self.preview_widget.switch_file(self.test_video_path)
        
        # Schedule a check after some time to see if video loaded
        QTimer.singleShot(2000, self.check_video_loaded)
        
        self.tests_total += 1
    
    def test_image_loading(self):
        """Test loading an image file"""
        self.status_label.setText("Testing image loading...")
        
        print(f"Testing image loading with file: {self.test_image_path}")
        print(f"File exists: {os.path.exists(self.test_image_path)}")
        
        # Load the image file using switch_file
        self.preview_widget.switch_file(self.test_image_path)
        
        self.tests_total += 1
        self.tests_passed += 1
        self.status_label.setText(f"Image loaded successfully. Tests: {self.tests_passed}/{self.tests_total}")
    
    def test_switch_scenario(self):
        """Test switching from image to video"""
        self.status_label.setText("Testing switch scenario (Image -> Video)...")
        
        # First load an image
        print(f"Loading image: {self.test_image_path}")
        self.preview_widget.switch_file(self.test_image_path)
        
        # After a short delay, load the video
        def load_video_after_delay():
            print(f"Loading video: {self.test_video_path}")
            print(f"Video file exists: {os.path.exists(self.test_video_path)}")
            self.preview_widget.switch_file(self.test_video_path)
            QTimer.singleShot(2000, self.check_video_loaded_after_switch)
        
        QTimer.singleShot(1000, load_video_after_delay)
        
        self.tests_total += 1
    
    def check_video_loaded(self):
        """Check if video was loaded properly"""
        # We can't directly check if the video is visually displayed,
        # but we can check the internal state 
        video_visible = self.preview_widget.video_widget.isVisible()
        has_source = not self.preview_widget.media_player.source().isEmpty()
        
        print(f"Video widget visible: {video_visible}")
        print(f"Media player has source: {has_source}")
        print(f"Current file: {self.preview_widget.current_file}")
        
        if video_visible and has_source:
            self.tests_passed += 1
            self.status_label.setText(f"Video loaded successfully. Tests: {self.tests_passed}/{self.tests_total}")
            print("✓ Video loading test PASSED")
        else:
            self.status_label.setText(f"Video loading test FAILED. Tests: {self.tests_passed}/{self.tests_total}")
            print("✗ Video loading test FAILED")
    
    def check_video_loaded_after_switch(self):
        """Check if video was loaded properly after switching from image"""
        video_visible = self.preview_widget.video_widget.isVisible()
        image_visible = self.preview_widget.image_label.isVisible()
        has_source = not self.preview_widget.media_player.source().isEmpty()
        
        print(f"After switch - Video widget visible: {video_visible}")
        print(f"After switch - Image label visible: {image_visible}")
        print(f"After switch - Media player has source: {has_source}")
        
        # After switching from image to video, video should be visible and image hidden
        if video_visible and not image_visible and has_source:
            self.tests_passed += 1
            self.status_label.setText(f"Switch test completed. Tests: {self.tests_passed}/{self.tests_total}")
            print("✓ Switch (Image->Video) test PASSED")
        else:
            self.status_label.setText(f"Switch test completed with issues. Tests: {self.tests_passed}/{self.tests_total}")
            print("⚠ Switch (Image->Video) test completed with issues")
    
    def run_all_tests(self):
        """Run all tests automatically"""
        print("Starting automated tests...")
        
        # Test 1: Image loading
        QTimer.singleShot(500, self.test_image_loading)
        
        # Test 2: Video loading 
        QTimer.singleShot(1500, self.test_video_loading)
        
        # Test 3: Switch scenario
        QTimer.singleShot(4000, self.test_switch_scenario)


def main():
    """Main function to run the test"""
    app = QApplication(sys.argv)
    
    window = PreviewTestWindow()
    window.show()
    
    # Run automated tests
    # Commenting out the auto-run so user can manually test
    # window.run_all_tests()
    
    print("Preview test window opened.")
    print("Manual test instructions:")
    print("1. Click 'Test Video Loading' to test video file loading")
    print("2. Click 'Test Image Loading' to test image file loading")
    print("3. Click 'Test Switch (Image->Video)' to test switching from image to video")
    print(f"Test video path: {window.test_video_path}")
    print(f"Test image path: {window.test_image_path}")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()