# Character Management System

## Overview

角色管理系统提供了完整的角色数据管理功能，包括角色的基本信息、资源文件和关系网的管理。

## Architecture

### Data Layer (`app/data/character.py`)

#### Character Class
表示单个角色，包含：
- 基本信息：名称、描述、故事
- 关系网：与其他角色的关系
- 资源文件：主视图、前视图、后视图、左视图、右视图、姿势图、服装图等
- 元数据：创建时间、更新时间等

#### CharacterManager Class
管理项目中的所有角色，提供：
- 创建角色 (`create_character`)
- 获取角色 (`get_character`)
- 列出所有角色 (`list_characters`)
- 更新角色 (`update_character`)
- 删除角色 (`delete_character`)
- 添加资源 (`add_resource`)
- 移除资源 (`remove_resource`)
- 重命名角色 (`rename_character`)
- 搜索角色 (`search_characters`)

### UI Layer

#### CharacterPanel (`app/ui/characters/character_panel.py`)
角色管理面板，提供：
- 角色列表显示
- 新建角色按钮
- 右键菜单（编辑、删除）
- 角色选择信号

#### CharacterEditDialog (`app/ui/characters/character_edit_dialog.py`)
角色编辑对话框，提供：
- 基本信息编辑（名称、描述、故事）
- 资源文件管理（各种视图图片）
- 关系网编辑
- 保存/取消功能

## Directory Structure

角色数据按项目组织，存储在项目目录下的 `characters` 目录：

```
project/
  characters/
    CharacterName1/
      config.yml          # 角色配置文件
      resources/           # 资源文件目录
        main_view.png
        front_view.png
        ...
    CharacterName2/
      config.yml
      resources/
        ...
```

## Usage

### 在代码中使用 CharacterManager

```python
from app.data.character import CharacterManager

# 初始化管理器
project_path = "/path/to/project"
manager = CharacterManager(project_path)

# 创建角色
character = manager.create_character(
    name="Alice",
    description="A friendly actor",
    story="Alice is a brave adventurer..."
)

# 添加资源文件
image_path = "/path/to/image.png"
manager.add_resource("Alice", "main_view", image_path)

# 更新角色信息
manager.update_character(
    "Alice",
    description="Updated description",
    story="Updated story",
    relationships={"Bob": "Friend", "Charlie": "Enemy"}
)

# 搜索角色
results = manager.search_characters("Alice")

# 删除角色
manager.delete_character("Alice", remove_files=True)
```

### 在UI中使用 CharacterPanel

```python
from app.ui.characters import CharacterPanel
from app.data.workspace import Workspace

# 创建面板
workspace = Workspace(workspace_path, project_name)
panel = CharacterPanel(workspace, parent_widget)

# 连接信号
panel.character_selected.connect(on_character_selected)

# 添加到布局
layout.addWidget(panel)
```

## Character Config YAML Structure

```yaml
character_id: "uuid-string"
name: "CharacterName"
description: "Character description"
story: "Character background story"
relationships:
  OtherCharacter1: "Relationship description 1"
  OtherCharacter2: "Relationship description 2"
resources:
  main_view: "characters/CharacterName/resources/main_view.png"
  front_view: "characters/CharacterName/resources/front_view.png"
  back_view: "characters/CharacterName/resources/back_view.png"
  left_view: "characters/CharacterName/resources/left_view.png"
  right_view: "characters/CharacterName/resources/right_view.png"
  pose: "characters/CharacterName/resources/pose.png"
  costume: "characters/CharacterName/resources/costume.png"
metadata: {}
created_at: "2024-01-01T00:00:00"
updated_at: "2024-01-01T00:00:00"
```

## Resource Types

支持的角色资源类型：
- `main_view`: 主视图
- `front_view`: 前视图
- `back_view`: 后视图
- `left_view`: 左视图
- `right_view`: 右视图
- `pose`: 姿势图
- `costume`: 服装图
- `other`: 其他

## Integration with Project

CharacterManager 已集成到 Project 类中：

```python
from app.data.project import Project

project = Project(workspace, project_path, project_name)
character_manager = project.get_character_manager()

# 使用角色管理器
character = character_manager.create_character("NewCharacter")
```

## Testing

运行单元测试：

```bash
python3 -m unittest tests.test_character_manager -v
```

测试覆盖：
- Character 类的初始化和序列化
- CharacterManager 的 CRUD 操作
- 资源文件管理
- 角色重命名
- 搜索功能
- 边界情况和错误处理

## Signals

CharacterManager 提供以下信号：
- `character_added`: 角色创建时触发
- `character_updated`: 角色更新时触发
- `character_deleted`: 角色删除时触发

使用示例：

```python
from blinker import signal

def on_character_added(character):
    print(f"Character added: {character.name}")

manager.character_added.connect(on_character_added)
```

## Error Handling

所有操作都会进行错误检查：
- 创建角色时检查名称是否为空或重复
- 更新/删除时检查角色是否存在
- 添加资源时检查文件是否存在
- 重命名时检查新名称是否已存在

操作失败时返回 `None` 或 `False`，并打印错误信息。

## Future Enhancements

可能的增强功能：
1. 角色模板系统
2. 批量导入/导出
3. 角色关系可视化
4. 更多资源类型支持
5. 角色版本管理
6. 角色标签系统

