import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QFileDialog, QHBoxLayout, QSlider,
    QComboBox, QGroupBox, QFrame, QDockWidget
)
from PySide6.QtCore import Qt, QUrl, Slot, QTimer, QSize
from PySide6.QtGui import QPixmap, QImageReader, QMovie, QKeyEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class MediaPreviewWidget(QWidget):
    """
    兼顾图片和视频预览的组件，并支持多种屏幕比例
    """
    IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webm')  # 注意：.webm 可能是视频或动画图片
    VIDEO_FORMATS = ('.mp4', '.avi', '.mov', '.wmv', '.mkv', '.webm')

    # 常见屏幕分辨率比例 (宽:高)
    ASPECT_RATIOS = {
        "16:9 (HD/FHD/UHD)": (16, 9),
        "4:3 (传统显示器)": (4, 3),
        "3:2 (DSLR照片)": (3, 2),
        "00000000:00000000 (正方形)": (1, 1),
        "18:9 (全面屏手机)": (18, 9),
        "19.5:9 (现代手机)": (195, 90),  # 用整数避免浮点
        "21:9 (超宽屏)": (21, 9),
        "3:4 (竖屏照片/手机)": (3, 4),
        "9:16 (竖屏视频/手机)": (9, 16),
        "自由比例": None  # 特殊选项，不强制比例
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.is_playing = False
        self.current_aspect_ratio_key = "16:9 (HD/FHD/UHD)"  # 默认比例
        # ------------------- 创建内部控件 -------------------
        # 用于显示图片的 QLabel
        self.image_label = QLabel("暂无预览")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: #2c3e50; color: #95a5a6; border: 2px solid #34495e; }")
        # 移除固定的最小大小，由布局决定
        # self.image_label.setMinimumSize(400, 300)

        # 用于显示视频的 QVideoWidget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("QVideoWidget { background-color: #1e1f22; border: 2px solid #34495e; }")
        self.video_widget.hide()

        # QMediaPlayer 和 QAudioOutput
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)

        # 控制按钮
        self.play_pause_btn = QPushButton("▶ 播放")
        self.play_pause_btn.clicked.connect(self.toggle_playback)
        self.play_pause_btn.setEnabled(False)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self._on_slider_moved)
        self.position_slider.setEnabled(False)

        # 比例选择下拉框
        self.aspect_ratio_combo = QComboBox()
        for key in self.ASPECT_RATIOS.keys():
            self.aspect_ratio_combo.addItem(key)
        # 设置默认选中项
        default_index = list(self.ASPECT_RATIOS.keys()).index(self.current_aspect_ratio_key)
        self.aspect_ratio_combo.setCurrentIndex(default_index)
        self.aspect_ratio_combo.currentTextChanged.connect(self._on_aspect_ratio_changed)

        # 控制布局
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("比例:"))
        control_layout.addWidget(self.aspect_ratio_combo, 1) # combo 占据更多空间
        control_layout.addStretch()
        control_layout.addWidget(self.play_pause_btn)
        control_layout.addWidget(self.position_slider)

        # 主布局：使用一个容器 widget 来包裹显示区域，便于控制比例
        self.display_container = QFrame()
        self.display_container.setStyleSheet("QFrame { background-color: #1e1f22; border-radius: 10px; }")
        container_layout = QVBoxLayout(self.display_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(0)
        container_layout.addWidget(self.image_label, 1, Qt.AlignCenter) # 居中对齐
        container_layout.addWidget(self.video_widget, 1, Qt.AlignCenter)
        container_layout.addStretch()

        # 最终主布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.display_container, 1) # 容器占据主要空间
        main_layout.addLayout(control_layout)

        # GIF 定时器
        self.gif_timer = QTimer(self)
        self.gif_timer.timeout.connect(self._update_gif)

        # 初始应用比例
        self._apply_aspect_ratio()

        self.docker = QDockWidget(self)
        self.docker.setFixedSize(300,600)

    def _on_aspect_ratio_changed(self, text):
        """当下拉框选择改变时"""
        self.current_aspect_ratio_key = text
        self._apply_aspect_ratio()
        # 如果已有文件，重新加载以适应新比例
        if self.current_file:
            self.load_file(self.current_file)

    def _apply_aspect_ratio(self):
        """根据当前选择的比例，调整 display_container 的大小策略"""
        ratio = self.ASPECT_RATIOS[self.current_aspect_ratio_key]
        if ratio is None:
            # 自由比例：让容器尽可能大
            self.display_container.setSizePolicy(Qt.Expanding, Qt.Expanding)
            self.display_container.setMinimumSize(100, 100) # 至少有个最小值
        else:
            width_ratio, height_ratio = ratio
            # 这里我们不直接设置固定大小，而是通过重写 sizeHint 来影响布局
            # 更好的方式是让父布局根据可用空间和比例计算
            # 我们通过设置最小大小和大小策略来引导布局
            # 这是一个简化处理，实际效果依赖于父布局
            pass
        # 强制重新布局，触发 resizeEvent
        self.display_container.updateGeometry()
        # 触发一次 resize 来确保内部控件适应
        self.resizeEvent(None) # 传入 None 表示不是真正的 resize 事件

    def load_file(self, file_path):
        """加载并预览指定的媒体文件"""
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            self._clear_display()
            return

        self.current_file = file_path
        _, ext = os.path.splitext(file_path.lower())

        self._stop_video()
        self.gif_timer.stop()

        if ext in self.IMAGE_FORMATS:
            if ext == '.gif':
                self._load_gif(file_path)
            else:
                self._load_image(file_path)
        elif ext in self.VIDEO_FORMATS:
            self._load_video(file_path)
        else:
            print(f"不支持的文件格式: {ext}")
            self._show_placeholder(f"不支持的格式: {ext}")

    def _load_image(self, image_path):
        """加载静态图片"""
        reader = QImageReader(image_path)
        reader.setAutoTransform(True)
        image = reader.read()

        if image.isNull():
            self._show_placeholder("无法加载图片")
            return

        pixmap = QPixmap.fromImage(image)
        # 在 resizeEvent 中处理缩放
        self.image_label.setPixmap(pixmap)
        self.image_label.show()
        self.video_widget.hide()
        self._update_controls_visibility(False)
        # 触发 resize 来缩放图片
        self.resizeEvent(None)

    def _load_gif(self, gif_path):
        """加载 GIF 动画"""
        movie = QMovie(gif_path)
        if movie.isValid():
            self.image_label.setMovie(movie)
            movie.start()
            self.gif_timer.start(100)
            self.image_label.show()
            self.video_widget.hide()
            self._update_controls_visibility(False)
            self.resizeEvent(None)
        else:
            self._show_placeholder("无法加载 GIF")
            self.gif_timer.stop()

    def _load_video(self, video_path):
        """加载视频"""
        url = QUrl.fromLocalFile(video_path)
        self.media_player.setSource(url)
        self.video_widget.show()
        self.image_label.hide()
        self._update_controls_visibility(True)

    def _on_media_status_changed(self, status):
        """媒体状态变化"""
        if status == QMediaPlayer.EndOfMedia:
            self.is_playing = False
            self.play_pause_btn.setText("▶ 播放")
            self.position_slider.setValue(0)
        elif status == QMediaPlayer.LoadingMedia:
            self._show_placeholder("加载视频中...")
        elif status == QMediaPlayer.LoadedMedia:
            self.play_pause_btn.setEnabled(True)
            self.position_slider.setEnabled(True)
        elif status == QMediaPlayer.StoppedState:
            self.is_playing = False
            self.play_pause_btn.setText("▶ 播放")
        elif status == QMediaPlayer.PlayingState:
            self.is_playing = True
            self.play_pause_btn.setText("⏸ 暂停")
        elif status == QMediaPlayer.PausedState:
            self.is_playing = False
            self.play_pause_btn.setText("▶ 播放")

    def toggle_playback(self):
        """切换播放/暂停"""
        if self.media_player.mediaStatus() in (QMediaPlayer.LoadedMedia, QMediaPlayer.PausedState, QMediaPlayer.EndOfMedia):
            self.media_player.play()
        elif self.media_player.mediaStatus() == QMediaPlayer.PlayingState:
            self.media_player.pause()

    def _on_position_changed(self, position):
        """更新进度条"""
        self.position_slider.setValue(position)

    def _on_duration_changed(self, duration):
        """设置进度条范围"""
        self.position_slider.setRange(0, duration)

    def _on_slider_moved(self, position):
        """拖动进度条"""
        self.media_player.setPosition(position)

    def _stop_video(self):
        """停止视频"""
        if self.media_player.isPlaying():
            self.media_player.stop()
        self.media_player.setSource(QUrl())

    def _update_controls_visibility(self, show):
        """更新控制按钮可见性"""
        self.play_pause_btn.setVisible(show)
        self.position_slider.setVisible(show)

    def _show_placeholder(self, text):
        """显示占位符"""
        self.image_label.setText(text)
        self.image_label.setPixmap(QPixmap())  # ✅ 使用空 QPixmap
        self.image_label.show()
        self.video_widget.hide()
        self._update_controls_visibility(False)

    def _clear_display(self):
        """清除显示"""
        self._stop_video()
        self.gif_timer.stop()
        self.image_label.clear()
        self.image_label.setPixmap(QPixmap())  # ✅ 使用空 QPixmap
        self.image_label.setText("暂无预览")
        self.video_widget.hide()
        self._update_controls_visibility(False)
        self.current_file = None

    def _update_gif(self):
        """GIF 更新 (保险)"""
        pass

    def resizeEvent(self, event):
        """窗口大小改变时，缩放图片以适应当前比例的显示区域"""
        super().resizeEvent(event)
        # 获取 display_container 的可用尺寸
        container_size = self.display_container.size()
        if container_size.isEmpty():
            return

        # 获取当前选择的比例
        ratio = self.ASPECT_RATIOS[self.current_aspect_ratio_key]
        target_size = container_size

        if ratio is not None:
            width_ratio, height_ratio = ratio
            # 计算在 container_size 内，符合宽高比的最大矩形
            container_aspect = container_size.width() / container_size.height()
            target_aspect = width_ratio / height_ratio

            if container_aspect > target_aspect:
                # 容器太宽，按高度计算宽度
                target_width = int(container_size.height() * target_aspect)
                target_height = container_size.height()
            else:
                # 容器太高，按宽度计算高度
                target_width = container_size.width()
                target_height = int(container_size.width() / target_aspect)
            target_size = QSize(target_width, target_height)

        # 缩放图片
        if self.image_label.pixmap() and not self.image_label.movie(): # 静态图片
            original_pixmap = self.image_label.pixmap()
            scaled_pixmap = original_pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            # 重新居中 (QLabel 的 alignment 可能不够)
            # 这里依赖布局的 AlignCenter

        # 视频由 QVideoWidget 自动处理，但我们确保它大小正确
        if self.video_widget.isVisible():
            self.video_widget.setFixedSize(target_size)

    def keyPressEvent(self, event: QKeyEvent):
        """空格键控制播放"""
        if event.key() == Qt.Key_Space and self.media_player.source().isValid():
            self.toggle_playback()
            event.accept()
        else:
            super().keyPressEvent(event)


# ------------------- 使用示例 -------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多媒体预览 - 支持比例切换")
        self.resize(1000, 700)

        # 创建预览组件
        self.preview_widget = MediaPreviewWidget()

        # 创建按钮
        self.load_btn = QPushButton("选择文件")
        self.load_btn.clicked.connect(self._on_load_clicked)

        # 布局
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.preview_widget, 1) # 预览组件占据主要空间
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.load_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def _on_load_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片或视频",
            "",
            "媒体文件 (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.avi *.mov *.wmv *.mkv *.webm);;所有文件 (*)"
        )
        if file_path:
            self.preview_widget.load_file(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())