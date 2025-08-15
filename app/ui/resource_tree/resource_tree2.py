import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QFileSystemModel,
    QVBoxLayout, QWidget, QStyledItemDelegate, QStyle, QHeaderView
)
from PySide6.QtCore import QDir, Qt, QModelIndex, QFileInfo, QStandardPaths
from PySide6.QtGui import QIcon


class FileTreeModel(QFileSystemModel):
    """
    自定义文件系统模型，用于支持懒加载和特定的图标/行为。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # 只显示文件夹
        self.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)
        # 设置列，我们主要用第一列（文件名）
        self.setRootPath("")

    def hasChildren(self, parent: QModelIndex) -> bool:
        """
        重写 hasChildren 以支持懒加载。
        对于目录，即使未展开也返回 True。
        """
        if not parent.isValid():
            return True

        # 检查缓存或文件系统以确定是否有子项
        # QFileSystemModel 通常会处理这部分，但我们确保它符合懒加载逻辑
        info = self.fileInfo(parent)
        if info.isDir():
            # 不立即检查子目录，让 isDirKey 决定是否需要展开
            # 这是 QFileSystemModel 的默认行为，我们保持它
            return True
        return False

    def data(self, index: QModelIndex, role: int):
        """
        重写 data 方法来自定义显示和图标。
        """
        if not index.isValid():
            return None

        if role == Qt.DecorationRole and index.column() == 0:
            # 为文件和文件夹设置图标
            file_info = self.fileInfo(index)
            if file_info.isDir():
                return QIcon.fromTheme("folder", self.style().standardIcon(QStyle.SP_DirIcon))
            else:
                return QIcon.fromTheme("text-x-generic", self.style().standardIcon(QStyle.SP_FileIcon))
        # 对于其他角色和列，使用默认实现
        return super().data(index, role)


class FileTreeView(QTreeView):
    """
    自定义 QTreeView 以实现双击展开/收起和点击图标展开/收起。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicked.connect(self.on_item_clicked)
        # 启用双缓冲以减少重绘闪烁
        self.setUniformRowHeights(True)

    def mousePressEvent(self, event):
        """
        重写 mousePressEvent 来检测是否点击了展开/收起图标区域。
        """
        index = self.indexAt(event.pos())
        if index.isValid():
            # 获取图标区域 (通常在第一列)
            rect = self.visualRect(index)
            # 假设图标在左侧，宽度大约为 indentation + icon size
            icon_width = self.indentation() + 20 # 粗略估计图标+缩进宽度
            if event.pos().x() < rect.left() + icon_width:
                # 点击了图标区域
                if self.model().hasChildren(index):
                    if self.isExpanded(index):
                        self.collapse(index)
                    else:
                        self.expand(index)
                    # 处理完图标点击后，不继续传递事件，避免选中行
                    return

        # 如果不是点击图标，则执行默认行为（如选中行）
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        重写 mouseDoubleClickEvent 来实现双击展开/收起整个节点。
        """
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == 0: # 通常只在第一列双击有效
            if self.model().hasChildren(index):
                if self.isExpanded(index):
                    self.collapse(index)
                else:
                    self.expand(index)
                # 双击事件被处理，不需要默认的编辑行为
                return

        # 如果双击的不是可展开的节点，或者不是第一列，则执行默认行为
        super().mouseDoubleClickEvent(event)

    def on_item_clicked(self, index: QModelIndex):
        """
        处理项目被单击的信号（用于调试或其它逻辑，此处非必需）。
        """
        # print(f"Item clicked: {self.model().filePath(index)}")
        pass


class MainWindow(QMainWindow):
    """
    主窗口，包含文件树视图。
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 文件浏览树 (PyCharm 风格)")
        self.setGeometry(300, 300, 600, 400)

        # 创建中央控件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建自定义模型和视图
        self.model = FileTreeModel()
        self.tree_view = FileTreeView()
        self.tree_view.setModel(self.model)

        # --- 配置视图样式以模仿 PyCharm ---
        # 隐藏标题栏 (PyCharm 树没有列标题)
        self.tree_view.setHeaderHidden(True)
        # 只显示第一列 (文件名)
        for i in range(1, self.model.columnCount()):
            self.tree_view.hideColumn(i)
        # 设置根索引为用户主目录或当前工作目录
        # root_path = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        root_path = ".."  # 使用当前脚本所在目录作为根目录方便测试
        root_index = self.model.setRootPath(root_path)
        self.tree_view.setRootIndex(root_index)

        # 可选：调整列宽以适应内容
        self.tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # 将视图添加到布局
        layout.addWidget(self.tree_view)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用程序图标 (可选)
    app.setWindowIcon(QIcon.fromTheme("system-file-manager"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())