import sys
import cv2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QStyle
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QImage, QPixmap


class FramePrecisePlayer(QMainWindow):
    """
    一个简单的视频播放器，支持精确到帧的播放、暂停和进度条拖动。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("精确到帧的视频播放器")
        self.setGeometry(100, 100, 800, 600)

        # --- 视频相关变量 ---
        self.video_capture = None
        self.total_frames = 0
        self.fps = 0.0
        self.current_frame = 0
        self.is_playing = False

        # --- 定时器 ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.play_next_frame)

        # --- UI 组件 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 视频显示区域
        self.video_label = QLabel("请加载视频文件")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("border: 1px solid gray;")
        main_layout.addWidget(self.video_label)

        # 控制按钮区域
        controls_layout = QHBoxLayout()

        self.open_button = QPushButton("打开视频")
        self.open_button.clicked.connect(self.open_file)
        controls_layout.addWidget(self.open_button)

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setEnabled(False)  # 初始禁用
        controls_layout.addWidget(self.play_button)

        # 进度条
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)  # 初始范围 0-0
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.sliderMoved.connect(self.on_slider_moved)  # 拖动时实时更新
        controls_layout.addWidget(self.slider)

        # 帧数/时间显示
        self.frame_label = QLabel("帧: 0 / 0")
        controls_layout.addWidget(self.frame_label)

        main_layout.addLayout(controls_layout)

    def open_file(self):
        """打开视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path):
        """加载视频文件"""
        # 释放之前的视频
        if self.video_capture:
            self.video_capture.release()

        self.video_capture = cv2.VideoCapture(file_path)

        if not self.video_capture.isOpened():
            self.video_label.setText("错误：无法打开视频文件")
            self.play_button.setEnabled(False)
            return

        # 获取视频信息
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)

        if self.total_frames <= 0 or self.fps <= 0:
            self.video_label.setText("错误：无法获取视频信息")
            self.play_button.setEnabled(False)
            self.video_capture.release()
            self.video_capture = None
            return

        # 设置 UI
        self.slider.setRange(0, self.total_frames - 1)
        self.slider.setValue(0)
        self.current_frame = 0
        self.is_playing = False
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setEnabled(True)
        self.update_frame_label()

        # 显示第一帧
        self.seek_to_frame(0)

    def toggle_playback(self):
        """切换播放/暂停状态"""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        """开始播放"""
        if not self.video_capture or self.total_frames <= 0:
            return
        interval_ms = int(1000 / self.fps) if self.fps > 0 else 40  # 默认 25 FPS
        self.timer.start(interval_ms)
        self.is_playing = True
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def pause(self):
        """暂停播放"""
        self.timer.stop()
        self.is_playing = False
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def play_next_frame(self):
        """定时器超时，播放下一帧"""
        if not self.video_capture:
            return

        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.current_frame = self.total_frames - 1
            self.pause()  # 播放完毕，暂停

        self.seek_to_frame(self.current_frame)

    def seek_to_frame(self, frame_number):
        """跳转到指定帧"""
        if not self.video_capture:
            return
        # 设置视频捕获位置
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        # 读取帧
        ret, frame = self.video_capture.read()
        if ret:
            self.current_frame = frame_number
            self.display_frame(frame)
            # 更新滑块位置（防止滑块移动时触发 seek）
            self.slider.blockSignals(True)
            self.slider.setValue(frame_number)
            self.slider.blockSignals(False)
            self.update_frame_label()
        else:
            return

    # 如果读取失败，可能是到了末尾或视频有问题
    # print(f"警告：无法读取帧 {frame_number}")

    def display_frame(self, frame):
        """在 QLabel 上显示 OpenCV BGR 格式的帧"""
        # 转换颜色空间 BGR -> RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # 使用 QPixmap 显示
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def update_frame_label(self):
        """更新帧数/时间显示"""
        if self.fps > 0:
            current_time = self.current_frame / self.fps
            total_time = self.total_frames / self.fps
            self.frame_label.setText(
                f"帧: {self.current_frame} / {self.total_frames - 1} "
                f"时间: {current_time:.2f}s / {total_time:.2f}s"
            )
        else:
            self.frame_label.setText(f"帧: {self.current_frame} / {self.total_frames - 1}")

    # --- Slider 事件处理 ---
    def on_slider_pressed(self):
        """滑块被按下"""
        if self.is_playing:
            self.pause()

    def on_slider_released(self):
        """滑块被释放"""
        # 可以在这里添加逻辑，例如释放后如果之前是播放状态则继续播放
        # 但通常拖动结束就是暂停状态
        pass

    def on_slider_moved(self, value):
        """滑块被拖动"""
        # 实时更新显示，提供更好的用户体验
        self.seek_to_frame(value)

    def closeEvent(self, event):
        """窗口关闭事件，释放资源"""
        if self.video_capture:
            self.video_capture.release()
        self.timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = FramePrecisePlayer()
    player.show()
    sys.exit(app.exec())




