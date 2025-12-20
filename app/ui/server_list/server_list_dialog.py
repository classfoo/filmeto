"""
Server List Dialog

A dialog for displaying and managing servers.
Provides a list view with server details and management actions.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QWidget, QMessageBox, QInputDialog,
    QTextEdit, QComboBox, QLineEdit, QFormLayout, QCheckBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QAction

from app.ui.base_widget import BaseWidget
from app.ui.dialog.custom_dialog import CustomDialog
from app.ui.server_list.server_config_dialog import ServerConfigDialog
from utils.i18n_utils import tr


class ServerItemWidget(QWidget):
    """
    Custom widget for displaying server information in list.
    """
    
    # Signals
    enable_clicked = Signal(str, bool)  # server_name, new_enabled_state
    edit_clicked = Signal(str)  # server_name
    delete_clicked = Signal(str)  # server_name
    
    def __init__(self, server, parent=None):
        super().__init__(parent)
        self.server = server
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Status indicator (colored circle)
        self.status_indicator = QLabel("●", self)
        self.status_indicator.setFixedSize(16, 16)
        status_font = QFont("Arial", 14, QFont.Bold)
        self.status_indicator.setFont(status_font)
        
        if server.is_enabled:
            self.status_indicator.setStyleSheet("color: #4CAF50;")  # Green
        else:
            self.status_indicator.setStyleSheet("color: #F44336;")  # Red
        
        layout.addWidget(self.status_indicator)
        
        # Server info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Name and type
        name_label = QLabel(f"{server.name} ({server.server_type})", self)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(11)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #E1E1E1;")
        info_layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(server.config.description or tr("无描述"), self)
        desc_label.setStyleSheet("color: #999999; font-size: 10px;")
        info_layout.addWidget(desc_label)

        # Plugin name
        plugin_label = QLabel(f"{tr('插件')}: {server.config.plugin_name}", self)
        plugin_label.setStyleSheet("color: #888888; font-size: 9px;")
        info_layout.addWidget(plugin_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        # Enable/Disable toggle button
        self.toggle_button = QPushButton(tr("禁用") if server.is_enabled else tr("启用"), self)
        self.toggle_button.setFixedSize(60, 28)
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        self._style_button(self.toggle_button, "#FF9800" if server.is_enabled else "#4CAF50")
        button_layout.addWidget(self.toggle_button)

        # Edit button
        self.edit_button = QPushButton(tr("编辑"), self)
        self.edit_button.setFixedSize(50, 28)
        self.edit_button.clicked.connect(lambda: self.edit_clicked.emit(server.name))
        self._style_button(self.edit_button, "#2196F3")
        button_layout.addWidget(self.edit_button)

        # Delete button (disabled for default servers)
        self.delete_button = QPushButton(tr("删除"), self)
        self.delete_button.setFixedSize(50, 28)
        self.delete_button.clicked.connect(lambda: self.delete_clicked.emit(server.name))
        
        if server.name in ["local", "filmeto"]:
            self.delete_button.setEnabled(False)
            self._style_button(self.delete_button, "#555555")
        else:
            self._style_button(self.delete_button, "#F44336")
        
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
    
    def _style_button(self, button: QPushButton, color: str):
        """Apply consistent button styling"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """)
    
    def _lighten_color(self, color: str) -> str:
        """Lighten a hex color"""
        # Simple lightening by adjusting RGB values
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = min(255, r + 20)
        g = min(255, g + 20)
        b = min(255, b + 20)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _darken_color(self, color: str) -> str:
        """Darken a hex color"""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = max(0, r - 20)
        g = max(0, g - 20)
        b = max(0, b - 20)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_toggle_clicked(self):
        """Handle toggle button click"""
        new_state = not self.server.is_enabled
        self.enable_clicked.emit(self.server.name, new_state)


class ServerListDialog(CustomDialog):
    """
    Dialog for displaying and managing servers.
    """

    # Signal emitted when servers are modified
    servers_modified = Signal()

    def __init__(self, workspace, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.server_manager = None

        # Setup dialog
        self.set_title(tr("服务器管理"))
        self.setMinimumSize(700, 500)

        # Initialize UI
        self._init_ui()

        # Load servers
        self._load_servers()
    
    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        # Note: Content margins are handled by CustomDialog, so we don't set them here

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel(tr("服务器列表"), self)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        # Apply specific styling to ensure visibility against CustomDialog background
        title_label.setStyleSheet("QLabel { color: #E1E1E1; }")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        refresh_button = QPushButton("\ue6b8 " + tr("刷新"), self)
        refresh_button.clicked.connect(self._load_servers)
        # Apply specific styling for consistency
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3f41;
                color: #E1E1E1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4c5052;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #2c2f31;
            }
        """)
        header_layout.addWidget(refresh_button)

        # Add server button
        add_button = QPushButton("\ue697 " + tr("添加服务器"), self)
        add_button.clicked.connect(self._on_add_server)
        # Apply specific styling for consistency
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3f41;
                color: #E1E1E1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4c5052;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #2c2f31;
            }
        """)
        header_layout.addWidget(add_button)

        layout.addLayout(header_layout)

        # Server list
        self.server_list = QListWidget(self)
        self.server_list.setSelectionMode(QListWidget.NoSelection)
        # Apply specific styling to avoid conflicts with CustomDialog
        self.server_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                color: #E1E1E1;
            }
            QListWidget::item {
                border-bottom: 1px solid #3c3c3c;
                padding: 4px;
            }
            QListWidget::item:hover {
                background-color: #323232;
            }
            QListWidget::item:selected {
                background-color: #404040;
            }
        """)
        layout.addWidget(self.server_list)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel(self)
        # Apply specific styling to ensure visibility against CustomDialog background
        self.status_label.setStyleSheet("QLabel { color: #888888; font-size: 11px; }")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Close button
        close_button = QPushButton(tr("关闭"), self)
        close_button.setFixedWidth(100)
        close_button.clicked.connect(self.reject)  # Use reject() for CustomDialog
        # Apply specific styling for consistency
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3f41;
                color: #E1E1E1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4c5052;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #2c2f31;
            }
        """)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

        # Set the layout to the custom dialog's content area
        self.setContentLayout(layout)
    
    def _load_servers(self):
        """Load servers from ServerManager"""
        try:
            # Import here to avoid circular dependency
            from server.server import ServerManager
            import os
            
            # Get workspace path
            workspace_path = self.workspace.workspace_path
            
            # Create server manager
            self.server_manager = ServerManager(workspace_path)
            
            # Clear existing items
            self.server_list.clear()
            
            # Get servers
            servers = self.server_manager.list_servers()
            
            if not servers:
                # Show empty state
                item = QListWidgetItem(self.server_list)
                empty_widget = QLabel(tr("暂无服务器配置"), self)
                empty_widget.setAlignment(Qt.AlignCenter)
                # Apply specific styling to ensure visibility against CustomDialog background
                empty_widget.setStyleSheet("QLabel { color: #666666; padding: 40px; }")
                item.setSizeHint(empty_widget.sizeHint())
                self.server_list.addItem(item)
                self.server_list.setItemWidget(item, empty_widget)
            else:
                # Add server items
                for server in servers:
                    item = QListWidgetItem(self.server_list)
                    server_widget = ServerItemWidget(server, self)
                    
                    # Connect signals
                    server_widget.enable_clicked.connect(self._on_toggle_server)
                    server_widget.edit_clicked.connect(self._on_edit_server)
                    server_widget.delete_clicked.connect(self._on_delete_server)
                    
                    item.setSizeHint(server_widget.sizeHint())
                    self.server_list.addItem(item)
                    self.server_list.setItemWidget(item, server_widget)
            
            # Update status
            active_count = sum(1 for s in servers if s.is_enabled)
            inactive_count = sum(1 for s in servers if not s.is_enabled)
            self.status_label.setText(
                f"{tr('总计')}: {len(servers)} | "
                f"{tr('活跃')}: {active_count} | "
                f"{tr('禁用')}: {inactive_count}"
            )
            
        except Exception as e:
            print(f"Failed to load servers: {e}")
            QMessageBox.critical(self, tr("错误"), f"{tr('加载服务器失败')}: {str(e)}")
    
    def _on_toggle_server(self, server_name: str, enabled: bool):
        """Handle server enable/disable toggle"""
        try:
            server = self.server_manager.get_server(server_name)
            if server:
                # Update config
                server.config.enabled = enabled
                self.server_manager.update_server(server_name, server.config)
                
                # Reload list
                self._load_servers()
                self.servers_modified.emit()
                
        except Exception as e:
            QMessageBox.critical(self, tr("错误"), f"{tr('更新服务器失败')}: {str(e)}")
    
    def _on_edit_server(self, server_name: str):
        """Handle edit server"""
        try:
            server = self.server_manager.get_server(server_name)
            if not server:
                QMessageBox.warning(self, tr("错误"), f"{tr('服务器未找到')}: {server_name}")
                return

            # Get plugin info
            plugin_info = server.get_plugin_info()
            if not plugin_info:
                QMessageBox.warning(
                    self,
                    tr("错误"),
                    f"{tr('无法获取插件信息')}: {server.config.plugin_name}"
                )
                return

            # Create edit dialog (reuse config dialog) - same plugin extension mechanism as new server
            dialog = ServerConfigDialog(plugin_info, self, server.config)

            # Pre-fill with existing values
            dialog.name_field.setText(server_name)
            dialog.name_field.setEnabled(False)  # Don't allow changing name
            dialog.description_field.setText(server.config.description or "")
            dialog.enabled_checkbox.setChecked(server.config.enabled)

            # Pre-fill parameter fields
            for field_name, field_info in dialog.field_widgets.items():
                widget = field_info["widget"]
                value = server.config.parameters.get(field_name)

                if value is not None:
                    from PySide6.QtWidgets import QCheckBox, QSpinBox, QLineEdit
                    if isinstance(widget, QCheckBox):
                        widget.setChecked(bool(value))
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QLineEdit):
                        widget.setText(str(value))

            # Handle special fields
            if server.config.endpoint:
                endpoint_widget = dialog.field_widgets.get("endpoint", {}).get("widget")
                if endpoint_widget:
                    endpoint_widget.setText(server.config.endpoint)

            if server.config.api_key:
                api_key_widget = dialog.field_widgets.get("api_key", {}).get("widget")
                if api_key_widget:
                    api_key_widget.setText(server.config.api_key)

            # Connect to the update handler instead of the create handler
            # Note: We don't need to disconnect anything because each dialog instance
            # is fresh and has no prior connections
            dialog.server_updated.connect(
                lambda name, config: self._on_server_updated(server_name, config)
            )

            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, tr("错误"), f"{tr('编辑服务器失败')}: {str(e)}")
    
    def _on_server_updated(self, server_name: str, config):
        """
        Handle server update from config dialog.
        
        Args:
            server_name: Name of the server to update
            config: Updated ServerConfig object
        """
        try:
            # Update server through server manager
            self.server_manager.update_server(server_name, config)
            
            # Reload server list
            self._load_servers()
            
            # Emit signal
            self.servers_modified.emit()
            
            # Show success message
            QMessageBox.information(
                self,
                tr("成功"),
                f"{tr('服务器')} '{server_name}' {tr('已成功更新')}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("错误"),
                f"{tr('更新服务器失败')}: {str(e)}"
            )
    
    def _on_delete_server(self, server_name: str):
        """Handle delete server"""
        reply = QMessageBox.question(
            self,
            tr("确认删除"),
            f"{tr('确定要删除服务器')} '{server_name}' {tr('吗')}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.server_manager.delete_server(server_name)
                self._load_servers()
                self.servers_modified.emit()
                
            except Exception as e:
                QMessageBox.critical(self, tr("错误"), f"{tr('删除服务器失败')}: {str(e)}")
    
    def _on_add_server(self):
        """Handle add new server - show dropdown menu with available plugins"""
        if not self.server_manager:
            QMessageBox.warning(self, tr("错误"), tr("服务器管理器未初始化"))
            return
        
        # Get available plugins
        plugins = self.server_manager.list_available_plugins()
        
        if not plugins:
            QMessageBox.warning(
                self,
                tr("提示"),
                tr("没有可用的插件。请检查插件目录。")
            )
            return
        
        # Create menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #E1E1E1;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3c3c3c;
                margin: 4px 0px;
            }
        """)
        
        # Add plugin actions
        for plugin in plugins:
            action = QAction(f"{plugin.name} - {plugin.description}", self)
            action.setData(plugin)  # Store plugin info in action
            action.triggered.connect(lambda checked=False, p=plugin: self._show_plugin_config_dialog(p))
            menu.addAction(action)
        
        # Show menu at button position
        button = self.sender()
        if button:
            menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        else:
            menu.exec(self.mapToGlobal(self.rect().center()))
    
    def _show_plugin_config_dialog(self, plugin_info):
        """
        Show configuration dialog for selected plugin.
        
        Args:
            plugin_info: PluginInfo object for the selected plugin
        """
        # Create and show config dialog
        dialog = ServerConfigDialog(plugin_info, self)
        dialog.server_created.connect(self._on_server_created)
        dialog.exec()
    
    def _on_server_created(self, server_name: str, config):
        """
        Handle server creation from config dialog.
        
        Args:
            server_name: Name of the new server
            config: ServerConfig object
        """
        try:
            # Add server through server manager
            self.server_manager.add_server(config)
            
            # Reload server list
            self._load_servers()
            
            # Emit signal
            self.servers_modified.emit()
            
            # Show success message
            QMessageBox.information(
                self,
                tr("成功"),
                f"{tr('服务器')} '{server_name}' {tr('已成功创建')}"
            )
            
        except ValueError as e:
            QMessageBox.critical(
                self,
                tr("错误"),
                f"{tr('创建服务器失败')}: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("错误"),
                f"{tr('创建服务器时发生错误')}: {str(e)}"
            )

