# 视频帧选择器功能 / Video Frame Selector Feature

## 概述 / Overview

为 `MediaPreviewWidget` 添加了视频帧选择器功能，**完全替代了传统的进度条**。在视频预览模式下显示一个支持换行的帧选择器，每个小方块代表视频中的一帧，提供更精确的帧级控制。

Added a video frame selector feature to `MediaPreviewWidget` that **completely replaces the traditional progress slider**. When in video preview mode, it displays a wrappable frame selector where each small block represents a frame in the video, providing more precise frame-level control.

## 主要功能 / Key Features

### 1. FrameBlock（帧块组件）
- 每个小方块代表视频中的一帧
- 尺寸：8x8 像素
- 状态：
  - 默认：灰色 (#666666)
  - 悬停：浅灰色 (#888888)
  - 选中：蓝色高亮 (#4080ff)

### 2. FrameSelectorWidget（帧选择器组件）
- **✨ 主要导航控件**：完全替代进度条，成为视频预览的主要时间轴控制
- **✨ 支持自动换行**：当帧数超出宽度时自动换行显示
- **✨ 自适应高度**：根据换行后的帧方块数量自动调整高度，无需手动滚动
- 自动根据视频总帧数创建帧块
- 支持单选模式
- 响应式布局：窗口大小改变时自动重新排列

### 3. 交互功能
- ✅ 点击帧块：暂停视频并跳转到对应帧
- ✅ 自动同步：视频播放时自动更新当前帧的高亮状态
- ✅ 进度条联动：拖动进度条时帧选择器同步更新
- ✅ 播放/暂停按钮：修复了状态同步问题，现在可以正常暂停

## 技术实现 / Technical Implementation

### 依赖 / Dependencies
```python
import cv2  # OpenCV for frame extraction
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QWidget, QScrollArea
```

### 关键方法 / Key Methods

#### MediaPreviewWidget
- `_load_video_frames(video_path)`: 使用 OpenCV 加载视频帧信息
- `_on_frame_selected(frame_index)`: 处理帧选择事件，暂停并跳转
- `_on_position_changed(position)`: 更新帧选择器的当前帧显示

#### FrameSelectorWidget
- `load_frames(total_frames)`: 根据总帧数创建帧块
- `clear_frames()`: 清除所有帧块
- `update_current_frame(frame_index)`: 更新当前帧高亮（不触发选择事件）

## 使用方法 / Usage

### 基本使用
```python
from app.ui.preview.preview import MediaPreviewWidget

# 创建预览组件
preview_widget = MediaPreviewWidget(workspace)

# 加载视频文件
preview_widget.switch_file("path/to/video.mp4")

# 帧选择器会自动显示在视频下方
```

### 测试
```bash
# 运行测试脚本
python test/test_frame_selector.py
```

## 视觉设计 / Visual Design

### 单行显示（帧数较少时）
```
┌─────────────────────────────────────────┐
│         Video Preview Area              │
│                                         │
│      [Video playback display]           │
│                                         │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ [▶] ▪▪▪▪▪▪■▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪  │
│       ↑ current/selected frame          │
└─────────────────────────────────────────┘
```

### 多行显示（帧数超出宽度时自动换行）
```
┌─────────────────────────────────────────┐
│         Video Preview Area              │
│                                         │
│      [Video playback display]           │
│                                         │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ [▶] Frame Selector (wrapped)          │
│     ▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪  │
│     ▪▪▪▪▪■▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪  │
│     ▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪  │
│       ↑ current/selected                │
└─────────────────────────────────────────┘
```

## 注意事项 / Notes

1. **自动换行**：帧选择器会根据容器宽度自动计算每行可容纳的帧数并换行显示
2. **自适应高度**：高度根据实际换行后的行数自动调整，最小30px，无上限
3. **性能优化**：对于帧数非常多的长视频（>1000帧），布局计算可能需要优化
4. **依赖项**：确保已安装 `opencv-python`：
   ```bash
   pip install opencv-python
   ```
5. **内存管理**：帧块会在切换视频或清除显示时自动释放
6. **响应式设计**：窗口大小改变时自动重新排列帧块并调整高度
7. **播放控制**：修复了播放/暂停按钮的状态同步问题

## 更新日志 / Changelog

### v2.2 (Current) - 自适应高度
- ✅ **高度自适应**：帧选择器高度根据换行后的实际行数自动调整
- ✅ **移除滚动条**：不再需要垂直滚动，所有帧块完全可见
- ✅ **更好的可见性**：长视频的所有帧都能直接看到，无需滚动
- ✅ **动态调整**：窗口宽度改变时自动重新计算行数和高度

### v2.1 - UI布局优化
- ✅ **布局改进**：Play/Pause按钮和帧选择器采用左右布局
- ✅ **空间优化**：帧选择器占据更多横向空间，更好地展示帧序列
- ✅ **交互优化**：按钮和时间轴在同一行，更符合直觉

### v2.0 - 重大更新
- ✅ **重大改变**：帧选择器完全替代进度条，成为主要时间轴控制
- ✅ **简化UI**：移除传统滑块，采用更直观的帧级可视化
- ✅ **优化布局**：播放/暂停按钮居中显示，界面更简洁
- ✅ **精确控制**：每一帧都可单独选择，提供帧级精度

### v1.1
- ✅ **新增**：帧选择器支持自动换行
- ✅ **修复**：播放/暂停按钮状态同步问题
- ✅ **优化**：响应式布局，窗口大小改变时自动重新排列
- ✅ **改进**：高度范围从固定30px改为30-100px可变

### v1.0
- ✅ 基础帧选择器功能
- ✅ 单选模式
- ✅ 与播放器同步

## 未来改进 / Future Improvements

- [ ] 添加帧缩略图预览（鼠标悬停时显示）
- [ ] 支持关键帧标记
- [ ] 支持范围选择（多帧选择）
- [ ] 性能优化：超长视频帧采样显示
- [ ] 添加帧数/时间标签显示
- [ ] 虚拟化滚动（仅渲染可见帧块）
