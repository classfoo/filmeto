import logging
from PySide6.QtCore import QSize, QRectF, Signal
from PySide6.QtGui import QTextFrame, QAction, Qt, QIcon, QPixmap, QPainter, QFont, QColor, QPen
from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLabel, QStyle, QToolButton, QMenu, QMessageBox, QInputDialog, QDialog, QLineEdit, QHBoxLayout, QDialogButtonBox

from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget
from utils.i18n_utils import tr

logger = logging.getLogger(__name__)


class ProjectMenu(BaseWidget):
    # 定义项目切换信号
    project_switched = Signal(str)

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
        self.toolbar_menu = QMenu(self)
        self.toolbar_menu.setStyleSheet("""
            QMenu {
                background-color: #2b2d30;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 5px 0px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
                font-size: 14px;
                color: #E1E1E1;
            }
            QMenu::item:selected {
                background-color: #3d3f4e;
            }
            QMenu::separator {
                height: 1px;
                background-color: #505254;
                margin: 5px 0px;
            }
        """)
        self.button.setMenu(self.toolbar_menu)
        
        # 添加新建项目菜单项
        self.new_project_action = QAction(tr("新建项目"), self)
        self.toolbar_menu.addAction(self.new_project_action)
        
        # 添加分隔线
        self.toolbar_menu.addSeparator()
        
        # 加载已有项目
        self.load_existing_projects()
        
        # 连接信号
        self.new_project_action.triggered.connect(self.on_new_project_triggered)

    def load_existing_projects(self):
        """加载已有的项目清单"""
        # 清除之前的项目菜单项（除了新建项目和分隔线）
        actions = self.toolbar_menu.actions()
        for action in actions[2:]:  # 保留前两个（新建项目和分隔线）
            self.toolbar_menu.removeAction(action)
        
        # 使用Workspace中的ProjectManager加载项目
        project_names = self.workspace.project_manager.list_projects()
        
        # 为每个项目创建菜单项
        for project_name in project_names:
            if project_name != self.workspace.project_name:  # 不显示当前项目
                # 获取项目完整路径通过ProjectManager
                project_instance = self.workspace.project_manager.get_project(project_name)
                if not project_instance:
                    # 如果项目实例不存在，则跳过该项目
                    continue

                project_path = project_instance.project_path

                # 创建动作
                action = QAction(project_name, self)

                # 为项目菜单项添加图标
                project_icon = self.create_rounded_letter_icon(
                    project_name[0].upper(),
                    size=56,
                    bg_color=QColor("blue"),
                    text_color=QColor("white"),
                    corner_radius_ratio=0.25
                )
                action.setIcon(project_icon)
                action.triggered.connect(lambda checked=False, name=project_name: self.on_project_selected(name))
                self.toolbar_menu.addAction(action)

                # 添加项目路径作为工具提示
                action.setToolTip(project_path)

    def on_project_selected(self, project_name):
        """处理项目选择"""
        logger.info(f"选择了项目: {project_name}")
        
        # 使用Workspace切换项目，确保workspace中的当前项目信息都被更新
        switched_project = self.workspace.switch_project(project_name)
        
        # 更新按钮显示的项目名称
        self.button.setText(project_name)
        
        # 重新加载项目列表以更新菜单
        self.load_existing_projects()
        
        # 发出项目切换信号
        self.project_switched.emit(project_name)

    def on_new_project_triggered(self):
        """处理新建项目菜单项被触发"""
        # 使用自定义对话框获取项目名称
        from app.ui.dialog.custom_dialog import CustomDialog
        dialog = CustomDialog(self)
        dialog.set_title(tr("新建项目"))
        
        # 创建内容布局
        content_layout = QVBoxLayout()
        
        # 标签
        label = QLabel(tr("请输入项目名称:"))
        label.setStyleSheet("color: #E1E1E1; font-size: 14px;")
        content_layout.addWidget(label)
        
        # 输入框
        line_edit = QLineEdit()
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1e1f22;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 8px;
                color: #E1E1E1;
                selection-background-color: #4080ff;
                font-size: 14px;
            }
        """)
        content_layout.addWidget(line_edit)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            dialog
        )
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #3d3f4e;
                color: #E1E1E1;
                border: 1px solid #505254;
                border-radius: 5px;
                padding: 6px 15px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #444654;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        content_layout.addWidget(button_box)
        
        dialog.setContentLayout(content_layout)
        
        # 设置焦点到输入框
        line_edit.setFocus()
        
        ok = dialog.exec() == QDialog.Accepted
        project_name = line_edit.text() if ok else ""
        
        if ok and project_name:
            try:
                # 使用工作区路径作为项目根目录
                new_project = self.workspace.project_manager.create_project(project_name)
                
                # 重新加载项目列表
                self.load_existing_projects()
                
                # 使用自定义对话框显示成功消息
                from app.ui.dialog import CustomDialog
                dialog = CustomDialog(self)
                dialog.set_title(tr("项目创建成功"))
                
                # 创建内容布局
                content_layout = QVBoxLayout()
                
                # 消息标签
                message_label = QLabel(tr("项目 '{}' 创建成功！").format(project_name))
                message_label.setStyleSheet("color: #E1E1E1; font-size: 14px;")
                message_label.setWordWrap(True)
                content_layout.addWidget(message_label)
                
                # 确定按钮
                ok_button = QPushButton(tr("确定"))
                ok_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3d3f4e;
                        color: #E1E1E1;
                        border: 1px solid #505254;
                        border-radius: 5px;
                        padding: 6px 15px;
                        font-size: 14px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #444654;
                    }
                    QPushButton:pressed {
                        background-color: #005a9e;
                    }
                """)
                ok_button.clicked.connect(dialog.accept)
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                button_layout.addWidget(ok_button)
                button_layout.addStretch()
                content_layout.addLayout(button_layout)
                
                dialog.setContentLayout(content_layout)
                dialog.exec()
            except Exception as e:
                # 使用自定义对话框显示错误消息
                from app.ui.dialog import CustomDialog
                dialog = CustomDialog(self)
                dialog.set_title(tr("项目创建失败"))
                
                # 创建内容布局
                content_layout = QVBoxLayout()
                
                # 消息标签
                message_label = QLabel(tr("创建项目时出错: {}".format(str(e))))
                message_label.setStyleSheet("color: #E1E1E1; font-size: 14px;")
                message_label.setWordWrap(True)
                content_layout.addWidget(message_label)
                
                # 确定按钮
                ok_button = QPushButton(tr("确定"))
                ok_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3d3f4e;
                        color: #E1E1E1;
                        border: 1px solid #505254;
                        border-radius: 5px;
                        padding: 6px 15px;
                        font-size: 14px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #444654;
                    }
                    QPushButton:pressed {
                        background-color: #005a9e;
                    }
                """)
                ok_button.clicked.connect(dialog.accept)
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                button_layout.addWidget(ok_button)
                button_layout.addStretch()
                content_layout.addLayout(button_layout)
                
                dialog.setContentLayout(content_layout)
                dialog.exec()
    
    # def on_project_switched(self, project_name):
    #     """实现BaseWidget的on_project_switched方法，在项目切换时刷新下拉菜单"""
    #     # 更新按钮显示的项目名称
    #     self.button.setText(project_name)
    #
    #     # 保存当前项目名称
    #     old_project_name = self.workspace.project_name
    #
    #     # 临时更新workspace的项目名称以确保菜单正确刷新
    #     self.workspace.project_name = project_name
    #
    #     # 重新加载项目列表以反映最新的项目状态
    #     self.load_existing_projects()
    #
    #     # 恢复原来的项目名称，因为workspace的实际切换可能还未完成
    #     self.workspace.project_name = old_project_name

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