import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QGraphicsDropShadowEffect, QSizePolicy, QPushButton, QScrollArea, QGridLayout
)
from PySide6.QtGui import QPixmap, QColor, QPalette, QPainter, QFont
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QTimer, Property, QSize


class HoverZoomFrame(QFrame):
    """
    一个自定义 QFrame，通过边框高亮来显示悬停和选中状态。
    """

    def __init__(self, parent, content_text, snapshot:QPixmap,index):
        super().__init__(parent)
        self.parent = parent
        self.index = index
        # --- 基本配置 ---
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        # 设置初始大小
        self.setMinimumSize(90, 160)
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

        # --- 状态 ---
        self._is_hovered = False
        self._is_selected = False
        
        # 更新样式
        self._update_style()

    def is_hovered(self):
        return self._is_hovered

    def set_hovered(self, hovered):
        if self._is_hovered != hovered:
            self._is_hovered = hovered
            self._update_style()
    
    def is_selected(self):
        return self._is_selected
    
    def set_selected(self, selected):
        if self._is_selected != selected:
            self._is_selected = selected
            self._update_style()
    
    def _update_style(self):
        """根据悬停和选中状态更新边框样式"""
        if self._is_selected:
            # 选中状态：蓝色高亮边框
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 3px solid #4080ff;
                    border-radius: 8px;
                }
            """)
        elif self._is_hovered:
            # 悬停状态：浅蓝色边框
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 2px solid #8888ff;
                    border-radius: 8px;
                }
            """)
        else:
            # 默认状态：灰色边框
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                }
            """)

    def enterEvent(self, event):
        """当鼠标进入控件时触发"""
        super().enterEvent(event)
        self.set_hovered(True)

    def leaveEvent(self, event):
        """当鼠标离开控件时触发"""
        super().leaveEvent(event)
        self.set_hovered(False)

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