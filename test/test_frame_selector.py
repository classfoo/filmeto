import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QTimer

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.preview.preview import MediaPreviewWidget, FrameSelectorWidget


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Frame Selector Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Frame selector widget
        self.frame_selector = FrameSelectorWidget()
        layout.addWidget(self.frame_selector)
        
        # Test buttons
        self.btn1 = QPushButton("Load 10 Frames")
        self.btn1.clicked.connect(lambda: self.load_frames(10))
        layout.addWidget(self.btn1)
        
        self.btn2 = QPushButton("Load 5 Frames")
        self.btn2.clicked.connect(lambda: self.load_frames(5))
        layout.addWidget(self.btn2)
        
        self.btn3 = QPushButton("Load 15 Frames")
        self.btn3.clicked.connect(lambda: self.load_frames(15))
        layout.addWidget(self.btn3)
        
    def load_frames(self, count):
        # Test loading different frame counts
        print(f"Loading {count} frames...")
        self.frame_selector.load_frames(count)
        print(f"Frame blocks count: {len(self.frame_selector.frame_blocks)}")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()