import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QColorDialog, QScrollArea, QFrame, QButtonGroup, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QPoint, Signal, QRect
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QIcon


# --- 自定义工具按钮 ---
class ToolButton(QPushButton):
    """自定义工具按钮，带有图标和文本"""

    def __init__(self, text="", icon_text="", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText(text)
        if icon_text:
            self.setIcon(QIcon())
            self.setText(icon_text + "\n" + text)
        # 增加按钮宽度以适应单列
        self.setStyleSheet("""
            ToolButton {
                padding: 10px 5px; /* 上下 padding 增大 */
                margin: 4px 8px;   /* 左右 margin 增大 */
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #e8e8e8;
                font-size: 11px;
                text-align: center;
                min-width: 80px; /* 设置最小宽度 */
            }
            ToolButton:hover {
                background-color: #d8d8d8;
            }
            ToolButton:checked {
                background-color: #a0c4e8;
                border: 2px solid #555;
            }
        """)


# --- 悬浮工具板 (修改为单列并吸附左侧) ---
class FloatingToolBar(QWidget):
    """
    单列布局的悬浮工具栏，吸附在主窗口左侧。
    """
    toolSelected = Signal(str)

    def __init__(self, drawing_widget, main_window, parent=None):
        super().__init__(parent)  # parent 现在是 MainWindow
        self.drawing_widget = drawing_widget
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint)

        # --- 样式调整 ---
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(245, 245, 245, 240); /* 更不透明 */
                border: 1px solid gray;
                border-top: none;    /* 隐藏顶边框 */
                border-bottom: none; /* 隐藏底边框 */
                border-left: none;   /* 隐藏左边框 */
                border-radius: 0px;  /* 移除圆角 */
                padding: 5px 0px;    /* 上下有padding, 左右无 */
            }
        """)

        # 固定宽度
        self.setFixedWidth(110)  # 可根据按钮宽度调整

        # --- 布局 ---
        # 使用 QVBoxLayout 实现单列
        # 将滚动区域直接作为主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 滚动区域自己控制内边距
        self.main_layout.setSpacing(0)  # 按钮组与拉伸之间的间距

        # 创建滚动区域以容纳所有工具
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示垂直滚动条
        # 滚动区域内容样式
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; } 
            QWidget { background-color: transparent; } /* 滚动区域内容背景透明 */
        """)

        # 工具按钮容器
        self.tools_widget = QWidget()
        self.tools_layout = QVBoxLayout(self.tools_widget)
        self.tools_layout.setContentsMargins(0, 0, 0, 0)  # 容器无内边距
        self.tools_layout.setSpacing(3)  # 按钮间距
        self.tools_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.tools_widget)
        self.main_layout.addWidget(self.scroll_area)

        # --- 工具定义 ---
        tools_data = [
            ("铅笔", "✏️", "pencil"),
            ("毛笔", "🖌️", "brush"),
            ("颜色", "🎨", "color"),
            ("图形", "⬜", "shapes"),
            ("橡皮", "🧹", "eraser"),
            ("套索", "🔗", "lasso"),
            ("印章", "🖼️", "stamp"),
            ("图层", "🗂️", "layers"),
            ("模糊", "🌫️", "blur"),
            ("马赛克", "🪟", "mosaic"),
            ("AI生成", "🤖", "ai_generate"),
            ("图生图", "🖼️➡️🖼️", "image_to_image"),
            ("文生图", "📝➡️🖼️", "text_to_image"),
            ("图生视频", "🖼️➡️🎥", "image_to_video"),
        ]

        self.tool_buttons = {}
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # 创建按钮并添加到布局
        for text, icon_text, tool_id in tools_data:
            button = ToolButton(text, icon_text)
            button.setObjectName(tool_id)
            button.clicked.connect(self.on_tool_button_clicked)
            self.tool_buttons[tool_id] = button
            self.button_group.addButton(button)
            self.tools_layout.addWidget(button)

        # 默认选中铅笔
        if "pencil" in self.tool_buttons:
            self.tool_buttons["pencil"].setChecked(True)
            self.current_tool = "pencil"
        else:
            self.current_tool = None

    def on_tool_button_clicked(self):
        button = self.sender()
        if button and button.isChecked():
            tool_id = button.objectName()
            self.current_tool = tool_id
            print(f"工具已选中: {tool_id}")
            self.toolSelected.emit(tool_id)

            if tool_id == "color":
                color = QColorDialog.getColor(initial=Qt.black, parent=self, options=QColorDialog.DontUseNativeDialog)
                if color.isValid():
                    print(f"选择的颜色: {color.name()}")
                    if self.drawing_widget:
                        self.drawing_widget.set_pen_color(color)
                button.setChecked(False)
                if self.current_tool == "pencil":
                    self.tool_buttons["pencil"].setChecked(True)
            elif tool_id in ["ai_generate", "image_to_image", "text_to_image", "image_to_video", "shapes", "layers"]:
                QMessageBox.information(self, "工具", f"选择了 {tool_id} 工具。\n这是一个高级功能占位符。")
                button.setChecked(False)
                self.tool_buttons.get(self.current_tool, None).setChecked(True)

    def update_position_and_size(self):
        """根据主窗口大小更新自身位置和大小"""
        if self.main_window:
            main_window_rect = self.main_window.rect()  # 获取主窗口内部区域（不包括边框）
            # 设置位置在主窗口内部的最左边
            self.move(0, 0)  # 相对于 MainWindow 的位置
            # 设置高度为与主窗口内部高度一致
            self.setFixedHeight(main_window_rect.height())
            # 宽度已在 __init__ 中固定


# --- 画图部件 ---
class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_StaticContents)
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(Qt.white)
        self.last_point = QPoint()
        self.is_drawing = False
        self.pen_color = Qt.black
        self.pen_width = 3
        self.current_tool = "pencil"

        # 注意：toolbar 现在由 MainWindow 创建和管理
        self.toolbar = None  # 将在 MainWindow 中设置

    def resizeEvent(self, event):
        if event.oldSize().isValid():
            new_pixmap = QPixmap(self.size())
            new_pixmap.fill(Qt.white)
            painter = QPainter(new_pixmap)
            painter.drawPixmap(QPoint(0, 0), self.pixmap)
            painter.end()
            self.pixmap = new_pixmap
        else:
            self.pixmap = QPixmap(self.size())
            self.pixmap.fill(Qt.white)
        # 工具栏位置更新由 MainWindow 管理
        super().resizeEvent(event)

    def set_pen_color(self, color):
        self.pen_color = color

    def on_tool_selected(self, tool_name):
        self.current_tool = tool_name
        print(f"画图部件收到工具选择: {tool_name}")

    def clear_canvas(self):
        self.pixmap.fill(Qt.white)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = event.position().toPoint()
            if self.current_tool in ["pencil", "brush", "eraser"]:
                self.is_drawing = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.is_drawing:
            painter = QPainter(self.pixmap)
            if self.current_tool == "pencil":
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            elif self.current_tool == "brush":
                pen = QPen(self.pen_color, self.pen_width + 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            elif self.current_tool == "eraser":
                pen = QPen(Qt.white, self.pen_width * 2, Qt.SolidLine, Qt.SquareCap, Qt.BevelJoin)
            else:
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.position().toPoint())
            painter.end()
            self.last_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_drawing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(QPoint(0, 0), self.pixmap)


# --- 主窗口 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 画图板 (单列工具板吸附左侧)")
        self.setGeometry(100, 100, 950, 680)

        self.drawing_widget = DrawingWidget()
        # --- 关键修改：设置中央部件 ---
        self.setCentralWidget(self.drawing_widget)

        # --- 关键修改：创建并管理工具栏 ---
        # 工具栏的父对象是 MainWindow 本身
        self.toolbar = FloatingToolBar(self.drawing_widget, self, self)
        self.drawing_widget.toolbar = self.toolbar  # 反向引用
        self.toolbar.toolSelected.connect(self.drawing_widget.on_tool_selected)
        self.toolbar.show()

        # --- 背景色 ---
        self.setStyleSheet("QMainWindow { background-color: #d0d0d0; }")

    def resizeEvent(self, event):
        """重写 resizeEvent 以更新工具栏大小和位置"""
        super().resizeEvent(event)
        # 确保在主窗口大小调整后更新工具栏
        if self.toolbar:
            self.toolbar.update_position_and_size()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())