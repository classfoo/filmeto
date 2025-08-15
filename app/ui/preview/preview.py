import os
import cv2
import asyncio
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QComboBox, QFrame, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QTimer, QSize, Signal
from PySide6.QtGui import QPixmap, QImageReader, QMovie, QKeyEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from app.data.task import TaskResult
from app.data.timeline import TimelineItem
from app.ui.base_widget import BaseTaskWidget
from app.ui.layers.layers_widget import LayersWidget


class FrameBlock(QFrame):
    """单个帧块组件，代表视频中的一帧"""
    clicked = Signal(int)  # 发送帧索引信号
    
    def __init__(self, frame_index, parent=None):
        super().__init__(parent)
        self.frame_index = frame_index
        self._is_selected = False
        
        # 设置固定大小为小方块
        self.setFixedSize(8, 8)
        self._update_style()
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置工具提示显示帧序号
        self.setToolTip(f"{frame_index}")
    
    def set_selected(self, selected):
        """设置选中状态"""
        if self._is_selected != selected:
            self._is_selected = selected
            self._update_style()
    
    def _update_style(self):
        """根据选中状态更新样式"""
        if self._is_selected:
            # 选中状态：蓝色高亮
            self.setStyleSheet("""
                QFrame {
                    background-color: #4080ff;
                    border: 1px solid #2060df;
                    border-radius: 2px;
                }
            """)
        else:
            # 默认状态：灰色
            self.setStyleSheet("""
                QFrame {
                    background-color: #666666;
                    border: 1px solid #555555;
                    border-radius: 2px;
                }
                QFrame:hover {
                    background-color: #888888;
                    border: 1px solid #666666;
                }
            """)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.frame_index)
        super().mousePressEvent(event)


class FrameSelectorWidget(QWidget):
    """视频帧选择器组件，显示所有帧的小方块，支持换行"""
    frame_selected = Signal(int)  # 发送选中的帧索引
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_blocks = []
        self.current_selected_index = -1
        self.total_frames = 0
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 禁用滚动条，自动适应高度
        self.scroll_area.setMinimumHeight(30)  # 最小高度30px
        # 移除最大高度限制，让高度根据内容自动调整
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2c2c2c;
                border: 1px solid #444444;
                border-radius: 4px;
            }
        """)
        
        # 帧块容器 - 使用自定义widget来实现换行布局
        self.frame_container = QWidget()
        self.frame_container.setStyleSheet("background-color: transparent;")
        
        self.scroll_area.setWidget(self.frame_container)
        main_layout.addWidget(self.scroll_area)
        
        # 隐藏组件，直到加载视频
        self.hide()
    
    def load_frames(self, total_frames):
        """根据总帧数创建帧块"""
        self.total_frames = total_frames
        
        # 调整帧块数量以匹配总帧数
        current_frame_count = len(self.frame_blocks)
        
        if current_frame_count < total_frames:
            # 需要添加更多帧块
            for i in range(current_frame_count, total_frames):
                frame_block = FrameBlock(i)
                frame_block.clicked.connect(self._on_frame_clicked)
                self.frame_blocks.append(frame_block)
                frame_block.setParent(self.frame_container)
        elif current_frame_count > total_frames:
            # 需要移除多余的帧块
            for i in range(total_frames, current_frame_count):
                frame_block = self.frame_blocks[i]
                frame_block.setParent(None)
                frame_block.deleteLater()
            self.frame_blocks = self.frame_blocks[:total_frames]
        
        # 更新所有帧块的索引
        for i in range(total_frames):
            self.frame_blocks[i].frame_index = i
            self.frame_blocks[i].setToolTip(f"{i}")
        
        # 显示或隐藏帧块
        for i, frame_block in enumerate(self.frame_blocks):
            frame_block.setVisible(i < total_frames)
        
        # 触发布局更新
        self._layout_frames()
        
        # 重置选中状态
        self.current_selected_index = -1
        # 确保UI状态也被重置，避免第一个帧块保持高亮
        if self.frame_blocks:
            for frame_block in self.frame_blocks:
                frame_block.set_selected(False)
        
        # 显示组件
        self.show()
    
    def _layout_frames(self):
        """重新布局帧块，支持换行"""
        if not self.frame_blocks:
            return
        
        container_width = self.scroll_area.viewport().width()
        if container_width <= 0:
            container_width = 800  # 默认宽度
        
        # 计算每行可以放置多少个帧块
        frame_width = 8  # 帧块宽度
        spacing = 2  # 间距
        margin = 5  # 边距
        
        available_width = container_width - 2 * margin
        frames_per_row = max(1, (available_width + spacing) // (frame_width + spacing))
        
        # 计算需要的行数
        num_rows = (len(self.frame_blocks) + frames_per_row - 1) // frames_per_row
        
        # 设置容器高度
        frame_height = 8
        container_height = num_rows * (frame_height + spacing) + 2 * margin
        self.frame_container.setMinimumHeight(container_height)
        self.frame_container.setMaximumHeight(container_height)  # 固定高度为计算出的高度
        
        # 同时更新 scroll_area 的高度以适应内容
        # 加上边框和内边距
        total_height = container_height + 2  # 2px for border
        self.scroll_area.setFixedHeight(total_height)
        
        # 布局帧块
        x = margin
        y = margin
        for i, frame_block in enumerate(self.frame_blocks):
            if i > 0 and i % frames_per_row == 0:
                # 换行
                x = margin
                y += frame_height + spacing
            
            frame_block.move(x, y)
            x += frame_width + spacing
    
    def resizeEvent(self, event):
        """窗口大小改变时重新布局"""
        super().resizeEvent(event)
        self._layout_frames()
    
    def clear_frames(self):
        """清除所有帧块"""
        for block in self.frame_blocks:
            block.setParent(None)
            block.deleteLater()
        self.frame_blocks.clear()
        self.current_selected_index = -1
        self.total_frames = 0
    
    def _on_frame_clicked(self, frame_index):
        """处理帧块点击事件"""
        # 取消之前的选中状态
        if 0 <= self.current_selected_index < len(self.frame_blocks):
            self.frame_blocks[self.current_selected_index].set_selected(False)
        
        # 设置新的选中状态
        self.current_selected_index = frame_index
        if 0 <= frame_index < len(self.frame_blocks):
            self.frame_blocks[frame_index].set_selected(True)
        
        # 发送信号
        self.frame_selected.emit(frame_index)
    
    def update_current_frame(self, frame_index):
        """更新当前显示的帧（不触发选中事件）"""
        if 0 <= self.current_selected_index < len(self.frame_blocks):
            self.frame_blocks[self.current_selected_index].set_selected(False)
        
        self.current_selected_index = frame_index
        if 0 <= frame_index < len(self.frame_blocks):
            self.frame_blocks[frame_index].set_selected(True)


class MediaPreviewWidget(BaseTaskWidget):
    """
    兼顾图片和视频预览的组件，并支持多种屏幕比例
    """
    # 添加信号用于异步加载完成时更新UI
    load_finished = Signal(str, str)  # file_path, load_type
    
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

    # 默认预览分辨率
    DEFAULT_PREVIEW_SIZE = (800, 450)

    def __init__(self, workspace):
        super().__init__(workspace)
        self.current_file = None
        self.is_playing = False
        self.current_aspect_ratio_key = "16:9 (HD/FHD/UHD)"  # 默认比例
        self.auto_play_on_load = True  # Flag to control auto-play behavior
        self.video_duration = 0  # Store the video duration for seamless looping
        self.timeline_index = None  # Track current timeline index
        self.video_capture = None  # OpenCV video capture for frame extraction
        self.total_frames = 0  # Total number of frames in video
        self.video_fps = 0.0  # Video FPS
        self.preview_size = self.DEFAULT_PREVIEW_SIZE  # 当前预览分辨率
        
        # 异步加载相关变量
        self.load_task = None  # 当前加载任务
        self.load_task_lock = threading.Lock()  # 保护加载任务的锁
        
        # ------------------- 创建内部控件 -------------------
        # 用于显示图片的 QLabel
        self.image_label = QLabel("暂无预览")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        # 控制按钮 - 仅显示图标，不显示文字
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setFixedSize(40, 40)  # 固定大小的图标按钮
        self.play_pause_btn.clicked.connect(self.toggle_playback)
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #2c2c2c;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #1c1c1c;
            }
            QPushButton:disabled {
                color: #666666;
                background-color: #1c1c1c;
            }
        """)
        
        # 帧选择器组件（替代进度条）
        self.frame_selector = FrameSelectorWidget()
        self.frame_selector.frame_selected.connect(self._on_frame_selected)

        # 比例选择下拉框
        self.aspect_ratio_combo = QComboBox()
        for key in self.ASPECT_RATIOS.keys():
            self.aspect_ratio_combo.addItem(key)
        # 设置默认选中项
        default_index = list(self.ASPECT_RATIOS.keys()).index(self.current_aspect_ratio_key)
        self.aspect_ratio_combo.setCurrentIndex(default_index)
        self.aspect_ratio_combo.currentTextChanged.connect(self._on_aspect_ratio_changed)

        # 控制布局 - Play/Pause按钮和帧选择器左右布局
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        control_layout.addWidget(self.play_pause_btn)
        control_layout.addWidget(self.frame_selector, 1)  # 帧选择器占据剩余空间

        # 主布局：使用一个容器 widget 来包裹显示区域，便于控制比例
        self.display_container = QFrame()
        self.display_container.setStyleSheet("QFrame { background-color: #1e1f22; border-radius: 10px; }")
        container_layout = QVBoxLayout(self.display_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(0)
        container_layout.addWidget(self.image_label, 1, Qt.AlignmentFlag.AlignCenter) # 居中对齐
        container_layout.addWidget(self.video_widget, 1, Qt.AlignmentFlag.AlignCenter)
        container_layout.addStretch()
        
        # 创建图层管理组件
        self.layers_widget = LayersWidget(self.workspace)
        # Note: We'll connect to LayerManager in set_timeline_item method
        # self.layers_widget.layer_changed.connect(self._on_layer_changed)
        
        # 创建中央内容布局：图层管理在左侧，预览容器在右侧
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        content_layout.addWidget(self.layers_widget)  # 左侧图层管理（固定宽度200px）
        
        # 创建右侧预览区域的垂直布局
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)
        preview_layout.addWidget(self.display_container, 1)  # 容器占据主要空间
        preview_layout.addLayout(control_layout)  # 控制布局（按钮+帧选择器）
        
        content_layout.addLayout(preview_layout, 1)  # 右侧预览区域占据剩余空间

        # 最终主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(content_layout, 1)

        # GIF 定时器
        self.gif_timer = QTimer(self)
        self.gif_timer.timeout.connect(self._update_gif)
        
        

        # 初始应用比例
        self._apply_aspect_ratio()

        # self.docker = QDockWidget(self)
        # self.docker.setFixedSize(300,600)

        # 连接异步加载完成信号
        self.load_finished.connect(self._on_load_finished)

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
            self.display_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        self.updateGeometry()

    def load_file(self, file_path):
        """异步加载并预览指定的媒体文件"""
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            self._clear_display()
            return

        # 取消之前的加载任务
        with self.load_task_lock:
            if self.load_task and not self.load_task.done():
                self.load_task.cancel()
        
        self.current_file = file_path
        _, ext = os.path.splitext(file_path.lower())

        # Clean up any existing media resources
        self.gif_timer.stop()
        
        # CRITICAL: Always stop video completely when loading any new file
        # This prevents background video loops from interfering
        if ext not in self.VIDEO_FORMATS:
            # If loading a non-video file, completely stop video playback
            self._stop_video()

        # 启动异步加载任务
        self._show_placeholder("加载中...")
        loop = asyncio.get_event_loop()
        self.load_task = loop.create_task(self._async_load_file(file_path))

    async def _async_load_file(self, file_path):
        """异步加载文件"""
        try:
            _, ext = os.path.splitext(file_path.lower())
            
            if ext in self.IMAGE_FORMATS:
                if ext == '.gif':
                    # GIF加载保持同步，因为QMovie需要在主线程中使用
                    self.load_finished.emit(file_path, "gif")
                else:
                    # 对于静态图片，使用异步加载
                    await self._async_load_image(file_path)
            elif ext in self.VIDEO_FORMATS:
                # 视频加载保持同步，因为QMediaPlayer需要在主线程中使用
                self.load_finished.emit(file_path, "video")
            else:
                print(f"不支持的文件格式: {ext}")
                self.load_finished.emit(file_path, "unsupported")
        except Exception as e:
            print(f"加载文件时出错: {e}")
            self.load_finished.emit(file_path, "error")

    async def _async_load_image(self, image_path):
        """异步加载静态图片"""
        # 在线程中执行耗时的图片加载操作
        def load_in_thread():
            reader = QImageReader(image_path)
            reader.setAutoTransform(True)
            image = reader.read()
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                return pixmap
            return None
        
        # 在线程池中执行图片加载
        loop = asyncio.get_event_loop()
        pixmap = await loop.run_in_executor(None, load_in_thread)
        
        # 发送信号到主线程更新UI
        if pixmap:
            self.load_finished.emit(image_path, "image")
        else:
            self.load_finished.emit(image_path, "error")

    def _on_load_finished(self, file_path, load_type):
        """在主线程中处理加载完成的回调"""
        # 检查是否仍在加载同一个文件
        if file_path != self.current_file:
            return  # 已经切换到其他文件，忽略此次加载结果
            
        if load_type == "image":
            self._load_image(file_path)
        elif load_type == "gif":
            self._load_gif(file_path)
        elif load_type == "video":
            self._load_video(file_path)
        elif load_type == "unsupported":
            self._show_placeholder(f"不支持的格式: {os.path.splitext(file_path)[1]}")
        elif load_type == "error":
            self._show_placeholder("无法加载文件")

    def _resize_image_label_with_pixmap(self, pixmap):
        """Resize image_label to match pixmap size while preserving aspect ratio"""
        original_size = pixmap.size()
        
        # Calculate the size that preserves original aspect ratio within container
        container_size = self.display_container.size()
        if not container_size.isEmpty():
            img_aspect = original_size.width() / original_size.height()
            container_aspect = container_size.width() / container_size.height()
            
            # Calculate dimensions with padding
            padding = 20
            available_width = container_size.width() - padding
            available_height = container_size.height() - padding
            
            if img_aspect > container_aspect:
                # Image is wider than container (relative to height)
                final_width = min(available_width, original_size.width())
                final_height = int(final_width / img_aspect)
            else:
                # Image is taller than container (relative to width)
                final_height = min(available_height, original_size.height())
                final_width = int(final_height * img_aspect)
            
            # Ensure we don't scale larger than the original image
            final_width = min(final_width, original_size.width())
            final_height = min(final_height, original_size.height())
            
            final_size = QSize(final_width, final_height)
        else:
            # If no container size available, use original size
            final_size = original_size
        
        # Set the pixmap and size the label to the calculated size
        scaled_pixmap = pixmap.scaled(
            final_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        # Resize the image_label to match the scaled image size
        self.image_label.resize(final_size)
    
    def _resize_image_label_with_movie(self, movie):
        """Resize image_label to match movie size while preserving aspect ratio"""
        frame_size = movie.frameRect().size()
        if frame_size.isEmpty():
            return  # Can't resize if frame size is unknown
            
        # Calculate the size that preserves original aspect ratio within container
        container_size = self.display_container.size()
        if not container_size.isEmpty():
            img_aspect = frame_size.width() / frame_size.height()
            container_aspect = container_size.width() / container_size.height()
            
            # Calculate dimensions with padding
            padding = 20
            available_width = container_size.width() - padding
            available_height = container_size.height() - padding
            
            if img_aspect > container_aspect:
                # Movie is wider than container (relative to height)
                final_width = min(available_width, frame_size.width())
                final_height = int(final_width / img_aspect)
            else:
                # Movie is taller than container (relative to width)
                final_height = min(available_height, frame_size.height())
                final_width = int(final_height * img_aspect)
            
            # Ensure we don't scale larger than the original
            final_width = min(final_width, frame_size.width())
            final_height = min(final_height, frame_size.height())
            
            final_size = QSize(final_width, final_height)
        else:
            # If no container size available, use original frame size
            final_size = QSize(frame_size.width(), frame_size.height())
        
        # Resize the image_label to match the calculated movie size
        self.image_label.resize(final_size)

    def _load_image(self, image_path):
        """加载静态图片"""
        # CRITICAL: Stop video playback completely before loading image
        # Only stop video if we're actually switching from video to image
        if self.video_widget.isVisible():
            self._stop_video_without_clearing_frames()
        
        reader = QImageReader(image_path)
        reader.setAutoTransform(True)
        image = reader.read()

        if image.isNull():
            self._show_placeholder("无法加载图片")
            return

        pixmap = QPixmap.fromImage(image)
        
        # 使用固定尺寸显示图片，避免因不同图片分辨率导致的尺寸变化和抖动
        self._set_preview_widget_size(self.image_label)  # 使用方法设置尺寸
        # 缩放图片以适应固定尺寸
        scaled_pixmap = pixmap.scaled(
            self.preview_size[0], self.preview_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        
        self.image_label.show()
        self.video_widget.hide()
        
        # Show controls for image (similar to video mode)
        self._update_controls_visibility(True)
        
        # Load a single frame for the frame selector (for the image)
        self.total_frames = 1  # Image is treated as a single frame
        self.frame_selector.load_frames(1)  # Load 1 frame
        
        # Reset play state to paused for image
        self.is_playing = False
        self.play_pause_btn.setText("▶")
        self.play_pause_btn.setEnabled(True)
        
        # 触发 resize 来缩放图片 - 使用 QTimer 来确保布局完全更新后再缩放
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.updateGeometry())

    def _load_gif(self, gif_path):
        """加载 GIF 动画"""
        # CRITICAL: Stop video playback completely before loading GIF
        # Only stop video if we're actually switching from video to GIF
        if self.video_widget.isVisible():
            self._stop_video_without_clearing_frames()
        
        movie = QMovie(gif_path)
        if movie.isValid():
            # Set the movie to the label
            self.image_label.setMovie(movie)
            movie.start()
            self.gif_timer.start(100)
            
            # 使用固定尺寸显示GIF，避免因不同GIF分辨率导致的尺寸变化和抖动
            self._set_preview_widget_size(self.image_label)  # 使用方法设置尺寸
            
            self.image_label.show()
            self.video_widget.hide()
            
            # Show controls for GIF (similar to video mode)
            self._update_controls_visibility(True)
            
            # Load a single frame for the frame selector (for the GIF)
            self.total_frames = 1  # GIF is treated as a single frame for the selector
            self.frame_selector.load_frames(1)  # Load 1 frame
            
            # Reset play state to paused for GIF
            self.is_playing = False
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setEnabled(True)
            
            # 触发 resize 来缩放图片 - 使用 QTimer 来确保布局完全更新后再缩放
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.updateGeometry())
        else:
            self._show_placeholder("无法加载 GIF")
            self.gif_timer.stop()

    def _load_video(self, video_path):
        """加载视频"""
        # 首先完全停止当前视频
        self._stop_video()
        
        # 确保视频控件显示，图片控件隐藏
        self.video_widget.show()
        self.image_label.hide()
        # 使用固定尺寸显示视频，避免因不同视频分辨率导致的尺寸变化和抖动
        self._set_preview_widget_size(self.video_widget)  # 使用方法设置尺寸
        self._update_controls_visibility(True)
        
        # 使用OpenCV加载视频以获取帧信息
        self._load_video_frames(video_path)
        
        # 设置新的视频源
        url = QUrl.fromLocalFile(video_path)
        self.media_player.setSource(url)
        
        # 添加错误检查
        if not self.media_player.source().isValid():
            print(f"无法加载视频源: {video_path}")
            self._show_placeholder("无法加载视频")
            return
        
        # Set flag to enable auto-play when media is loaded
        self.auto_play_on_load = True
        
        # 重置 playback button state
        if self.play_pause_btn.text() != "▶":
            self.play_pause_btn.setText("▶")
        # Don't disable the button immediately - wait for media to load
        # Some video files might load immediately, so check the status
        if self.media_player.source().isValid():
            # In some cases, media might be already loaded
            if self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia:
                self.play_pause_btn.setEnabled(True)
                # Auto-play the video when first loaded
                self.media_player.play()
                # Update button text to indicate it's playing
                self.is_playing = True
                self.play_pause_btn.setText("⏸")
            else:
                # Wait for the media status change event to enable the button
                self.play_pause_btn.setEnabled(True)
        else:
            self.play_pause_btn.setEnabled(False)
    
        # 触发 resize 来缩放视频 - 使用 QTimer 来确保布局完全更新后再缩放
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.updateGeometry())
    
    def _load_video_frames(self, video_path):
        """使用OpenCV加载视频帧信息（优化版本以减少闪烁）"""
        # 释放之前的视频捕获
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        # 打开视频文件
        self.video_capture = cv2.VideoCapture(video_path)
        
        if not self.video_capture.isOpened():
            print(f"无法打开视频文件: {video_path}")
            # 不隐藏帧选择器，只是不更新
            return
        
        # 获取视频信息
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        
        if self.total_frames <= 0 or self.video_fps <= 0:
            print(f"无法获取视频帧信息: 总帧数={self.total_frames}, FPS={self.video_fps}")
            # 不隐藏帧选择器，只是不更新
            return
        
        # 更新帧选择器（重用现有的帧块以减少闪烁）
        self.frame_selector.load_frames(self.total_frames)
        self.frame_selector.show()
    
    def _on_frame_selected(self, frame_index):
        """处理帧选择事件"""
        if self.total_frames <= 0:
            return
        
        # For videos, handle frame selection with video capture
        if self.video_capture and self.video_fps > 0 and self.video_widget.isVisible():
            # For videos, calculate time position and set it
            position_ms = int(round((frame_index / self.video_fps) * 1000))
            # 跳转到指定位置 - this ensures more precise timing
            self.media_player.setPosition(position_ms)
        elif self.image_label.isVisible():
            # For images, just ensure the state is paused (no frame jumping needed)
            # The image is always at "frame 0"
            pass
        
        # Use QTimer to ensure precise timing of the pause operation
        # This allows the position to be set before pausing (if applicable)
        QTimer.singleShot(0, lambda: self._ensure_video_stopped())
        
        # Update UI state immediately to reflect intended state
        self.is_playing = False
        self.play_pause_btn.setText("▶")
    
    def _ensure_video_stopped(self):
        """确保视频确实已停止"""
        self.media_player.pause()
        # The is_playing flag is already set to False in _on_frame_selected
        # but we ensure the player is paused in case of any timing issues
        self.is_playing = False

    def _on_slider_pressed(self):
        """帧块被点击时暂停播放（帧选择器触发）"""
        if self.is_playing:
            self.media_player.pause()
            self.is_playing = False
            self.play_pause_btn.setText("▶")

    def _on_media_status_changed(self, status):
        """媒体状态变化（优化版本以减少闪烁）"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Only loop if we're still displaying a video (not switched to image)
            # and if the video is still playing
            if self.video_widget.isVisible() and self.is_playing:
                # For seamless looping, reset position to beginning immediately
                # to avoid the black screen during transition
                self.media_player.setPosition(0)
                # Continue playing to maintain seamless playback
                self.media_player.play()
            else:
                # If video widget is hidden or not playing, stop the loop
                self.is_playing = False
                self.play_pause_btn.setText("▶")
        elif status == QMediaPlayer.MediaStatus.LoadingMedia:
            # 不显示加载占位符，避免闪烁
            pass
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Enable controls only when media is actually loaded
            self.play_pause_btn.setEnabled(True)
            # Ensure the video widget is visible when media is loaded
            if not self.video_widget.isVisible():
                self.video_widget.show()
                self.image_label.hide()
            # Make sure the controls are visible
            self._update_controls_visibility(True)
            # Auto-play the video after it's loaded if the flag is set
            if self.auto_play_on_load:
                # 使用 QTimer.singleShot 确保在 UI 更新后再播放
                QTimer.singleShot(0, lambda: self._play_when_ready())
        elif status == QMediaPlayer.MediaStatus.BufferedMedia:
            # BufferedMedia 也是一个可以播放的状态
            self.play_pause_btn.setEnabled(True)
            if self.auto_play_on_load:
                QTimer.singleShot(0, lambda: self._play_when_ready())
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            # Handle invalid media
            print("无效的媒体文件")
            self._show_placeholder("无效的媒体文件")
            self.play_pause_btn.setEnabled(False)
        elif status == QMediaPlayer.PlaybackState.StoppedState:
            self.is_playing = False
            self.play_pause_btn.setText("▶")
        elif status == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self.play_pause_btn.setText("⏸")
        elif status == QMediaPlayer.PlaybackState.PausedState:
            self.is_playing = False
            self.play_pause_btn.setText("▶")

    def toggle_playback(self):
        """切换播放/暂停"""
        # For videos: toggle actual playback
        if self.video_widget.isVisible() and self.media_player.source().isValid():
            # 使用 is_playing 状态而不是 playbackState，更可靠
            if self.is_playing:
                # Currently playing, so pause it
                self.media_player.pause()
                self.is_playing = False
                self.play_pause_btn.setText("▶")
            else:
                # Currently paused or stopped, so play it
                self.media_player.play()
                self.is_playing = True
                self.play_pause_btn.setText("⏸")
        # For images: toggle the play/pause state visually (since there's no actual playback)
        elif self.image_label.isVisible() or self.total_frames == 1:
            # Toggle the play state for visual consistency
            if self.is_playing:
                # Currently "playing", so pause it
                self.is_playing = False
                self.play_pause_btn.setText("▶")
            else:
                # Currently paused, so play it (though no actual action for image)
                self.is_playing = True
                self.play_pause_btn.setText("⏸")
                # After a short time, automatically return to paused state for images
                if self.image_label.isVisible() or self.total_frames == 1:
                    QTimer.singleShot(500, lambda: self._auto_pause_image())
        else:
            # 如果没有任何有效的媒体源，尝试重新加载
            if self.current_file and os.path.exists(self.current_file):
                _, ext = os.path.splitext(self.current_file.lower())
                if ext in self.VIDEO_FORMATS:
                    self._load_video(self.current_file)

    def _auto_pause_image(self):
        """Automatically pause for images"""
        if (self.image_label.isVisible() or self.total_frames == 1) and self.is_playing:
            self.is_playing = False
            self.play_pause_btn.setText("▶")

    def _on_position_changed(self, position):
        """更新帧选择器（替代进度条）"""
        # 更新帧选择器的当前帧显示
        # For videos: update current frame based on position
        if self.video_fps > 0 and self.total_frames > 0 and self.video_widget.isVisible():
            current_frame = int(round((position / 1000.0) * self.video_fps))
            # 确保帧索引在有效范围内
            current_frame = max(0, min(current_frame, self.total_frames - 1))
            self.frame_selector.update_current_frame(current_frame)
        # For images: if we have only 1 frame, always show it as selected
        elif self.total_frames == 1 and self.image_label.isVisible():
            self.frame_selector.update_current_frame(0)
        
        # Only loop if we're still displaying the video (not switched to image)
        # For seamless looping, check if we're getting close to the end
        # and loop before reaching the actual end to prevent black screen
        if (self.video_widget.isVisible() and
            self.video_duration > 0 and 
            self.is_playing and 
            self.video_duration - position < 200):  # Loop 200ms before end
            # Reset to beginning slightly before video ends
            self.media_player.setPosition(0)

    def _on_duration_changed(self, duration):
        """设置视频时长"""
        self.video_duration = duration

    def _stop_video(self):
        """停止视频并重置播放器状态"""
        # 停止播放
        if self.media_player.isPlaying():
            self.media_player.stop()
        
        # 等待播放状态更新完成 (需要确保播放器完全停止)
        # 重置播放状态 variable
        self.is_playing = False
        
        # Clear the source to ensure clean state for next video
        self.media_player.setSource(QUrl())
        
        # Reset position to 0
        self.media_player.setPosition(0)
        
        # 释放视频捕获资源
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        # 清除帧选择器 (only for videos, not for images which have 1 frame)
        self.frame_selector.clear_frames()
        self.frame_selector.hide()
        
        # Disable controls since there's no active media
        self.play_pause_btn.setEnabled(False)
        if self.play_pause_btn.text() != "▶":
            self.play_pause_btn.setText("▶")
        
        # Reset frame count
        self.total_frames = 0

    def _stop_video_without_clearing_frames(self):
        """停止视频但不清除帧选择器"""
        # 停止播放
        if self.media_player.isPlaying():
            self.media_player.stop()
        
        # 等待播放状态更新完成 (需要确保播放器完全停止)
        # 重置播放状态 variable
        self.is_playing = False
        
        # Clear the source to ensure clean state for next video
        self.media_player.setSource(QUrl())
        
        # Reset position to 0
        self.media_player.setPosition(0)
        
        # 释放视频捕获资源
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        # Disable controls since there's no active media
        self.play_pause_btn.setEnabled(False)
        if self.play_pause_btn.text() != "▶":
            self.play_pause_btn.setText("▶")
        
        # Reset frame count
        self.total_frames = 0

    def _update_controls_visibility(self, show):
        """更新控制按钮可见性"""
        self.play_pause_btn.setVisible(show)
        # Only show frame selector if there are frames loaded (for images/videos)
        if show and self.total_frames > 0:
            self.frame_selector.show()
        else:
            self.frame_selector.hide()

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
        self.frame_selector.hide()
        self.current_file = None
        self.total_frames = 0  # Reset frame count

    def _update_gif(self):
        """GIF 更新 (保险)"""
        pass

    def switch_file(self, file_path):
        """切换文件但不重新构造UI控件（优化版本以防止闪烁）"""
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            self._show_placeholder("文件不存在")
            return

        # # 如果切换到同一个文件，直接返回
        # if self.current_file == file_path:
        #     return

        self.current_file = file_path
        _, ext = os.path.splitext(file_path.lower())

        # 根据文件类型进行相应处理
        if ext in self.IMAGE_FORMATS:
            if ext == '.gif':
                self._switch_to_gif(file_path)
            else:
                self._switch_to_image(file_path)
        elif ext in self.VIDEO_FORMATS:
            self._switch_to_video(file_path)
        else:
            print(f"不支持的文件格式: {ext}")
            self._show_placeholder(f"不支持的格式: {ext}")

    def _switch_to_image(self, image_path):
        """切换到静态图片（优化版本以防止闪烁）"""
        # 先停止视频播放（如果正在播放）
        if self.video_widget.isVisible():
            # 完全停止视频并清理资源
            if self.media_player.isPlaying():
                self.media_player.stop()
            self.media_player.setSource(QUrl())  # 清除视频源
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            self.is_playing = False
            self.play_pause_btn.setText("▶")
        
        # 直接同步加载图片（避免异步导致的延迟和闪烁）
        reader = QImageReader(image_path)
        reader.setAutoTransform(True)
        image = reader.read()
        
        if image.isNull():
            self._show_placeholder("无法加载图片")
            return
        
        pixmap = QPixmap.fromImage(image)
        
        # 更新帧选择器（图片只有1帧）
        self.total_frames = 1
        self.frame_selector.load_frames(1)
        
        # 使用固定尺寸显示图片，避免因不同图片分辨率导致的尺寸变化和抖动
        self._set_preview_widget_size(self.image_label)  # 使用方法设置尺寸
        # 缩放图片以适应固定尺寸
        scaled_pixmap = pixmap.scaled(
            self.preview_size[0], self.preview_size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        
        # 切换控件可见性
        self.video_widget.hide()
        self.image_label.show()
        self._update_controls_visibility(True)
        
        # 重置播放状态
        self.is_playing = False
        self.play_pause_btn.setText("▶")
        self.play_pause_btn.setEnabled(True)

    def _switch_to_gif(self, gif_path):
        """切换到GIF动画（优化版本以防止闪烁）"""
        # 先停止视频播放（如果正在播放）
        if self.video_widget.isVisible():
            # 完全停止视频并清理资源
            if self.media_player.isPlaying():
                self.media_player.stop()
            self.media_player.setSource(QUrl())  # 清除视频源
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            self.is_playing = False
            self.play_pause_btn.setText("▶")
        
        # 加载GIF
        movie = QMovie(gif_path)
        if movie.isValid():
            # 更新帧选择器（GIF作为单帧处理）
            self.total_frames = 1
            self.frame_selector.load_frames(1)
            
            # 先设置movie再切换可见性
            self.image_label.setMovie(movie)
            movie.start()
            self.gif_timer.start(100)
            
            # 使用固定尺寸显示GIF，避免因不同GIF分辨率导致的尺寸变化和抖动
            self._set_preview_widget_size(self.image_label)  # 使用方法设置尺寸
            
            # 切换控件可见性
            self.video_widget.hide()
            self.image_label.show()
            self._update_controls_visibility(True)
            
            # 重置播放状态
            self.is_playing = False
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setEnabled(True)
        else:
            self._show_placeholder("无法加载 GIF")
            self.gif_timer.stop()

    def _switch_to_video(self, video_path):
        """切换到视频（优化版本以防止闪烁）"""
        # 停止GIF播放（如果正在播放）
        self.gif_timer.stop()
        
        # 先完全停止当前视频（如果正在播放）
        if self.media_player.isPlaying():
            self.media_player.stop()
        
        # 清除旧视频源
        self.media_player.setSource(QUrl())
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        # 加载新视频的帧信息
        self._load_video_frames(video_path)
        
        # 设置新的视频源
        url = QUrl.fromLocalFile(video_path)
        self.media_player.setSource(url)
        # 添加错误检查
        if not self.media_player.source().isValid():
            print(f"无法加载视频源: {video_path}")
            self._show_placeholder("无法加载视频")
            return
        
        # 切换控件可见性（先隐藏图片，再显示视频）
        self.image_label.hide()
        self.video_widget.show()
        # 使用固定尺寸显示视频，避免因不同视频分辨率导致的尺寸变化和抖动
        self._set_preview_widget_size(self.video_widget)  # 使用方法设置尺寸

        self._update_controls_visibility(True)
        
        # 设置自动播放标志
        self.auto_play_on_load = True
        
        # 重置播放按钮状态
        self.is_playing = False
        self.play_pause_btn.setText("▶")
        self.play_pause_btn.setEnabled(True)  # 等待媒体加载完成后启用
        
        # 检查是否已经加载完成
        if self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia:
            self.play_pause_btn.setEnabled(True)
            # Auto-play the video when first loaded
            if self.auto_play_on_load:
                self.media_player.play()
                # Update button text to indicate it's playing
                self.is_playing = True
                self.play_pause_btn.setText("⏸")
                # Reset the flag
                self.auto_play_on_load = False

    def _set_preview_widget_size(self, widget):
        """
        设置预览控件的尺寸
        
        Args:
            widget: 需要设置尺寸的控件 (QLabel 或 QVideoWidget)
        """
        widget.setFixedSize(self.preview_size[0], self.preview_size[1])

    def set_preview_size(self, width, height):
        """
        设置预览分辨率
        
        Args:
            width (int): 预览宽度
            height (int): 预览高度
        """
        self.preview_size = (width, height)
        
        # 如果当前有文件正在显示，重新加载以适应新尺寸
        if self.current_file:
            # 只有在存在 load_task_lock 属性时才调用 load_file
            if hasattr(self, 'load_task_lock'):
                self.load_file(self.current_file)
            else:
                # 如果没有 load_task_lock，至少更新当前显示的组件尺寸
                if self.image_label.isVisible():
                    self._set_preview_widget_size(self.image_label)
                elif self.video_widget.isVisible():
                    self._set_preview_widget_size(self.video_widget)
    
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

        # 图片和视频都使用固定尺寸显示，不随窗口大小变化，避免切换过程中的抖动

    def keyPressEvent(self, event: QKeyEvent):
        """空格键控制播放"""
        if event.key() == Qt.Key.Key_Space and self.media_player.source().isValid():
            self.toggle_playback()
            event.accept()
        else:
            super().keyPressEvent(event)

    def on_timeline_switch(self,item:TimelineItem):
        #self.switch_file(item.get_preview_path())
        self.timeline_index = item.get_index()
        # Update layers widget with the new timeline item
        self.layers_widget.set_timeline_item(item)
        return

    def on_task_finished(self,result:TaskResult):
        timeline_index = result.get_timeline_index()
        # Only update if viewing the same timeline item
        if timeline_index == self.timeline_index:
            # Check what type of media was generated
            new_image_path = result.get_image_path()
            new_video_path = result.get_video_path()
            
            # Only update the currently displayed media type to avoid unexpected switches
            # If currently showing video and a new video was generated, update it
            if new_video_path and self.video_widget.isVisible():
                self.load_file(new_video_path)
            # If currently showing image and a new image was generated (and no video is being displayed), update it
            elif new_image_path and self.image_label.isVisible():
                self.load_file(new_image_path)
            # Otherwise, don't automatically switch media types
            # The user can manually switch by clicking the timeline item again
    
    def on_project_switched(self, project_name):
        """处理项目切换"""
        # 清除当前显示
        self._clear_display()
        
        # 重置状态
        self.current_file = None
        self.timeline_index = None
        
        # 重置帧选择器
        self.frame_selector.load_frames(0)
        
        # 停止所有播放
        self._stop_video()
        self.gif_timer.stop()

    def _play_when_ready(self):
        """在媒体准备好时播放"""
        # 检查媒体是否有效且未在播放
        if (self.media_player.source().isValid() and 
            not self.media_player.isPlaying() and 
            self.auto_play_on_load):
            self.media_player.play()
            # Update button text to indicate it's playing
            self.is_playing = True
            self.play_pause_btn.setText("⏸")
            # Reset the flag
            self.auto_play_on_load = False
    
    def set_timeline_item(self, timeline_item: TimelineItem):
        """
        设置当前时间线项，更新图层管理器
        
        Args:
            timeline_item: 时间线项对象
        """
        # Disconnect from previous layer manager if exists
        if hasattr(self, '_layer_manager') and self._layer_manager:
            try:
                self._layer_manager.layer_changed.disconnect(self._on_layer_manager_changed)
            except:
                pass  # Signal was not connected
        
        self.layers_widget.set_timeline_item(timeline_item)
        
        # Connect to the new timeline item's layer manager
        if timeline_item:
            self._layer_manager = timeline_item.get_layer_manager()
            if self._layer_manager:
                self._layer_manager.layer_changed.connect(self._on_layer_manager_changed)
        else:
            self._layer_manager = None
        
        # 加载当前时间线项的预览
        preview_path = timeline_item.get_preview_path()
        if preview_path and os.path.exists(preview_path):
            self.load_file(preview_path)
    
    def _on_layer_manager_changed(self, sender, **kwargs):
        """
        处理来自 LayerManager 的图层变化事件，重新生成预览
        """
        # 调用原有的处理逻辑
        self._on_layer_changed()
    
    def _on_layer_changed(self):
        """
        处理图层变化事件，重新生成预览
        """
        # TODO: 实现图层合成逻辑
        # 当图层发生变化时，需要重新合成所有图层并更新预览
        print("图层已变化，需要重新生成预览")
