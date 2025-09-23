import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout,
    QLabel, QVBoxLayout, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QKeyEvent, QPixmap, QColor

from app.data.timeline import Timeline
from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget, BaseTaskWidget
from app.ui.draggable_scroll_area import DraggableScrollArea
from app.ui.hover_zoom_frame import HoverZoomFrame


class HorizontalTimeline(BaseTaskWidget):
    """左右滑动的卡片式时间线主窗口"""
    def __init__(self,parent:QWidget,workspace:Workspace):
        super().__init__(workspace)
        self.setWindowTitle("TimeLine")
        self.resize(parent.width(), parent.height())
        self.setContentsMargins(5,5,5,5)

        # ------------------- 创建可滚动区域 -------------------
        self.scroll_area = DraggableScrollArea()
        self.scroll_area.setWidgetResizable(True) # 内容 widget 可随区域大小调整
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # 水平滚动条按需显示
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # 关闭垂直滚动条
        self.scroll_area.setStyleSheet(f"""
            DraggableScrollArea {{
                background-color: #1e1f22;
            }}
        """)
        # ------------------- 创建内容容器和布局 -------------------
        self.content_widget = BaseWidget(workspace)
        self.content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: #1e1f22;
            }}
        """)
        self.timeline_layout = QHBoxLayout(self.content_widget)
        self.timeline_layout.setContentsMargins(5, 5, 5, 5) # 左右留出边距，方便滑动
        self.timeline_layout.setSpacing(5) # 卡片之间的间距
        # 将内容容器放入滚动区域
        self.scroll_area.setWidget(self.content_widget)

        # ------------------- 添加一些示例卡片 -------------------
        timeline = workspace.project().timeline()
        timeline_item_count = timeline.itemCount()
        self.cards = []
        for i in range(timeline_item_count):  # 创建 10 个示例卡片
            timeline_item = timeline.getItem(i+1)
            snapshot_image = timeline_item.getSnapshotImage()
            title = f"# {i+1}"
            card = HoverZoomFrame(title, snapshot_image,self)
            self.timeline_layout.addWidget(card)
            self.cards.append(card)
        self.timeline_layout.addStretch()
        # ------------------- 主窗口布局 -------------------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.scroll_area)

        # 可选：添加一些说明
        # info_label = QLabel("提示：鼠标拖动或使用左右方向键滑动时间线")
        # info_label.setAlignment(Qt.AlignCenter)
        # main_layout.addWidget(info_label)

        # 聚焦以接收键盘事件
        self.scroll_area.setFocusPolicy(Qt.StrongFocus)
        self.scroll_area.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        """重写键盘事件，支持左右方向键滑动"""
        if isinstance(event, QKeyEvent):
            scroll_bar = self.scroll_area.horizontalScrollBar()
            current_value = scroll_bar.value()

            if event.key() == Qt.Key_Left:
                # 向左滑动（值减小）
                scroll_bar.setValue(current_value - 50)
            elif event.key() == Qt.Key_Right:
                # 向右滑动（值增加）
                scroll_bar.setValue(current_value + 50)
            else:
                # 如果不是左右键，调用父类处理其他事件（如关闭窗口的 Esc）
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def on_task_finished(self, result):
        timeline_index = result.get_timeline()
        card = self.cards[timeline_index-1]
        snapshot_path = result.get_image()
        original_pixmap= QPixmap(snapshot_path)
        card.setImage(original_pixmap)
        return

# ------------------- 运行应用 -------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HorizontalTimeline()
    window.show()
    sys.exit(app.exec())