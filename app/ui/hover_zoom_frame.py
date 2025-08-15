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

    def __init__(self, content_text, snapshot:QPixmap,parent=None):
        super().__init__(parent)

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QFrame 鼠标悬停高亮放大（修正版）")
        self.setGeometry(200, 200, 900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        scroll_area = QScrollArea(central_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        grid_layout = QGridLayout(content_widget)
        grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        grid_layout.setSpacing(30)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        # 添加多个示例 Frame
        texts = [
            "卡片 A\n内容行 00000000\n内容行 2",
            "卡片 B\n这是 B 的内容\n更多信息",
            "卡片 C\nC 卡片\n描述信息",
            "卡片 D\nD 内容\n最后详情",
            "卡片 E\nE 卡片信息\n额外文本",
            "卡片 F\nF 的描述\n结尾",
        ]
        positions = [(i, j) for i in range(2) for j in range(3)]
        for i, (row, col) in enumerate(positions):
            text = texts[i] if i < len(texts) else f"卡片 {i + 1}\n示例内容"
            frame = HoverZoomFrame(text)
            grid_layout.addWidget(frame, row, col)

        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(scroll_area)

        info_label = QLabel(
            "将鼠标悬停在下方的卡片上查看高亮放大效果。\n"
            "现在可以频繁快速地移入移出，控件会正确地保持在原始位置。"
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: gray; padding: 10px;")
        info_label.setWordWrap(True)
        main_layout.insertWidget(0, info_label)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())