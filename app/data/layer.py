import os
from enum import Enum
from typing import Optional, Callable, List, Tuple
from blinker import signal
import cv2
import numpy as np
import shutil

class LayerType(Enum):
    IMAGE = ("image", "\uE6BC")  # 图片生成图标
    VIDEO = ("video", "\uE6BD")  # 视频图标
    GRAPHIC = ("graphic", "\uE61A")  # 调色板图标
    AUDIO = ("audio", "\uE73B")  # 音频相关图标
    SUBTITLE = ("subtitle", "\uE647")  # 文字图标

    def __init__(self, value: str, icon: str):
        self._value_ = value
        self.icon = icon

    @property
    def value(self) -> str:
        return self._value_


class Layer:

    def __init__(self, layer_id: int, name: str = "", layer_type: LayerType = LayerType.IMAGE,
                 visible: bool = True, locked: bool = False, x: int = 0, y: int = 0, width: int = 0, height: int = 0, 
                 timeline_item = None):
        self.id = layer_id
        self.name = name if name else f"图层-{layer_id}"
        self.type = layer_type
        self.visible = visible
        self.locked = locked
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.timeline_item = timeline_item
        # 修复：检查timeline_item是否为None，避免AttributeError
        self.layers_path = self.timeline_item.get_layers_path() if self.timeline_item else None

    def get_layer_path(self) -> str:
        # 修复：检查layers_path是否存在
        if not self.layers_path:
            return None
        if self.type==LayerType.IMAGE:
            return os.path.join(self.layers_path, f"{self.id}.png")
        if self.type==LayerType.VIDEO:
            return os.path.join(self.layers_path, f"{self.id}.mp4")
        return None

    def to_dict(self):
        """
        将图层对象转换为字典格式，用于保存到配置文件
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "visible": self.visible,
            "locked": self.locked,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }

    @classmethod
    def from_dict(cls, data: dict, timeline_item):
        """
        从字典数据创建图层对象
        """
        layer_id = data.get("id", 0)
        name = data.get("name", "")
        # 通过值查找对应的枚举项
        layer_type_value = data.get("type", LayerType.IMAGE.value)
        layer_type = next((t for t in LayerType if t.value == layer_type_value), LayerType.IMAGE)
        visible = data.get("visible", True)
        locked = data.get("locked", False)
        x = data.get("x", 0)
        y = data.get("y", 0)
        width = data.get("width", 0)
        height = data.get("height", 0)
        return cls(layer_id, name, layer_type, visible, locked, x, y, width, height, timeline_item)


class LayerManager:

    layer_changed = signal('layer_changed')

    def __init__(self):
        self.layers = None
        self.timeline_item = None

    def load_layers(self, timeline_item):
        self.timeline_item = timeline_item
        print(f"Loading layers for timeline item: {timeline_item.index if timeline_item else 'None'}")
        layers_data = timeline_item.get_config_value("layers") or []
        # 使用字典存储图层，以图层ID为键
        self.layers = {layer_data["id"]: Layer.from_dict(layer_data, timeline_item) for layer_data in layers_data}
        print(f"Loaded {len(self.layers)} layers")

    def connect_layer_changed(self, func):
        self.layer_changed.connect(func)

    def _save_layers(self):
        # 按图层ID排序，确保保存顺序一致
        layers_data = [self.layers[layer_id].to_dict() for layer_id in sorted(self.layers.keys())]
        self.timeline_item.set_config_value("layers", layers_data)

    def add_layer(self, layer_type: LayerType = LayerType.IMAGE) -> Layer:
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
        
        # 生成新的图层ID（基于现有最大ID+1，避免删除后的ID冲突）
        if self.layers:
            existing_ids = list(self.layers.keys())
            new_id = max(existing_ids) + 1
        else:
            new_id = 1
        layers_path = self.timeline_item.layers_path

        # 创建图层对应的文件
        if layer_type == LayerType.VIDEO:
            # 视频图层创建mp4文件
            layer = Layer(new_id, f"Layer-{new_id}", layer_type, True, False, 0, 0, 720, 1280, self.timeline_item)
            # Create a minimal placeholder mp4 file
            # For now, we'll create a placeholder file with zeros
            with open(layer.get_layer_path(), 'wb') as f:
                f.write(b'\x00' * 1024)  # Write 1KB of zeros as a minimal placeholder
        else:
            # 其他图层类型创建png文件
            layer_file_path = os.path.join(layers_path, f"{new_id}.png")
            layer = Layer(new_id, f"Layer-{new_id}", layer_type, True, False,0,0,720,1280,self.timeline_item)
            # Create a placeholder png file with 720x1280 dimensions
            img = np.zeros((1280, 720, 4), dtype=np.uint8)  # 720x1280 with alpha
            img[:, :] = [0, 0, 0, 0]  # Transparent black
            cv2.imwrite(layer_file_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            
            # 设置图层的默认尺寸
            layer.width = 720
            layer.height = 1280
        
        return self._add_layer(layer)

    def add_layer_from_file(self, source_path: str, layer_type: LayerType = LayerType.IMAGE) -> Layer:
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
        
        # 生成新的图层ID（基于现有最大ID+1，避免删除后的ID冲突）
        if self.layers:
            existing_ids = list(self.layers.keys())
            new_id = max(existing_ids) + 1
        else:
            new_id = 1

        # 获取源文件扩展名
        ext = os.path.splitext(source_path)[1] or ".png"
        layer_file_path = os.path.join(self.timeline_item.layers_path, f"{new_id}{ext}")

        # 复制源文件到layers目录
        shutil.copy2(source_path, layer_file_path)

        # 创建图层对象
        layer = Layer(new_id, f"Layer-{new_id}", layer_type, True, False, 0, 0, 0, 0, self.timeline_item)

        # 获取图片尺寸
        if layer_type == LayerType.IMAGE:
            try:
                img = cv2.imread(source_path)
                if img is not None:
                    height, width = img.shape[:2]
                    layer.width = width
                    layer.height = height
                else:
                    layer.width, layer.height = 720, 1280  # 默认尺寸
            except Exception as e:
                print(f"Error reading image dimensions: {e}")
                layer.width, layer.height = 720, 1280  # 默认尺寸
        else:
            # 对于非图片类型，使用默认尺寸
            layer.width, layer.height = 720, 1280  # 默认尺寸

        return self._add_layer(layer)

    def _add_layer(self, layer: Layer) -> Layer:
        # 使用字典存储图层
        self.layers[layer.id] = layer
        self._save_layers()
        # Emit the general layer_changed signal only if the current timeline_item 
        # in this layer manager is the currently selected timeline_item
        if self.timeline_item and self.timeline_item.index == self.timeline_item.timeline.get_current_item().index:
            self.layer_changed.send(self, layer=layer, change_type='added')
        return layer

    def remove_layer(self, layer_id: int) -> bool:
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
        
        # 直接通过ID访问图层
        if layer_id in self.layers:
            layer = self.layers[layer_id]
            # 先删除对应的文件
            layers_path = self.timeline_item.layers_path
            # Find all files that start with the layer ID followed by a dot (e.g., "1.png", "1.mp4", etc.)
            layer_files = []
            if os.path.exists(layers_path):
                for file_name in os.listdir(layers_path):
                    if file_name.startswith(f"{layer_id}."):
                        layer_files.append(os.path.join(layers_path, file_name))
            
            # Remove the found files
            for file_path in layer_files:
                try:
                    os.remove(file_path)
                    print(f"Deleted layer file: {file_path}")
                except OSError as e:
                    print(f"Error deleting layer file {file_path}: {e}")
            
            # 从内存和配置中删除图层
            del self.layers[layer_id]
            self._save_layers()

            # Emit the general layer_changed signal only if the current timeline_item 
            # in this layer manager is the currently selected timeline_item
            if self.timeline_item.index == self.timeline_item.timeline.get_current_item().index:
                self.layer_changed.send(self, layer=layer, change_type='removed')
            
            return True
        return False

    def toggle_visibility(self, layer_id: int) -> Optional[bool]:
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
        
        # 直接通过ID访问图层
        if layer_id in self.layers:
            layer = self.layers[layer_id]
            layer.visible = not layer.visible
            self._save_layers()
            # Emit the general layer_changed signal only if the current timeline_item 
            # in this layer manager is the currently selected timeline_item
            if self.timeline_item.index == self.timeline_item.timeline.get_current_item().index:
                self.layer_changed.send(self, layer=layer, change_type='modified')
            
            return layer.visible
        return None

    def toggle_lock(self, layer_id: int) -> Optional[bool]:
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
        
        # 直接通过ID访问图层
        if layer_id in self.layers:
            layer = self.layers[layer_id]
            layer.locked = not layer.locked
            self._save_layers()
            # Emit the general layer_changed signal only if the current timeline_item 
            # in this layer manager is the currently selected timeline_item
            if self.timeline_item.index == self.timeline_item.timeline.get_current_item().index:
                self.layer_changed.send(self, layer=layer, change_type='modified')
            
            return layer.locked
        return None

    def rename_layer(self, layer_id: int, new_name: str) -> bool:
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
        
        # 直接通过ID访问图层
        if layer_id in self.layers:
            layer = self.layers[layer_id]
            layer.name = new_name
            self._save_layers()
            # Emit the general layer_changed signal only if the current timeline_item 
            # in this layer manager is the currently selected timeline_item
            if self.timeline_item.index == self.timeline_item.timeline.get_current_item().index:
                self.layer_changed.send(self, layer=layer, change_type='modified')
            
            return True
        return False

    def move_layer(self, layer_id: int, new_position: int) -> bool:
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
        
        # 获取按ID排序的图层列表
        sorted_layer_ids = sorted(self.layers.keys())
        if new_position < 0 or new_position >= len(sorted_layer_ids):
            return False

        # 找到要移动的图层
        if layer_id not in self.layers:
            return False

        # 移动图层（在保存时调整顺序）
        self._save_layers()
        # Emit the general layer_changed signal only if the current timeline_item 
        # in this layer manager is the currently selected timeline_item
        if self.timeline_item.index == self.timeline_item.timeline.get_current_item().index:
            layer_obj = self.layers[layer_id]
            self.layer_changed.send(self, layer=layer_obj, change_type='reordered')
        
        return True

    def get_layer(self, layer_id: int) -> Optional[Layer]:
        # 直接通过ID访问图层
        return self.layers.get(layer_id)

    def get_layers(self):
        # 按ID排序返回图层列表
        result = [self.layers[layer_id] for layer_id in sorted(self.layers.keys())] if self.layers is not None else []
        return result

    def get_visible_layers(self):
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
            
        if not self.layers:
            return []
        
        # 按图层ID排序
        sorted_layers = [self.layers[layer_id] for layer_id in sorted(self.layers.keys())]
        
        # 用于跟踪未被完全覆盖的图层
        visible_layers = []
        
        # 从下到上处理每个图层
        for i, layer in enumerate(sorted_layers):
            # 跳过不可见图层
            if not layer.visible:
                continue
                
            # 检查图层是否有效（有尺寸）
            if layer.width <= 0 or layer.height <= 0:
                visible_layers.append(layer)
                continue
                
            # 检查当前图层是否被上面的图层完全覆盖
            is_fully_covered = False
            
            # 检查上方所有可见图层
            for j in range(i + 1, len(sorted_layers)):
                upper_layer = sorted_layers[j]
                # 只考虑可见且有尺寸的图层
                if not upper_layer.visible or upper_layer.width <= 0 or upper_layer.height <= 0:
                    continue
                    
                # 检查当前图层是否完全在上层图层内
                if (layer.x >= upper_layer.x and 
                    layer.y >= upper_layer.y and
                    layer.x + layer.width <= upper_layer.x + upper_layer.width and
                    layer.y + layer.height <= upper_layer.y + upper_layer.height):
                    is_fully_covered = True
                    break
            
            # 如果没有被完全覆盖，则添加到可见图层列表
            if not is_fully_covered:
                visible_layers.append(layer)
        
        return visible_layers

    def generate_visible_file(self, output_path, canvas_size=(1920, 1080)):
        # 检查timeline_item是否已加载
        if self.timeline_item is None:
            raise ValueError("LayerManager has not loaded timeline_item yet. Call load_layers() first.")
            
        # 获取可见图层列表
        visible_layers = self.get_visible_layers()
        
        # 构造图层和图像路径的元组列表
        layer_path_tuples = []
        layers_path = self.timeline_item.layers_path
        
        for layer in visible_layers:
            # 查找对应图层的文件
            layer_files = [f for f in os.listdir(layers_path) if f.startswith(f"{layer.id}.")]
            if layer_files:
                image_path = os.path.join(layers_path, layer_files[0])
                layer_path_tuples.append((layer, image_path))
        
        # 使用图像工具合成可见图层
        self.composite_visible_layers(layer_path_tuples, output_path, canvas_size)
        
        return output_path


    def composite_visible_layers(self, layer_image_paths: List[Tuple[Layer, str]], output_path: str,
                                 canvas_size: Tuple[int, int] = (1920, 1080)):
        """
        将多个可见图层的图片绘制到一个图片文件中

        Args:
            layer_image_paths: 包含图层和图像路径的元组列表 [(layer, image_path), ...]
            output_path: 输出图像文件路径
            canvas_size: 画布尺寸 (width, height)
        """
        # 创建一个黑色背景的画布
        canvas = np.zeros((canvas_size[1], canvas_size[0], 3), dtype=np.uint8)

        # 按照图层顺序从下到上绘制图层
        for layer, image_path in layer_image_paths:
            if not os.path.exists(image_path):
                continue

            # 跳过不可见图层
            if not layer.visible:
                continue

            # 读取图层图像
            layer_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if layer_image is None:
                continue

            # 如果图像有alpha通道，使用透明度混合
            if len(layer_image.shape) == 3 and layer_image.shape[2] == 4:
                # 分离RGBA通道
                b, g, r, a = cv2.split(layer_image)
                layer_image_rgb = cv2.merge([b, g, r])
                alpha = a.astype(float) / 255.0

                # 调整图层图像大小以匹配图层指定的尺寸
                if layer.width > 0 and layer.height > 0:
                    layer_image_rgb = cv2.resize(layer_image_rgb, (layer.width, layer.height))
                    alpha = cv2.resize(alpha, (layer.width, layer.height))
                else:
                    layer.height, layer.width = layer_image_rgb.shape[:2]

                # 确保图层在画布范围内
                if (0 <= layer.x < canvas_size[0] and 0 <= layer.y < canvas_size[1] and
                        layer.x + layer.width <= canvas_size[0] and layer.y + layer.height <= canvas_size[1] and
                        layer.width > 0 and layer.height > 0):

                    # 提取画布上对应区域
                    canvas_region = canvas[layer.y:layer.y + layer.height, layer.x:layer.x + layer.width]

                    # 应用alpha混合
                    for c in range(3):
                        canvas_region[:, :, c] = (1 - alpha) * canvas_region[:, :, c] + alpha * layer_image_rgb[:, :, c]
            else:
                # 处理没有alpha通道的图像
                # 调整图层图像大小以匹配图层指定的尺寸
                if layer.width > 0 and layer.height > 0:
                    layer_image = cv2.resize(layer_image, (layer.width, layer.height))
                else:
                    if len(layer_image.shape) == 3:
                        layer.height, layer.width = layer_image.shape[:2]
                    else:
                        layer.height, layer.width = layer_image.shape[0], layer_image.shape[1]

                # 确保图层在画布范围内
                if (0 <= layer.x < canvas_size[0] and 0 <= layer.y < canvas_size[1] and
                        layer.x + layer.width <= canvas_size[0] and layer.y + layer.height <= canvas_size[1] and
                        layer.width > 0 and layer.height > 0):
                    # 直接复制图像到画布指定位置
                    canvas[layer.y:layer.y + layer.height, layer.x:layer.x + layer.width] = layer_image

        # 保存最终合成的图像
        cv2.imwrite(output_path, canvas)