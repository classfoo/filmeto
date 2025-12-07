from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication, QSizePolicy
from PySide6.QtCore import Qt, QRect, QPoint, QTimer, Signal
from PySide6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QMouseEvent, QCursor
from app.data.workspace import Workspace
from utils.i18n_utils import tr
from .voice_timeline_scroll import VoiceTimelineScroll
import random
import math


class VoiceCard(QWidget):
    """配音卡片组件，可拖拽调整位置和长度，支持显示WAV波形"""
    
    # 当配音卡片被修改时发出信号
    card_changed = Signal()
    
    def __init__(self, content="", wav_file=None, parent=None):
        super().__init__(parent)
        self.content = content
        self.wav_file = wav_file
        self.waveform_data = []
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
        
        # 设置窗口标志，使其可以正确显社
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # 设置样式
        self.setStyleSheet("""
            VoiceoverCard {
                background-color: rgba(255, 215, 0, 180);
                border-radius: 4px;
                color: black;
                font-size: 10px;
            }
        """)
        
        # 双击编辑定时器
        self.double_click_timer = QTimer()
        self.double_click_timer.setSingleShot(True)
        self.double_click_timer.timeout.connect(self.handle_single_click)
        self.click_count = 0
        
        # 生成波形数据（无论是否有WAV文件）
        self.generate_waveform_data()
            
        # 启用鼠标跟踪
        self.setMouseTracking(True)
    
    def generate_waveform_data(self):
        """生成示例波形数据"""
        # 在实际应用中，这里会解析真实的WAV文件并生成波形数据
        # 为演示目的，我们生成一些随机波形数据
        self.waveform_data = []
        for i in range(self.width()):
            if self.wav_file:
                # 如果有WAV文件，生成随机波形
                value = math.sin(i * 0.2) * 10 + random.uniform(-3, 3)
            else:
                # 如果没有WAV文件，生成直线波形（默认值为0）
                value = 0
            self.waveform_data.append(value)
    
    def paintEvent(self, event):
        """绘制配音卡片和波形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        pen_color = QColor(255, 215, 0, 220)
        # 如果鼠标在边缘，高亮边框
        if self.on_left_edge or self.on_right_edge:
            pen_color = QColor(255, 255, 255, 255)  # 白色高亮
            
        # 根据鼠标悬停状态调整背景色
        background_color = QColor(255, 215, 0, 180)  # 默认背景色
        if self.hovered:
            # 鼠标悬停时使用较亮的颜色
            background_color = QColor(255, 230, 50, 200)
            
        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(pen_color, 2 if (self.on_left_edge or self.on_right_edge) else 1))
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 4, 4)
        
        # 绘制波形
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        mid_y = self.height() / 2
        for i in range(min(len(self.waveform_data), self.width())):
            x = i
            if self.wav_file and self.waveform_data[i] != 0:
                # 有WAV文件且有波形数据时，绘制实际波形
                y1 = mid_y - self.waveform_data[i] / 2
                y2 = mid_y + self.waveform_data[i] / 2
            else:
                # 没有WAV文件或没有波形数据时，绘制直线波形
                y1 = mid_y
                y2 = mid_y
            painter.drawLine(x, int(y1), x, int(y2))
        
        # 如果没有波形数据，绘制文本
        if not self.wav_file and len([x for x in self.waveform_data if x != 0]) == 0:
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont("", 9))
            
            # 文本省略处理
            text = self.content
            metrics = painter.fontMetrics()
            if metrics.horizontalAdvance(text) > self.width() - 10:
                while metrics.horizontalAdvance(text + "...") > self.width() - 10 and len(text) > 0:
                    text = text[:-1]
                text += "..."
            
            painter.drawText(QRect(5, 0, self.width() - 10, self.height()), 
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
    
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
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
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
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))  # 设置为水平调整大小光标
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
        
        # 重新生成波形数据
        self.generate_waveform_data()
        
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
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
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
        """编辑配音内容"""
        # 在实际应用中，这里会弹出一个对话框让用户编辑配音内容或选择WAV文件
        # 为简化，我们只是改变内容
        self.content = "编辑后的配音内容" if self.content == "Voiceover" else "Voiceover"
        if not self.wav_file:
            self.wav_file = "example.wav"  # 示例WAV文件
            self.generate_waveform_data()
        self.update()


class VoiceTimeline(QWidget):
    """配音时间线组件 - 带水平滚动支持"""
    
    def __init__(self, parent:QWidget,workspace: Workspace):
        super().__init__(parent)
        self.workspace = workspace
        self.items = []
        
        # 设置固定高度
        font = QFont()
        font.setPointSize(12)
        font_metrics = self.fontMetrics()
        height = font_metrics.height()
        self.setFixedHeight(max(height + 4, 24))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 创建滚动区域
        self.scroll_area = VoiceTimelineScroll(self)
        self.scroll_area.setStyleSheet("""
            VoiceTimelineScroll {
                background-color: #252525;
                border-top: 1px solid #444444;
            }
        """)
        
        # 创建内容容器来放置卡片
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background-color: #252525;
            }
        """)
        # 设置最小宽度，将在 set_content_width 中动态设置
        self.content_widget.setMinimumWidth(800)
        
        # 将内容容器放入滚动区域
        self.scroll_area.setWidget(self.content_widget)
        
        # 布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.scroll_area)
        
        # 启用鼠标跟踪和焦点
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # 初始化UI内容
        self.init_ui()
        
    def init_ui(self):
        """初始化UI内容 - 添加示例卡片"""
        # 添加几个示例配音卡片
        self.add_voiceover_card("示例配音 1")
        self.add_voiceover_card("示例配音 2")
    
    def add_voiceover_card(self, content="Voiceover", wav_file=None):
        """添加配音卡片"""
        card = VoiceCard(content, wav_file, self.content_widget)  # 父对象改为 content_widget
        card.move(10 + len(self.items) * 120, 2)  # 简单排列
        card.show()
        card.card_changed.connect(self.on_card_changed)
        self.items.append(card)
        
    def on_card_changed(self):
        """当卡片发生变化时调用"""
        # 可以在这里处理卡片变化的逻辑
        pass
        
    def mouseDoubleClickEvent(self, event):
        """双击时间线添加新的配音卡片"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 计算相对于 content_widget 的位置
            scroll_offset = self.scroll_area.horizontalScrollBar().value()
            content_x = event.pos().x() + scroll_offset
            card = VoiceCard("New Voiceover", None, self.content_widget)
            card.move(content_x, 2)
            card.show()
            card.card_changed.connect(self.on_card_changed)
            self.items.append(card)
    
    def clear_items(self):
        """清空所有配音项"""
        for item in self.items:
            item.deleteLater()
        self.items.clear()
        
    def paintEvent(self, event):
        """绘制虚线框占位符"""
        super().paintEvent(event)
        
        # 如果没有配音项，在 content_widget 上绘制虚线框占位符
        if not self.items and self.content_widget:
            painter = QPainter(self.content_widget)
            pen = QPen(Qt.PenStyle.DashLine)
            pen.setColor(Qt.GlobalColor.gray)
            painter.setPen(pen)
            # 绘制虚线框
            rect = self.content_widget.rect()
            rect.adjust(2, 2, -2, -2)  # 留出边距
            painter.drawRect(rect)
            painter.end()
    
    def set_content_width(self, width: int):
        """设置内容宽度以实现统一的滚动范围"""
        self.content_widget.setMinimumWidth(width)