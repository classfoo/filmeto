import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                               QVBoxLayout, QLabel)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPalette, QColor, QPainter, QBrush, QPen, QMouseEvent

class MacButton(QWidget):
    """自定义的 macOS 风格按钮 (红、黄、绿)"""
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.hovered = False
        self.setFixedSize(12, 12)  # macOS 按钮标准大小

    def enterEvent(self, event):
        self.hovered = True
        self.update()  # 触发重绘
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()  # 触发重绘
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 根据颜色设置画笔和画刷
        if self.color == 'red':
            base_color = QColor(255, 85, 85)      # 红色
            hover_color = QColor(255, 120, 120)   # 悬停时更亮
        elif self.color == 'yellow':
            base_color = QColor(255, 186, 0)      # 黄色
            hover_color = QColor(255, 200, 60)    # 悬停时更亮
        elif self.color == 'green':
            base_color = QColor(34, 217, 82)      # 绿色
            hover_color = QColor(80, 230, 120)    # 悬停时更亮
        else:
            base_color = QColor(128, 128, 128)
            hover_color = QColor(160, 160, 160)

        #决定使用哪种颜色
        current_color = hover_color if self.hovered else base_color

        # 绘制圆形背景
        painter.setPen(Qt.NoPen)  # 无边框
        painter.setBrush(QBrush(current_color))
        painter.drawEllipse(0, 0, 12, 12)

        # 根据颜色绘制图标
        painter.setPen(QPen(Qt.white, 1.5))  # 图标颜色为白色
        if self.color == 'red':  # 关闭按钮 - 对角线
            painter.drawLine(3, 3, 9, 9)
            painter.drawLine(3, 9, 9, 3)
        elif self.color == 'yellow':  # 最小化按钮 - 底部横线
            painter.drawLine(3, 7, 9, 7)
        elif self.color == 'green':  # 最大化/还原按钮 - 正方形或两个对角线表示还原
            if not self.parent().isMaximized():  # 如果不是最大化，则绘制正方形
                painter.drawRect(4, 4, 4, 4)
            else:  # 如果是最大化状态，则绘制还原符号
                painter.drawLine(3, 3, 9, 3)
                painter.drawLine(3, 3, 3, 9)
                painter.drawLine(9, 3, 9, 9)
                painter.drawLine(3, 9, 9, 9)


class MacTitleBar(QWidget):
    """macOS 风格的自定义标题栏"""
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 6, 12, 6)  # 与 macOS 间距类似
        self.layout.setSpacing(10)  # 按钮间距

        # 创建三个按钮
        self.close_button = MacButton('red', self)
        self.minimize_button = MacButton('yellow', self)
        self.maximize_button = MacButton('green', self)

        # 添加到布局
        self.layout.addWidget(self.close_button)
        self.layout.addWidget(self.minimize_button)
        self.layout.addWidget(self.maximize_button)

        # 添加一个占位符，将按钮推到左边
        #self.layout.addStretch()

        # 连接按钮点击事件
        self.close_button.mousePressEvent = self.close_window
        self.minimize_button.mousePressEvent = self.minimize_window
        self.maximize_button.mousePressEvent = self.maximize_window

    def close_window(self, event):
        if event.button() == Qt.LeftButton:
            self.window.close()

    def minimize_window(self, event):
        if event.button() == Qt.LeftButton:
            self.window.showMinimized()

    def maximize_window(self, event):
        if event.button() == Qt.LeftButton:
            if self.window.isMaximized():
                self.window.showNormal()
            else:
                self.window.showMaximized()