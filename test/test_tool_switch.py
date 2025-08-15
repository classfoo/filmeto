import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.preview.preview import MediaPreviewWidget


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tool Switch Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Preview widget
        self.preview = MediaPreviewWidget(None)  # Simplified for test
        layout.addWidget(self.preview)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.btn_image = QPushButton("Switch to Image")
        self.btn_image.clicked.connect(self.switch_to_image)
        button_layout.addWidget(self.btn_image)
        
        self.btn_video = QPushButton("Switch to Video")
        self.btn_video.clicked.connect(self.switch_to_video)
        button_layout.addWidget(self.btn_video)
        
        self.btn_gif = QPushButton("Switch to GIF")
        self.btn_gif.clicked.connect(self.switch_to_gif)
        button_layout.addWidget(self.btn_gif)
        
        layout.addLayout(button_layout)
        
        # Sample file paths (you would need to provide actual paths)
        self.sample_image = "/path/to/sample/image.png"
        self.sample_video = "/path/to/sample/video.mp4"
        self.sample_gif = "/path/to/sample/animation.gif"
        
    def switch_to_image(self):
        # Test switching to an image
        print("Switching to image...")
        self.preview.switch_file(self.sample_image)
        
    def switch_to_video(self):
        # Test switching to a video
        print("Switching to video...")
        self.preview.switch_file(self.sample_video)
        
    def switch_to_gif(self):
        # Test switching to a GIF
        print("Switching to GIF...")
        self.preview.switch_file(self.sample_gif)


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()