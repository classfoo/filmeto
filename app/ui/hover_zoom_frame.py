import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QGraphicsDropShadowEffect, QSizePolicy, QPushButton, QScrollArea, QGridLayout
)
from PySide6.QtGui import QPixmap, QColor, QPalette, QPainter, QFont
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QTimer, Property, QSize


class HoverZoomFrame(QFrame):
    """
    一个自定义 QFrame，鼠标悬停时会平滑地放大并添加阴影高亮，
    鼠标移出时可靠地恢复到原始状态，解决了频繁进出导致的移位问题。
    """

    def __init__(self, parent, content_text, snapshot:QPixmap,index):
        super().__init__(parent)
        self.parent = parent
        self.index = index
        # --- 基本配置 ---
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: white; border-radius: 8px;")
        # 设置初始大小
        #self.setFixedSize(90,160)
        self.setMinimumSize(90, 160)
        #self.setMaximumSize(180,360)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # 启用鼠标跟踪
        self.setMouseTracking(True)

        # --- 内容 ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.content_label = QLabel(content_text)
        scaled_image = snapshot.scaled(QSize(80,150),Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)
        self.content_label.setPixmap(scaled_image)
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setWordWrap(True)
        font = self.content_label.font()
        font.setPointSize(10)
        self.content_label.setFont(font)
        layout.addWidget(self.content_label)

        # --- 动画和效果 ---
        # 放大动画 (修改大小和位置)
        self.zoom_in_anim = QPropertyAnimation(self, b"geometry")
        self.zoom_in_anim.setDuration(300)
        self.zoom_in_anim.setEasingCurve(QEasingCurve.OutBack)

        # 恢复动画 (修改大小和位置)
        self.zoom_out_anim = QPropertyAnimation(self, b"geometry")
        self.zoom_out_anim.setDuration(300)
        self.zoom_out_anim.setEasingCurve(QEasingCurve.InBack)

        # 阴影效果 (用于高亮)
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(15)
        self.shadow_effect.setXOffset(0)
        self.shadow_effect.setYOffset(0)
        self.shadow_effect.setColor(QColor(64, 128, 255, 180))
        self.shadow_effect.setEnabled(False)
        self.setGraphicsEffect(self.shadow_effect)

        # --- 状态 ---
        self._is_hovered = False
        self._is_animating_in = False
        self._is_animating_out = False
        # 关键修改：存储原始几何状态，只在第一次进入时设置
        self.original_geometry = QRect()
        self._original_geometry_set = False

        # --- 连接动画信号 ---
        self.zoom_in_anim.finished.connect(self._on_zoom_in_finished)
        self.zoom_out_anim.finished.connect(self._on_zoom_out_finished)

    def is_hovered(self):
        return self._is_hovered

    def set_hovered(self, hovered):
        if self._is_hovered != hovered:
            self._is_hovered = hovered
            self._update_animation_state()

    def _update_animation_state(self):
        """根据 is_hovered 状态和当前动画状态决定下一步操作"""
        if self._is_hovered:
            # 鼠标进入
            if not self._original_geometry_set:
                # 第一次进入时记录原始位置和大小
                self.original_geometry = self.geometry()
                self._original_geometry_set = True

            if self._is_animating_out:
                self.zoom_out_anim.stop()
                self._is_animating_out = False
            if not self._is_animating_in:
                self._start_zoom_in_animation()
        else:
            # 鼠标离开
            if self._is_animating_in:
                self.zoom_in_anim.stop()
                self._is_animating_in = False
            # 只有在原始几何信息已设置且未在缩小动画中时才开始缩小
            if self._original_geometry_set and not self._is_animating_out:
                self._start_zoom_out_animation()

    def enterEvent(self, event):
        """当鼠标进入控件时触发"""
        super().enterEvent(event)
        self.set_hovered(True)

    def leaveEvent(self, event):
        """当鼠标离开控件时触发"""
        super().leaveEvent(event)
        self.set_hovered(False)

    def _start_zoom_in_animation(self):
        """开始鼠标悬停时的放大动画（放大+高亮）"""
        self._is_animating_in = True

        # 始终基于记录的原始几何状态计算
        current_rect = self.original_geometry
        if current_rect.isEmpty():
            self._is_animating_in = False
            return

        scale_factor = 1.05
        new_width = int(current_rect.width() * scale_factor)
        new_height = int(current_rect.height() * scale_factor)

        # 计算新的位置，使放大后中心不变，基于原始位置
        delta_x = (new_width - current_rect.width()) // 2
        delta_y = (new_height - current_rect.height()) // 2
        new_x = current_rect.x() - delta_x
        new_y = current_rect.y() - delta_y

        new_rect = QRect(new_x, new_y, new_width, new_height)

        self.zoom_in_anim.setStartValue(self.geometry())  # 从当前（可能是原始或动画中）位置开始
        self.zoom_in_anim.setEndValue(new_rect)

        self.shadow_effect.setEnabled(True)
        self.zoom_in_anim.start()

    def _start_zoom_out_animation(self):
        """开始鼠标离开时的恢复动画（恢复原始大小+取消高亮）"""
        self._is_animating_out = True

        # 始终恢复到记录的原始几何状态
        self.zoom_out_anim.setStartValue(self.geometry())
        self.zoom_out_anim.setEndValue(self.original_geometry)

        self.zoom_out_anim.start()

    def _on_zoom_in_finished(self):
        """放大动画结束后的回调"""
        self._is_animating_in = False
        if not self._is_hovered:
            self._update_animation_state()

    def _on_zoom_out_finished(self):
        """恢复动画结束后的回调"""
        self._is_animating_out = False
        self.shadow_effect.setEnabled(False)
        # 动画完全结束后，可以认为回到了静止的原始状态
        # 但如果鼠标又进来了，_original_geometry_set 仍然是 True，这是正确的

    def setContent(self, text):
        """设置显示的文本内容"""
        self.content_label.setText(text)

    def setImage(self,snapshot:QPixmap):
        scaled_image = snapshot.scaled(QSize(80,150),Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)
        self.content_label.setPixmap(scaled_image)

    def mousePressEvent(self, event):
        """Handle mouse click event to add a new card"""
        if event.button() == Qt.LeftButton:
            if hasattr(self.parent, 'on_mouse_press_card'):
                self.parent.on_mouse_press_card(self.index)