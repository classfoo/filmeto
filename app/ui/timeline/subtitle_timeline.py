from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication
from PySide6.QtCore import Qt, QRect, QPoint, QTimer, Signal
from PySide6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QMouseEvent, QCursor
from app.data.workspace import Workspace
from utils.i18n_utils import tr


class SubtitleCard(QWidget):
    """字幕卡片组件，可拖拽调整位置和长度"""
    
    # 当字幕卡片被修改时发出信号
    card_changed = Signal()
    
    def __init__(self, content="", parent=None):
        super().__init__(parent)
        self.content = content
        self.setFixedHeight(20)
        self.setMinimumWidth(50)
        self.resize(100, 20)
        
        # 拖拽相关属性
        self.dragging = False
        self.resizing_left = False
        self.resizing_right = False
        self.drag_start_pos = QPoint()
        self.original_geometry = QRect()
        
        # 边缘检测相关属性
        self.edge_size = 5  # 边缘检测区域大小
        self.on_left_edge = False
        self.on_right_edge = False
        
        # 鼠标悬停状态
        self.hovered = False
        
        # 设置窗口标志，使其可以正确显示
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 设置样式
        self.setStyleSheet("""
            SubtitleCard {
                background-color: rgba(30, 144, 255, 180);
                border-radius: 4px;
                color: white;
                font-size: 10px;
            }
        """)
        
        # 双击编辑定时器
        self.double_click_timer = QTimer()
        self.double_click_timer.setSingleShot(True)
        self.double_click_timer.timeout.connect(self.handle_single_click)
        self.click_count = 0
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        """绘制字幕卡片"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        pen_color = QColor(30, 144, 255, 220)
        # 如果鼠标在边缘，高亮边框
        if self.on_left_edge or self.on_right_edge:
            pen_color = QColor(255, 255, 255, 255)  # 白色高亮
            
        # 根据鼠标悬停状态调整背景色
        background_color = QColor(30, 144, 255, 180)  # 默认背景色
        if self.hovered:
            # 鼠标悬停时使用较亮的颜色
            background_color = QColor(65, 170, 255, 200)
            
        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(pen_color, 2 if (self.on_left_edge or self.on_right_edge) else 1))
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 4, 4)
        
        # 绘制文本
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("", 9))
        
        # 文本省略处理
        text = self.content
        metrics = painter.fontMetrics()
        if metrics.horizontalAdvance(text) > self.width() - 10:
            while metrics.horizontalAdvance(text + "...") > self.width() - 10 and len(text) > 0:
                text = text[:-1]
            text += "..."
        
        painter.drawText(QRect(5, 0, self.width() - 10, self.height()), 
                         Qt.AlignVCenter | Qt.AlignLeft, text)
    
    def enterEvent(self, event):
        """处理鼠标进入事件"""
        self.hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """处理鼠标离开事件"""
        self.hovered = False
        self.on_left_edge = False
        self.on_right_edge = False
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.update()
        super().leaveEvent(event)
    
    def is_on_edge(self, pos):
        """检查鼠标是否在边缘区域"""
        self.on_left_edge = pos.x() <= self.edge_size
        self.on_right_edge = pos.x() >= self.width() - self.edge_size
        return self.on_left_edge or self.on_right_edge
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件"""
        # 检查鼠标是否在边缘
        if self.is_on_edge(event.pos()):
            if self.on_left_edge or self.on_right_edge:
                self.setCursor(QCursor(Qt.SizeHorCursor))  # 设置为水平调整大小光标
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))  # 恢复默认光标
            self.on_left_edge = False
            self.on_right_edge = False
            
        self.update()  # 重绘以显示高亮效果
        
        if not (self.dragging or self.resizing_left or self.resizing_right):
            super().mouseMoveEvent(event)
            return
            
        delta = event.globalPos() - self.drag_start_pos
        
        if self.dragging:
            # 拖拽移动位置
            new_x = self.original_geometry.x() + delta.x()
            new_y = self.original_geometry.y()  # 保持在同一水平线上
            self.move(max(0, new_x), new_y)
        elif self.resizing_left:
            # 调整左侧大小
            new_width = self.original_geometry.width() - delta.x()
            new_x = self.original_geometry.x() + delta.x()
            if new_width >= 50:  # 最小宽度
                self.setGeometry(new_x, self.original_geometry.y(), new_width, self.original_geometry.height())
        elif self.resizing_right:
            # 调整右侧大小
            new_width = self.original_geometry.width() + delta.x()
            if new_width >= 50:  # 最小宽度
                self.resize(new_width, self.height())
        
        self.card_changed.emit()
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.click_count += 1
            if self.click_count == 1:
                self.double_click_timer.start(QApplication.doubleClickInterval())
            
            self.drag_start_pos = event.globalPos()
            self.original_geometry = self.geometry()
            
            # 检查是否在调整大小的边缘上
            if self.is_on_edge(event.pos()):
                if self.on_left_edge:
                    self.resizing_left = True
                elif self.on_right_edge:
                    self.resizing_right = True
            else:
                self.dragging = True
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """处理鼠标释放事件"""
        self.dragging = False
        self.resizing_left = False
        self.resizing_right = False
        # 恢复光标
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.on_left_edge = False
        self.on_right_edge = False
        self.update()  # 重绘以移除高亮效果
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """处理双击事件"""
        self.click_count = 0
        self.double_click_timer.stop()
        self.edit_content()
    
    def handle_single_click(self):
        """处理单击事件"""
        self.click_count = 0
        # 可以在这里添加单击选中的逻辑
    
    def edit_content(self):
        """编辑字幕内容"""
        # 在实际应用中，这里会弹出一个对话框让用户编辑字幕内容
        # 为简化，我们只是改变内容
        self.content = "编辑后的字幕内容" if self.content == "Subtitle" else "Subtitle"
        self.update()


class SubtitleTimeline(QWidget):
    """字幕时间线组件"""
    
    def __init__(self, parent:QWidget,workspace: Workspace):
        super().__init__(parent)
        self.workspace = workspace
        self.items = []
        self.init_ui()
        
        # 启用鼠标跟踪和焦点
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def init_ui(self):
        # 设置固定高度为12pt对应的高度
        font = QFont()
        font.setPointSize(12)
        font_metrics = self.fontMetrics()
        height = font_metrics.height()
        self.setFixedHeight(max(height + 4, 24))  # 确保最小高度，添加一些内边距
        
        # 设置样式
        self.setStyleSheet("""
            SubtitleTimeline {
                background-color: #252525;
                border-bottom: 1px solid #444444;
            }
        """)
        
        # 添加几个示例子幕卡片
        self.add_subtitle_card("示例字幕 1")
        self.add_subtitle_card("示例字幕 2")
    
    def add_subtitle_card(self, content="Subtitle"):
        """添加字幕卡片"""
        card = SubtitleCard(content, self)
        card.move(10 + len(self.items) * 120, 2)  # 简单排列
        card.show()
        card.card_changed.connect(self.on_card_changed)
        self.items.append(card)
        
    def on_card_changed(self):
        """当卡片发生变化时调用"""
        # 可以在这里处理卡片变化的逻辑
        pass
        
    def mouseDoubleClickEvent(self, event):
        """双击时间线添加新的字幕卡片"""
        if event.button() == Qt.LeftButton:
            card = SubtitleCard("New Subtitle", self)
            card.move(event.pos().x(), 2)
            card.show()
            card.card_changed.connect(self.on_card_changed)
            self.items.append(card)
    
    def clear_items(self):
        """清空所有字幕项"""
        for item in self.items:
            item.deleteLater()
        self.items.clear()
        
    def paintEvent(self, event):
        """绘制虚线框占位符"""
        super().paintEvent(event)
        
        # 如果没有字幕项，绘制虚线框占位符
        if not self.items:
            painter = QPainter(self)
            pen = QPen(Qt.DashLine)
            pen.setColor(Qt.gray)
            painter.setPen(pen)
            # 绘制虚线框
            rect = self.rect()
            rect.adjust(2, 2, -2, -2)  # 留出边距
            painter.drawRect(rect)
            painter.end()