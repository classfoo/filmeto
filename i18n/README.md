# Filmeto 国际化 (i18n) 使用指南

## 概述

Filmeto 使用 PySide6 的 Qt 国际化机制来支持多语言。目前支持：
- **中文 (zh_CN)** - 默认语言
- **English (en_US)** - 英文

## 文件结构

```
filmeto/
├── i18n/                           # 翻译文件目录
│   ├── filmeto_en_US.ts           # 英文翻译源文件 (XML格式)
│   └── filmeto_en_US.qm           # 编译后的翻译文件 (二进制)
├── utils/
│   └── i18n_utils.py              # 国际化工具类
└── app/
    └── ui/                         # UI组件
        ├── main_window.py         # 包含语言切换按钮
        ├── preview.py             # 使用翻译函数
        ├── timeline.py            # 使用翻译函数
        └── ...
```

## 如何使用翻译

### 1. 在代码中使用翻译

导入翻译函数：
```python
from utils.i18n_utils import tr
```

使用 `tr()` 函数包裹需要翻译的字符串：
```python
# 之前
button = QPushButton("播放")

# 之后
button = QPushButton(tr("▶ 播放"))
```

### 2. 添加新的翻译

#### 步骤 1: 在代码中使用 `tr()` 包裹字符串
```python
label = QLabel(tr("新功能"))
```

#### 步骤 2: 更新翻译文件
编辑 `i18n/filmeto_en_US.ts`，添加新的翻译条目：
```xml
<message>
    <source>新功能</source>
    <translation>New Feature</translation>
</message>
```

#### 步骤 3: 编译翻译文件
```bash
cd /Users/classfoo/ai/filmeto
pyside6-lrelease i18n/filmeto_en_US.ts -qm i18n/filmeto_en_US.qm
```

### 3. 语言切换

用户可以通过顶部工具栏的 🌐 按钮切换语言：
1. 点击 🌐 按钮
2. 在下拉菜单中选择语言（中文 或 English）
3. 应用会立即切换到选定的语言

## 翻译管理器 API

### TranslationManager

```python
from utils.i18n_utils import translation_manager

# 获取可用语言
languages = translation_manager.get_available_languages()
# 返回: {"zh_CN": "中文", "en_US": "English"}

# 获取当前语言
current = translation_manager.get_current_language()
# 返回: "zh_CN" 或 "en_US"

# 切换语言
translation_manager.switch_language("en_US")

# 获取语言显示名称
name = translation_manager.get_language_name("en_US")
# 返回: "English"
```

## 已翻译的组件

### 主窗口 (MainWindow)
- 顶部工具栏
- 语言切换按钮
- 导出按钮

### 时间线 (Timeline)
- 窗口标题
- "Add Card" 按钮

### 预览组件 (Preview)
- 播放/暂停按钮
- 比例选择下拉框
- 状态提示文本
- 加载提示

### 任务列表 (Task List)
- 刷新按钮

## 工具函数

### `tr(text: str) -> str`
主要的翻译函数，根据当前语言返回翻译后的文本。

**示例：**
```python
from utils.i18n_utils import tr

# 中文环境下
tr("播放")  # 返回: "播放"

# 英文环境下  
tr("播放")  # 返回: "Play"
```

## 添加新语言

如果需要添加其他语言（如日语、法语等）：

1. 创建新的 TS 文件：
```bash
cp i18n/filmeto_en_US.ts i18n/filmeto_ja_JP.ts
```

2. 编辑新文件，修改语言代码和翻译内容

3. 在 `utils/i18n_utils.py` 中添加语言：
```python
self.available_languages = {
    "zh_CN": "中文",
    "en_US": "English",
    "ja_JP": "日本語"  # 新增
}
```

4. 编译翻译文件：
```bash
pyside6-lrelease i18n/filmeto_ja_JP.ts -qm i18n/filmeto_ja_JP.qm
```

## 注意事项

1. **中文为源语言**：所有 `tr()` 函数中的字符串应使用中文
2. **即时生效**：语言切换后会立即应用，但某些动态创建的UI元素可能需要重新创建
3. **编译必需**：修改 `.ts` 文件后必须重新编译为 `.qm` 文件才能生效
4. **字符串一致性**：确保 `tr()` 中的字符串与 `.ts` 文件中的 `<source>` 标签完全一致

## 自动提取翻译字符串

可以使用 Qt 的 lupdate 工具自动扫描代码并生成翻译文件：

```bash
pyside6-lupdate app/ -ts i18n/filmeto_en_US.ts
```

但需要注意，这会覆盖现有的 `.ts` 文件，建议手动管理翻译条目。

## 调试

查看当前语言和翻译状态：
```python
from utils.i18n_utils import translation_manager

print(f"Current language: {translation_manager.get_current_language()}")
print(f"Available languages: {translation_manager.get_available_languages()}")
```

## 示例

完整示例：创建一个支持国际化的对话框

```python
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from utils.i18n_utils import tr

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("我的对话框"))
        
        layout = QVBoxLayout(self)
        
        label = QLabel(tr("欢迎使用 Filmeto！"))
        layout.addWidget(label)
        
        ok_button = QPushButton(tr("确定"))
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        cancel_button = QPushButton(tr("取消"))
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
```

对应的翻译文件条目：
```xml
<message>
    <source>我的对话框</source>
    <translation>My Dialog</translation>
</message>
<message>
    <source>欢迎使用 Filmeto！</source>
    <translation>Welcome to Filmeto!</translation>
</message>
<message>
    <source>确定</source>
    <translation>OK</translation>
</message>
<message>
    <source>取消</source>
    <translation>Cancel</translation>
</message>
```
