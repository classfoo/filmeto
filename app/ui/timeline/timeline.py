import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout,
    QLabel, QVBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QPixmap

from app.data.timeline import TimelineItem
from app.data.workspace import Workspace
from app.ui.base_widget import BaseWidget, BaseTaskWidget
from app.ui.timeline.draggable_scroll_area import DraggableScrollArea
from app.ui.timeline.hover_zoom_frame import HoverZoomFrame
from utils import qt_utils
from utils.i18n_utils import tr, translation_manager


class AddCardFrame(QFrame):
    """Special frame for adding new cards to the timeline"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Basic configuration
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 2px dashed #666666;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #3c3c3c;
                border: 2px dashed #8888ff;
            }
        """)
        
        # Set initial size
        self.setMinimumSize(90, 160)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Enable mouse tracking
        self.setMouseTracking(True)

        # Content layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        # Title label
        self.title_label = QLabel(tr("Add Card"))
        self.title_label.setAlignment(Qt.AlignCenter)
        font = self.title_label.font()
        font.setPointSize(10)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.title_label)

        # Set cursor to indicate clickable
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        """Handle mouse click event to add a new card"""
        if event.button() == Qt.LeftButton:
            if hasattr(self.parent, 'add_new_card'):
                self.parent.add_new_card()


class HorizontalTimeline(BaseTaskWidget):
    """左右滑动的卡片式时间线主窗口"""
    def __init__(self,parent:QWidget,workspace:Workspace):
        super().__init__(workspace)
        self.setWindowTitle(tr("TimeLine"))
        self.resize(parent.width(), parent.height())
        self.setContentsMargins(5,5,5,5)
        self.selected_card_index = None  # 跟踪当前选中的卡片索引
        
        # Set size policy to prevent vertical expansion
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

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
        timeline = workspace.get_project().get_timeline()
        timeline_item_count = timeline.get_item_count()
        self.cards = []
        for i in range(timeline_item_count):  # 创建 10 个示例卡片
            index = i+1
            timeline_item = timeline.get_item(index)
            snapshot_image = timeline_item.get_image()
            title = f"# {i+1}"
            card = HoverZoomFrame(self, title, snapshot_image, index)
            self.timeline_layout.addWidget(card)
            self.cards.append(card)
        
        # Set the timeline to the current index from project config instead of always jumping to 1
        current_index = workspace.get_project().get_timeline_index()
        if 1 <= current_index <= timeline_item_count:
            timeline.set_item_index(current_index)
            self.selected_card_index = current_index
            # 设置当前选中的卡片为选中状态
            if self.cards:
                self.cards[current_index - 1].set_selected(True)
        else:
            # If current index is out of bounds, default to 1
            timeline.set_item_index(1)
            self.selected_card_index = 1
            if self.cards:
                self.cards[0].set_selected(True)
        # Add the "Add Card" button at the end
        self.add_card_button = AddCardFrame(self)
        self.timeline_layout.addWidget(self.add_card_button)
        
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
        
        # Connect to language change signal
        translation_manager.language_changed.connect(self.retranslateUi)
        
        # Connect timeline switch signal to update card images
        self.workspace.connect_timeline_switch(self.on_timeline_switch)

    def retranslateUi(self):
        """更新所有UI文本当语言变化时"""
        self.setWindowTitle(tr("TimeLine"))
        # Update Add Card button label
        if hasattr(self, 'add_card_button') and self.add_card_button:
            self.add_card_button.title_label.setText(tr("Add Card"))
    
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
        timeline_index = result.get_timeline_index()
        card = self.cards[timeline_index-1]
        image_path = result.get_image_path()
        if image_path is not None:
            original_pixmap= QPixmap(image_path)
            card.setImage(original_pixmap)
        return
    
    def add_new_card(self):
        """Add a new card to the timeline"""
        try:
            timeline = self.workspace.get_project().get_timeline()
            new_index = timeline.add_item()
            self.timeline_layout.removeWidget(self.add_card_button)
            qt_utils.remove_last_stretch(self.timeline_layout)
            # 修复：使用新索引获取时间线项，然后获取图像
            new_timeline_item = timeline.get_item(new_index)
            snapshot_image = new_timeline_item.get_image()
            title = f"# {new_index}"
            new_card = HoverZoomFrame(self, title, snapshot_image, new_index)
            
            # Add the new card
            self.timeline_layout.addWidget(new_card)
            self.cards.append(new_card)
            
            # Re-add the add button and stretch
            self.timeline_layout.addWidget(self.add_card_button)
            self.timeline_layout.addStretch()
            
            # Update the timeline index to the newly created card
            timeline.set_item_index(new_index)
            
            # Force a layout update
            self.content_widget.update()
            self.update()
            
        except Exception as e:
            print(f"Error adding new card: {e}")
            import traceback
            traceback.print_exc()

    def on_timeline_switch(self, item: TimelineItem):
        """Handle timeline switch to update card images"""
        # Update the image for the card corresponding to the switched timeline item
        index = item.get_index()
        if 1 <= index <= len(self.cards):
            # Load the new image and update the card
            pixmap = item.get_image()
            self.cards[index-1].setImage(pixmap)
    
    def on_project_switched(self, project_name):
        """处理项目切换"""
        # 清除现有的卡片
        for card in self.cards:
            self.timeline_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        
        # 移除添加卡片按钮和占位符
        self.timeline_layout.removeWidget(self.add_card_button)
        qt_utils.remove_last_stretch(self.timeline_layout)
        
        # 重新加载新项目的时间线卡片
        timeline = self.workspace.get_project().get_timeline()
        timeline_item_count = timeline.get_item_count()
        
        for i in range(timeline_item_count):
            index = i + 1
            timeline_item = timeline.get_item(index)
            snapshot_image = timeline_item.get_image()
            title = f"# {index}"
            card = HoverZoomFrame(self, title, snapshot_image, index)
            self.timeline_layout.addWidget(card)
            self.cards.append(card)
        
        # 重新添加"添加卡片"按钮和占位符
        self.timeline_layout.addWidget(self.add_card_button)
        self.timeline_layout.addStretch()
        
        # 重置选中状态
        self.selected_card_index = None
        current_index = self.workspace.get_project().get_timeline_index()
        if 1 <= current_index <= timeline_item_count:
            timeline.set_item_index(current_index)
            self.selected_card_index = current_index
            if self.cards:
                self.cards[current_index - 1].set_selected(True)
        else:
            # 如果当前索引超出范围，默认为1
            timeline.set_item_index(1)
            self.selected_card_index = 1
            if self.cards:
                self.cards[0].set_selected(True)

    def on_mouse_press_card(self,index):
        # 取消之前选中卡片的选中状态
        if self.selected_card_index is not None and 1 <= self.selected_card_index <= len(self.cards):
            self.cards[self.selected_card_index - 1].set_selected(False)
        
        # 设置新选中的卡片
        self.selected_card_index = index
        if 1 <= index <= len(self.cards):
            self.cards[index - 1].set_selected(True)
        
        self.workspace.get_project().get_timeline().set_item_index(index)

# ------------------- 运行应用 -------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HorizontalTimeline()
    window.show()
    sys.exit(app.exec())