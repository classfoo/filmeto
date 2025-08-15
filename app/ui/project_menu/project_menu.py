from PySide6.QtCore import QSize, QRectF
from PySide6.QtGui import QTextFrame, QAction, Qt, QIcon, QPixmap, QPainter, QFont, QColor, QPen
from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLabel, QStyle, QToolButton, QMenu, QMessageBox

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr


class ProjectMenu(BaseWidget):

    def __init__(self,workspace:Workspace):
        super(ProjectMenu,self).__init__(workspace)
        self.setObjectName("project_menu")
        self.workspace = workspace
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.button = QToolButton(self)
        self.button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.layout.addWidget(self.button)
        self.button.setText(workspace.project_name)
        self.button.setFixedSize(120,32)
        self.button.setPopupMode(QToolButton.InstantPopup)
        icon_b = self.create_rounded_letter_icon("B", size=56, bg_color=QColor("purple"), text_color=QColor("white"),
                                            corner_radius_ratio=0.25)
        self.button.setIcon(icon_b)
        self.button.setIconSize(QSize(24,24))
        toolbar_menu = QMenu(self)
        self.button.setMenu(toolbar_menu)
        tb_action1 = QAction(tr("工具栏选项1"), self)
        tb_action2 = QAction(tr("工具栏选项2"), self)
        toolbar_menu.addAction(tb_action1)
        toolbar_menu.addAction(tb_action2)

        tb_action1.triggered.connect(lambda: self.on_menu_action_triggered(tr("工具栏选项1")))
        tb_action2.triggered.connect(lambda: self.on_menu_action_triggered(tr("工具栏选项2")))

    def on_menu_action_triggered(self, action_text):
        """处理菜单项被触发"""
        print(f"菜单项 '{action_text}' 被触发")
        QMessageBox.information(self, tr("菜单项触发"), tr("你点击了: {}").format(action_text))

    def on_menu_button_main_clicked(self):
        """处理 MenuButtonPopup 模式下按钮主要区域的点击"""
        print("MenuButtonPopup 按钮的主要区域被点击")
        QMessageBox.information(self, tr("按钮点击"), tr("你点击了 MenuButton 的主要区域！"))


    def create_rounded_letter_icon(self,letter, size=32, bg_color=QColor("transparent"), text_color=QColor("black"), font_family="Sans-serif", corner_radius_ratio=0.2):
        """
        使用 QPainter 创建一个包含单个字母的 QIcon，并应用圆角效果。

        :param letter: 要绘制的字母 (字符串)
        :param size: 图标大小 (正方形)
        :param bg_color: 背景颜色
        :param text_color: 字母颜色
        :param font_family: 字体族
        :param corner_radius_ratio: 圆角半径与图标大小的比例 (0.0 到 0.5)
        :return: QIcon 对象
        """
        # 创建一个 QPixmap 作为画布
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent) # 初始填充为透明，这对于圆角外围很重要

        # 创建 QPainter 对象
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing) # 启用抗锯齿，对圆角平滑很重要

        # --- 关键步骤：设置圆角剪裁区域 ---
        # 定义圆角矩形区域
        rect = QRectF(0, 0, size, size)
        corner_radius = size * corner_radius_ratio

        # 设置剪裁路径为圆角矩形
        # 注意：Qt 5.12+ 可直接使用 QPainterPath 和 setClipPath
        # 对于更广泛的兼容性，这里使用 setClipRegion 配合绘制路径的方法不太直接
        # 最简单且有效的方法是先绘制圆角矩形路径，然后用它来设置剪裁
        from PySide6.QtGui import QPainterPath # 导入 QPainterPath
        path = QPainterPath()
        path.addRoundedRect(rect, corner_radius, corner_radius)
        painter.setClipPath(path) # 设置剪裁路径

        # --- 在剪裁区域内绘制内容 ---
        # 绘制背景 (如果需要)
        if bg_color != Qt.transparent and bg_color.alpha() > 0:
            painter.fillRect(rect, bg_color)

        # 设置字体
        font = QFont(font_family, size // 1.5, QFont.Bold) # 字体大小约为图标的一半，加粗
        painter.setFont(font)

        # 设置文本颜色
        painter.setPen(QPen(text_color))

        # 绘制文本 (会自动被剪裁区域限制)
        painter.drawText(rect.toRect(), Qt.AlignCenter, letter)

        # 结束绘制
        painter.end()

        # 将 QPixmap 转换为 QIcon 并返回
        return QIcon(pixmap)