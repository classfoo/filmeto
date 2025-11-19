from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout, QScrollArea


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

