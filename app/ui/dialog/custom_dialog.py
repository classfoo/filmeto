from PySide6.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QMouseEvent
from .mac_button import MacTitleBar


class CustomTitleBar(QFrame):
    """自定义标题栏，模仿Mac风格"""
    
    # Forward navigation signals from MacTitleBar
    back_clicked = Signal()
    forward_clicked = Signal()

    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.setObjectName("CustomDialogTitleBar")  # Add object name for CSS
        self.setFixedHeight(36)  # 调整高度以适应 MacTitleBar
        self.setStyleSheet("""
            #CustomDialogTitleBar {
                background-color: #3d3f4e;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
            }
        """)

        self.parent_dialog = parent
        self.drag_position = QPoint()

        # 创建标题栏布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)  # 调整边距以适应 MacTitleBar
        layout.setSpacing(0)

        # Mac风格的窗口控制按钮组 (red, yellow, green)
        self.mac_control_buttons = MacTitleBar(self.parent_dialog)
        self.mac_control_buttons.set_for_dialog()
        # Hide navigation controls from MacTitleBar since we're providing our own in CustomTitleBar
        self.mac_control_buttons.show_navigation_buttons(False)  # Ensure MacTitleBar's nav buttons are hidden
        layout.addWidget(self.mac_control_buttons)

        # Add a separator space between the Mac control buttons and the navigation buttons
        separator = QWidget()
        separator.setFixedWidth(8)
        layout.addWidget(separator)

        # Add navigation buttons after the Mac control buttons
        nav_layout = QHBoxLayout()
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

        # Container for navigation buttons
        self.nav_container = QWidget(self)
        self.nav_container.setLayout(nav_layout)
        self.nav_container.hide()  # Initially hidden
        layout.addWidget(self.nav_container)

        # 标题标签
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CustomDialogTitleLabel")  # Add object name for CSS
        self.title_label.setStyleSheet("""
            #CustomDialogTitleLabel {
                color: #E1E1E1;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        # 添加弹性空间
        layout.addWidget(self.title_label)
        layout.addStretch()

        # 右侧工具栏容器（供子类添加按钮）
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setSpacing(8)
        layout.addLayout(self.toolbar_layout)

        # 启用鼠标跟踪
        self.setMouseTracking(True)

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
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent_dialog.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
            self.parent_dialog.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def set_title(self, title):
        """设置标题"""
        self.title_label.setText(title)

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
    


class CustomDialog(QDialog):
    """自定义无边框对话框"""
    
    # Forward navigation signals
    back_clicked = Signal()
    forward_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建自定义标题栏
        self.title_bar = CustomTitleBar(self)
        # Forward navigation signals from title bar
        self.title_bar.back_clicked.connect(self.back_clicked.emit)
        self.title_bar.forward_clicked.connect(self.forward_clicked.emit)
        main_layout.addWidget(self.title_bar)

        # 内容区域容器
        self.content_container = QFrame()
        self.content_container.setObjectName("CustomDialogContentContainer")  # Add object name for CSS
        self.content_container.setStyleSheet("""
            #CustomDialogContentContainer {
                background-color: #2b2d30;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                border: 1px solid #505254;
                border-top: none;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(20, 15, 20, 20)
        self.content_layout.setSpacing(10)

        main_layout.addWidget(self.content_container)

        # 启用鼠标跟踪
        self.setMouseTracking(True)
        self.drag_position = QPoint()
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def set_title(self, title):
        """设置对话框标题"""
        self.title_bar.set_title(title)
    
    def show_navigation_buttons(self, show: bool = True):
        """Show or hide navigation buttons in title bar"""
        self.title_bar.show_navigation_buttons(show)
    
    def set_navigation_enabled(self, back_enabled: bool, forward_enabled: bool):
        """Enable or disable navigation buttons in title bar"""
        self.title_bar.set_navigation_enabled(back_enabled, forward_enabled)
    
    def setContentLayout(self, layout):
        """设置内容布局"""
        # 清除现有的布局项
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加新布局
        self.content_layout.addLayout(layout)
    
    def setContentWidget(self, widget):
        """设置内容控件"""
        # 清除现有的布局项
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加控件
        self.content_layout.addWidget(widget)