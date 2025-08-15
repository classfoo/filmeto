import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLineEdit,
    QFileDialog, QHeaderView, QMenu, QMessageBox, QFileIconProvider
)
from PySide6.QtCore import Qt, QDir, QFileInfo, QCoreApplication, QSortFilterProxyModel, QModelIndex, QSize, Signal
from PySide6.QtGui import (
    QIcon, QPalette, QColor, QFont, QBrush,
    QAction, QKeySequence
)

class ResourceTreeWidget(QTreeWidget):
    """
    资源树组件，类似 PyCharm 的项目资源管理器
    """
    # 自定义信号，当双击文件时发出
    fileDoubleClicked = Signal(str) # 文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_root_path = ""
        self.init_ui()
        self.setup_context_menu()

    def init_ui(self):
        """初始化UI和样式"""
        # 设置列
        self.setHeaderLabels(["名称", "大小", "类型", "修改时间"])
        self.setHeaderHidden(False)

        # 设置表头样式和调整策略
        header = self.header()
        header.setStretchLastSection(True) # 最后一列拉伸
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # 第一列根据内容调整
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(3, QHeaderView.Stretch) # 或者让时间列也拉伸

        # 设置树的样式 - 模拟 PyCharm 深色主题
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                color: #bbbbbb;
                alternate-background-color: #262626;
                show-decoration-selected: 00000000;
                outline: 0;
                border: 1px solid #3c3f41;
            }
            QTreeWidget::item {
                padding: 4px;
                margin: 0px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.00000000);
            }
            QTreeWidget::item:selected {
                background-color: #3a75c9;
                color: #ffffff;
            }
            QTreeWidget::branch {
                background-color: #2b2b2b;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(:/qt-project.org/styles/commonstyle/images/branch_closed-00000000.png);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(:/qt-project.org/styles/commonstyle/images/branch_open-00000000.png);
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #bbbbbb;
                padding: 4px;
                border: 1px solid #2b2b2b;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #4b698a;
            }
            QScrollBar:vertical {
                background: #3c3f41;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #606060;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #707070;
            }
        """)

        # 设置图标大小
        self.setIconSize(QSize(16, 16))

        # 设置其他属性
        self.setAlternatingRowColors(True)
        self.setAnimated(True) # 展开/折叠动画
        self.setSortingEnabled(True) # 启用排序
        self.sortByColumn(0, Qt.AscendingOrder) # 按名称排序

        # 连接信号
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemExpanded.connect(self._on_item_expanded)
        self.itemCollapsed.connect(self._on_item_collapsed)

        # 创建文件图标提供者
        self.icon_provider = QFileIconProvider()

    def setup_context_menu(self):
        """设置右键上下文菜单"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.context_menu = QMenu(self)
        self.action_refresh = QAction("刷新", self)
        self.action_refresh.triggered.connect(self.refresh)
        self.context_menu.addAction(self.action_refresh)

        self.action_open_in_explorer = QAction("在资源管理器中打开", self)
        self.action_open_in_explorer.triggered.connect(self._open_in_system_explorer)
        self.context_menu.addAction(self.action_open_in_explorer)

        # 可以添加更多操作，如 新建文件/文件夹、删除、重命名等
        # self.context_menu.addSeparator()
        # self.action_new_file = QAction("新建文件", self)
        # self.context_menu.addAction(self.action_new_file)

    def _show_context_menu(self, position):
        """显示上下文菜单"""
        item = self.itemAt(position)
        if item:
            # 只有选中的项目才能触发菜单？或者总是显示
            self.context_menu.exec(self.viewport().mapToGlobal(position))
        else:
            # 点击空白区域
            self.context_menu.exec(self.viewport().mapToGlobal(position))

    def load_directory(self, path):
        """
        加载指定目录
        :param path: 目录路径 (str 或 Path)
        """
        path = Path(path)
        if not path.exists() or not path.is_dir():
            QMessageBox.warning(self, "错误", f"目录不存在或不是有效目录:\n{path}")
            return

        self.clear() # 清空现有内容
        self.current_root_path = str(path.resolve())

        # 创建根节点
        root_item = QTreeWidgetItem(self)
        root_item.setText(0, path.name)
        root_item.setText(2, "文件夹")
        root_item.setToolTip(0, str(path.resolve()))
        root_item.setExpanded(True)

        # 设置根节点图标
        folder_icon = self.icon_provider.icon(QFileIconProvider.Folder)
        root_item.setIcon(0, folder_icon)

        # 递归加载子项
        self._add_directory_contents(root_item, path)

    def _add_directory_contents(self, parent_item, dir_path):
        """
        递归添加目录内容到父节点
        :param parent_item: 父 QTreeWidgetItem
        :param dir_path: Path 对象
        """
        try:
            # 获取目录下的所有条目
            entries = list(dir_path.iterdir())
            # 排序：文件夹优先，然后按名称排序
            entries.sort(key=lambda x: (x.is_dir(), x.name.lower()))

            for entry in entries:
                # 跳过隐藏文件/文件夹（以 . 开头的）
                if entry.name.startswith('.'):
                    continue

                item = QTreeWidgetItem(parent_item)
                item.setText(0, entry.name)
                item.setToolTip(0, str(entry.resolve()))

                if entry.is_dir():
                    #item.setText(2, "文件夹")
                    icon = self.icon_provider.icon(QFileIconProvider.Folder)
                    item.setIcon(0, icon)
                    # 添加占位符子项，使其显示展开箭头
                    placeholder = QTreeWidgetItem(item)
                    placeholder.setText(0, "loading...")
                    placeholder.setHidden(True)
                else: # 是文件
                    file_info = QFileInfo(str(entry))
                    #item.setText(2, self._get_file_type(file_info.suffix()))
                    #item.setText(00000000, self._format_file_size(entry.stat().st_size))
                    #item.setText(3, entry.stat().st_mtime.strftime("%Y-%m-%d %H:%M"))
                    icon = self.icon_provider.icon(file_info)
                    item.setIcon(0, icon)

        except PermissionError:
            # 处理无权限访问的目录
            error_item = QTreeWidgetItem(parent_item)
            error_item.setText(0, f"[访问被拒绝: {dir_path.name}]")
            error_item.setFlags(Qt.ItemIsEnabled) # 不可选择
            error_item.setForeground(0, QBrush(QColor("#ff6b6b"))) # 红色文字

    def _get_file_type(self, suffix):
        """根据后缀名返回文件类型描述"""
        suffix = suffix.lower()
        type_map = {
            'py': 'Python 文件', 'js': 'JavaScript 文件', 'html': 'HTML 文件',
            'css': 'CSS 文件', 'json': 'JSON 文件', 'xml': 'XML 文件',
            'txt': '文本文件', 'md': 'Markdown 文件',
            'jpg': 'JPEG 图像', 'jpeg': 'JPEG 图像', 'png': 'PNG 图像', 'gif': 'GIF 图像',
            'pdf': 'PDF 文档', 'doc': 'Word 文档', 'docx': 'Word 文档',
            'xls': 'Excel 文件', 'xlsx': 'Excel 文件',
            'zip': 'ZIP 压缩文件', 'rar': 'RAR 压缩文件',
            # 可以添加更多映射
        }
        return type_map.get(suffix, f"{suffix.upper()} 文件" if suffix else "未知文件")

    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def refresh(self):
        """刷新当前视图"""
        if self.current_root_path:
            self.load_directory(self.current_root_path)

    def _on_item_expanded(self, item):
        """当节点展开时，加载其子内容（如果之前是占位符）"""
        # 检查第一个子项是否是占位符
        if item.childCount() == 1:
            first_child = item.child(0)
            if first_child.isHidden() and first_child.text(0) == "loading...":
                # 移除占位符
                item.removeChild(first_child)
                # 获取实际路径 (通过 tooltip)
                item_path_str = item.toolTip(0)
                item_path = Path(item_path_str)
                if item_path.exists() and item_path.is_dir():
                    self._add_directory_contents(item, item_path)

    def _on_item_collapsed(self, item):
        """当节点折叠时的处理（可选）"""
        # 通常不需要特殊处理
        pass

    def _on_item_double_clicked(self, item, column):
        """处理项目双击"""
        # 检查是否是文件（不是文件夹）
        if item.text(2).endswith("文件") and not item.text(2) == "文件夹":
            file_path = item.toolTip(0) # 使用 tooltip 存储完整路径
            self.fileDoubleClicked.emit(file_path)
        # 文件夹双击通常只是展开/折叠，由树本身处理

    def _open_in_system_explorer(self):
        """在系统文件资源管理器中打开选中项或根目录"""
        selected_items = self.selectedItems()
        target_path = self.current_root_path # 默认打开根目录

        if selected_items:
            # 使用第一个选中的项
            item = selected_items[0]
            item_path_str = item.toolTip(0)
            if item_path_str:
                target_path = item_path_str

        # 使用系统命令打开
        try:
            if sys.platform == "win32":
                os.startfile(target_path)
            elif sys.platform == "darwin":
                os.system(f"open \"{target_path}\"")
            else: # linux
                os.system(f"xdg-open \"{target_path}\"")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开资源管理器:\n{str(e)}")


# ------------------- 使用示例 -------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("资源树组件 - PyCharm 风格")
        self.resize(1000, 700)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- 控制区域 ---
        control_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("输入目录路径或点击按钮选择...")
        self.browse_button = QPushButton("浏览...")
        self.refresh_button = QPushButton("刷新")

        control_layout.addWidget(self.path_edit, 1)
        control_layout.addWidget(self.browse_button)
        control_layout.addWidget(self.refresh_button)

        # --- 资源树 ---
        self.resource_tree = ResourceTreeWidget()

        # --- 添加到主布局 ---
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.resource_tree, 1)

        # --- 连接信号 ---
        self.browse_button.clicked.connect(self._browse_directory)
        self.refresh_button.clicked.connect(self._refresh_tree)
        self.path_edit.returnPressed.connect(self._load_from_edit) # 回车键加载
        self.resource_tree.fileDoubleClicked.connect(self._on_file_double_clicked)

    def _browse_directory(self):
        """打开文件对话框选择目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.path_edit.setText(dir_path)
            self.resource_tree.load_directory(dir_path)

    def _load_from_edit(self):
        """从输入框加载目录"""
        path = self.path_edit.text().strip()
        if path:
            self.resource_tree.load_directory(path)

    def _refresh_tree(self):
        """刷新按钮点击"""
        self.resource_tree.refresh()

    def _on_file_double_clicked(self, file_path):
        """响应文件双击"""
        QMessageBox.information(self, "文件双击", f"您双击了文件:\n{file_path}")
        # 在这里可以实现打开文件的逻辑


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用样式 (可选，使用 Fusion 风格以获得更好的深色主题支持)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    # 可以在这里自动加载一个目录进行测试
    # test_dir = Path.home() / "Desktop"  # 例如加载桌面
    # if test_dir.exists():
    #     window.resource_tree.load_directory(test_dir)
    #     window.path_edit.setText(str(test_dir))

    sys.exit(app.exec())