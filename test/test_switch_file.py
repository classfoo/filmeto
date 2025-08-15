import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QTimer

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.preview.preview import MediaPreviewWidget
from app.data.timeline import TimelineItem


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preview Switch Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Preview widget
        self.preview = MediaPreviewWidget(None)  # Simplified for test
        layout.addWidget(self.preview)
        
        # Test buttons
        self.btn1 = QPushButton("Switch to Image")
        self.btn1.clicked.connect(self.switch_to_image)
        layout.addWidget(self.btn1)
        
        self.btn2 = QPushButton("Switch to Video")
        self.btn2.clicked.connect(self.switch_to_video)
        layout.addWidget(self.btn2)
        
        # Sample file paths (you would need to provide actual paths)
        self.sample_image = "/path/to/sample/image.png"
        self.sample_video = "/path/to/sample/video.mp4"
        
    def switch_to_image(self):
        # Test switching to an image without reconstructing UI
        print("Switching to image...")
        self.preview.switch_file(self.sample_image)
        
    def switch_to_video(self):
        # Test switching to a video without reconstructing UI
        print("Switching to video...")
        self.preview.switch_file(self.sample_video)


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()