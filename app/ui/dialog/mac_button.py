import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                               QVBoxLayout, QLabel, QDialog, QPushButton)
from PySide6.QtCore import Qt, QPoint, QRectF, Signal
from PySide6.QtGui import QPalette, QColor, QPainter, QBrush, QPen, QMouseEvent, QFont, QFontMetrics

class MacButton(QWidget):
    """自定义的 macOS 风格按钮 (红、黄、绿)"""
    # 信号：通知其他按钮有鼠标悬停事件
    hover_changed = Signal(bool)
    
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.hovered = False
        self.show_icon = False  # 控制是否显示图标
        self.setFixedSize(12, 12)  # macOS 按钮标准大小
        self.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停为手型

    def set_show_icon(self, show):
        """设置是否显示图标"""
        if self.show_icon != show:
            self.show_icon = show
            self.update()

    def enterEvent(self, event):
        self.hovered = True
        self.hover_changed.emit(True)  # 通知父组件
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.hover_changed.emit(False)  # 通知父组件
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 根据颜色设置画笔和画刷 - 精确还原 macOS 的颜色
        if self.color == 'red':
            base_color = QColor(255, 95, 86)       # macOS 红色 #FF5F56
        elif self.color == 'yellow':
            base_color = QColor(255, 189, 46)      # macOS 黄色 #FFBD2E
        elif self.color == 'green':
            base_color = QColor(39, 201, 63)       # macOS 绿色 #27C93F
        else:
            base_color = QColor(128, 128, 128)

        # 绘制圆形背景
        painter.setPen(Qt.NoPen)  # 无边框
        painter.setBrush(QBrush(base_color))
        painter.drawEllipse(0, 0, 12, 12)

        # 只在 show_icon 为 True 时绘制图标
        if self.show_icon:
            # 设置图标画笔颜色 - 使用深棕色，更接近真实 macOS
            painter.setPen(QPen(QColor(130, 60, 50), 1.2))
            painter.setRenderHint(QPainter.Antialiasing)

            # 根据颜色绘制对应的图标
            if self.color == 'red':  # 关闭按钮 - X 形状
                # 绘制 X 符号
                painter.drawLine(4, 4, 8, 8)
                painter.drawLine(8, 4, 4, 8)
                
            elif self.color == 'yellow':  # 最小化按钮 - 横线
                # 绘制水平线
                painter.drawLine(3, 6, 9, 6)
                
            elif self.color == 'green':  # 最大化/还原按钮
                # 检查窗口是否最大化
                window = self.window()
                if window and window.isMaximized():
                    # 还原图标 - 两个对角箭头
                    # 左上箭头
                    painter.drawLine(4, 5, 4, 3)
                    painter.drawLine(4, 3, 6, 3)
                    # 右下箭头
                    painter.drawLine(8, 7, 8, 9)
                    painter.drawLine(8, 9, 6, 9)
                else:
                    # 最大化图标 - 两个对角箭头（向外）
                    # 左上箭头
                    painter.drawLine(3, 3, 3, 6)
                    painter.drawLine(3, 3, 6, 3)
                    # 右下箭头  
                    painter.drawLine(9, 9, 9, 6)
                    painter.drawLine(9, 9, 6, 9)


class MacTitleBar(QWidget):
    """macOS 风格的自定义标题栏"""
    # Signals for navigation
    back_clicked = Signal()
    forward_clicked = Signal()
    
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.is_dialog = False  # 标记是否为对话框
        self.layout = QHBoxLayout(self)
        # macOS 标准间距：左边距 8px，上下 6px，按钮间距 8px
        self.layout.setContentsMargins(8, 6, 8, 6)
        self.layout.setSpacing(8)  # 按钮间距 8px

        # 创建三个按钮
        self.close_button = MacButton('red', self)
        self.minimize_button = MacButton('yellow', self)
        self.maximize_button = MacButton('green', self)

        # 将所有按钮放入列表便于管理
        self.buttons = [self.close_button, self.minimize_button, self.maximize_button]

        # 连接悬停信号
        for button in self.buttons:
            button.hover_changed.connect(self._on_button_hover_changed)

        # 添加到布局
        self.layout.addWidget(self.close_button)
        self.layout.addWidget(self.minimize_button)
        self.layout.addWidget(self.maximize_button)

        # 添加一个占位符，将按钮推到左边
        # self.layout.addStretch()

        # 连接按钮点击事件
        self.close_button.mousePressEvent = self.close_window
        self.minimize_button.mousePressEvent = self.minimize_window
        self.maximize_button.mousePressEvent = self.maximize_window
        
        # Navigation buttons container (initially hidden)
        self.nav_container = QWidget(self)
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)
        
        # Back button
        self.back_button = QPushButton("◀", self)
        self.back_button.setFixedSize(24, 24)
        self.back_button.clicked.connect(self.back_clicked.emit)
        self.back_button.setEnabled(False)
        self._style_nav_button(self.back_button)
        nav_layout.addWidget(self.back_button)
        
        # Forward button
        self.forward_button = QPushButton("▶", self)
        self.forward_button.setFixedSize(24, 24)
        self.forward_button.clicked.connect(self.forward_clicked.emit)
        self.forward_button.setEnabled(False)
        self._style_nav_button(self.forward_button)
        nav_layout.addWidget(self.forward_button)
        
        self.nav_container.hide()  # Initially hidden
        self.layout.addWidget(self.nav_container)

    def set_for_dialog(self):
        """设置为对话框模式，此时最大化按钮变为最小化按钮"""
        self.is_dialog = True
    
    def show_navigation_buttons(self, show: bool = True):
        """Show or hide navigation buttons"""
        if show:
            self.nav_container.show()
        else:
            self.nav_container.hide()
    
    def set_navigation_enabled(self, back_enabled: bool, forward_enabled: bool):
        """Enable or disable navigation buttons"""
        self.back_button.setEnabled(back_enabled)
        self.forward_button.setEnabled(forward_enabled)
    
    def _style_nav_button(self, button):
        """Apply styling to navigation buttons"""
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #4c4f52;
                color: #E1E1E1;
            }
            QPushButton:pressed:enabled {
                background-color: #3c3f42;
            }
            QPushButton:disabled {
                color: #444444;
            }
        """)

    def _on_button_hover_changed(self, is_hovering):
        """当任意按钮的悬停状态改变时，更新所有按钮的图标显示"""
        # 检查是否有任何按钮被悬停
        any_hovered = any(button.hovered for button in self.buttons)
        
        # 更新所有按钮的图标显示状态
        for button in self.buttons:
            button.set_show_icon(any_hovered)

    def enterEvent(self, event):
        """鼠标进入标题栏区域，显示所有图标"""
        for button in self.buttons:
            button.set_show_icon(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开标题栏区域，隐藏所有图标"""
        for button in self.buttons:
            button.set_show_icon(False)
        super().leaveEvent(event)

    def close_window(self, event):
        if event.button() == Qt.LeftButton:
            # 如果是对话框类型，使用 reject 方法来正确关闭
            if isinstance(self.window, QDialog):
                self.window.reject()
            else:
                self.window.close()

    def minimize_window(self, event):
        if event.button() == Qt.LeftButton:
            # 对于 QDialog，通常没有最小化按钮，但我们仍然可以实现
            if isinstance(self.window, QDialog):
                self.window.showMinimized()
            else:
                self.window.showMinimized()

    def maximize_window(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_dialog:
                # 对于对话框，最大化按钮也执行最小化操作
                self.window.showMinimized()
            else:
                # 正常窗口模式下，执行最大化/还原操作
                if self.window.isMaximized():
                    self.window.showNormal()
                else:
                    self.window.showMaximized()
