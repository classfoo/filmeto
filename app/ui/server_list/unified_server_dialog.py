"""
Unified Server Management Dialog

Mac-style preferences dialog that switches between server list and config views
using navigation buttons instead of opening separate dialogs.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QPushButton, QMessageBox, QMenu, QStackedWidget, QDialogButtonBox, QVBoxLayout, QWidget
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction

from app.ui.dialog.custom_dialog import CustomDialog
from app.ui.server_list.server_views import ServerListView, ServerConfigView
from utils.i18n_utils import tr


class UnifiedServerDialog(CustomDialog):
    """
    Unified dialog for server management with Mac-style navigation.
    
    This dialog contains a stacked widget that switches between:
    - Server list view
    - Server configuration view
    
    Navigation is handled via back/forward buttons in the title bar.
    """
    
    # Signal emitted when servers are modified
    servers_modified = Signal()
    
    def __init__(self, workspace, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.server_manager = None
        
        # Navigation state
        self.view_history = []
        self.current_view_index = -1
        
        # Setup dialog
        self.setMinimumSize(700, 500)
        
        # Initialize UI
        self._init_ui()
        
        # Load servers
        self._load_servers()
        
        # Show list view initially
        self._show_list_view()
    
    def _init_ui(self):
        """Initialize UI components"""
        # Show navigation buttons
        self.show_navigation_buttons(True)

        # Connect navigation signals
        self.back_clicked.connect(self._on_back_clicked)
        self.forward_clicked.connect(self._on_forward_clicked)

        # Create main content widget with layout
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Create stacked widget for view switching
        self.stacked_widget = QStackedWidget(self)

        # Create views
        self.list_view = ServerListView(self)
        self.config_view = ServerConfigView(self)

        # Add views to stack
        self.stacked_widget.addWidget(self.list_view)
        self.stacked_widget.addWidget(self.config_view)

        # Connect signals from list view
        self.list_view.server_selected_for_edit.connect(self._on_edit_server)
        self.list_view.server_toggled.connect(self._on_toggle_server)
        self.list_view.server_deleted.connect(self._on_delete_server)
        self.list_view.add_server_clicked.connect(self._on_add_server)
        self.list_view.refresh_clicked.connect(self._load_servers)

        # Connect signals from config view
        self.config_view.save_clicked.connect(self._on_config_saved)
        self.config_view.cancel_clicked.connect(self._on_config_cancelled)

        # Add the stacked widget to the main layout
        main_layout.addWidget(self.stacked_widget)

        # Create button box with close button at the bottom
        self.button_box = QDialogButtonBox()
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)
        self.close_button.setText(tr("关闭"))  # Use translation for "Close"
        self.close_button.clicked.connect(self.reject)  # Close the dialog when clicked
        main_layout.addWidget(self.button_box)

        # Set the main content as the dialog's content
        self.setContentWidget(main_content)

        # Add title bar buttons
        self._add_titlebar_buttons()
    
    def _add_titlebar_buttons(self):
        """Add action buttons to title bar"""
        # Refresh button
        self.refresh_button = QPushButton("🔄 " + tr("刷新"), self)
        self.refresh_button.clicked.connect(self._load_servers)
        self.refresh_button.setFixedHeight(26)
        self._style_title_button(self.refresh_button)
        self.title_bar.toolbar_layout.addWidget(self.refresh_button)
        
        # Add server button
        self.add_button = QPushButton("➕ " + tr("添加服务器"), self)
        self.add_button.clicked.connect(self._on_add_server)
        self.add_button.setFixedHeight(26)
        self._style_title_button(self.add_button)
        self.title_bar.toolbar_layout.addWidget(self.add_button)
    
    def _style_title_button(self, button):
        """Apply styling to title bar buttons"""
        button.setStyleSheet("""
            QPushButton {
                background-color: #4c5052;
                color: #E1E1E1;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5c6062;
                border: 1px solid #777777;
            }
            QPushButton:pressed {
                background-color: #3c4042;
            }
        """)
    
    def _load_servers(self):
        """Load servers from ServerManager"""
        try:
            from server.server import ServerManager
            
            # Get workspace path
            workspace_path = self.workspace.workspace_path
            
            # Create server manager
            self.server_manager = ServerManager(workspace_path)
            
            # Set server manager in list view
            self.list_view.set_server_manager(self.server_manager)
            
        except Exception as e:
            print(f"Failed to load servers: {e}")
            QMessageBox.critical(self, tr("错误"), f"{tr('加载服务器失败')}: {str(e)}")
    
    def _show_list_view(self):
        """Switch to list view"""
        self.stacked_widget.setCurrentWidget(self.list_view)
        self.set_title(tr("服务器管理"))
        self._update_title_bar_buttons(show_list_buttons=True)
        self._add_to_history("list")
        self._update_navigation_buttons()
    
    def _show_config_view(self, plugin_info, server_config=None):
        """
        Switch to config view.
        
        Args:
            plugin_info: PluginInfo object
            server_config: Optional ServerConfig for editing
        """
        self.config_view.configure(plugin_info, server_config)
        self.stacked_widget.setCurrentWidget(self.config_view)
        
        if server_config:
            self.set_title(f"{tr('编辑服务器')} - {server_config.name}")
        else:
            self.set_title(f"{tr('添加服务器')} - {plugin_info.name}")
        
        self._update_title_bar_buttons(show_list_buttons=False)
        self._add_to_history("config")
        self._update_navigation_buttons()
    
    def _update_title_bar_buttons(self, show_list_buttons: bool):
        """Update visibility of title bar buttons based on current view"""
        self.refresh_button.setVisible(show_list_buttons)
        self.add_button.setVisible(show_list_buttons)
    
    def _add_to_history(self, view_name: str):
        """Add view to navigation history"""
        # Trim forward history if we're not at the end
        if self.current_view_index < len(self.view_history) - 1:
            self.view_history = self.view_history[:self.current_view_index + 1]
        
        # Add new view
        self.view_history.append(view_name)
        self.current_view_index = len(self.view_history) - 1
    
    def _update_navigation_buttons(self):
        """Update navigation button states"""
        can_go_back = self.current_view_index > 0
        can_go_forward = self.current_view_index < len(self.view_history) - 1
        self.set_navigation_enabled(can_go_back, can_go_forward)
    
    def _on_back_clicked(self):
        """Handle back button click"""
        if self.current_view_index > 0:
            self.current_view_index -= 1
            view_name = self.view_history[self.current_view_index]
            self._navigate_to_view(view_name)
    
    def _on_forward_clicked(self):
        """Handle forward button click"""
        if self.current_view_index < len(self.view_history) - 1:
            self.current_view_index += 1
            view_name = self.view_history[self.current_view_index]
            self._navigate_to_view(view_name)
    
    def _navigate_to_view(self, view_name: str):
        """Navigate to a view without adding to history"""
        if view_name == "list":
            self.stacked_widget.setCurrentWidget(self.list_view)
            self.set_title(tr("服务器管理"))
            self._update_title_bar_buttons(show_list_buttons=True)
        elif view_name == "config":
            self.stacked_widget.setCurrentWidget(self.config_view)
            # Title would have been set when originally navigating to config view
            self._update_title_bar_buttons(show_list_buttons=False)
        
        self._update_navigation_buttons()
    
    def _on_toggle_server(self, server_name: str, enabled: bool):
        """Handle server enable/disable toggle"""
        try:
            server = self.server_manager.get_server(server_name)
            if server:
                server.config.enabled = enabled
                self.server_manager.update_server(server_name, server.config)
                self.list_view.load_servers()
                self.servers_modified.emit()
        except Exception as e:
            QMessageBox.critical(self, tr("错误"), f"{tr('更新服务器失败')}: {str(e)}")
    
    def _on_edit_server(self, server_name: str):
        """Handle edit server request"""
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
            
            # Show config view for editing
            self._show_config_view(plugin_info, server.config)
            
        except Exception as e:
            QMessageBox.critical(self, tr("错误"), f"{tr('编辑服务器失败')}: {str(e)}")
    
    def _on_delete_server(self, server_name: str):
        """Handle delete server request"""
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
                self.list_view.load_servers()
                self.servers_modified.emit()
            except Exception as e:
                QMessageBox.critical(self, tr("错误"), f"{tr('删除服务器失败')}: {str(e)}")
    
    def _on_add_server(self):
        """Handle add new server request"""
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
        
        # Filter out default server plugins
        filtered_plugins = [
            plugin for plugin in plugins 
            if plugin.name not in ["Local Server", "Filmeto Server"]
        ]
        
        if not filtered_plugins:
            QMessageBox.warning(
                self,
                tr("提示"),
                tr("没有可用的服务器插件。请检查插件目录。")
            )
            return
        
        # Create menu for plugin selection
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
        for plugin in filtered_plugins:
            action = QAction(plugin.name, self)
            action.triggered.connect(lambda checked=False, p=plugin: self._show_config_view(p))
            menu.addAction(action)
        
        # Show menu at button position
        button = self.sender()
        if button:
            menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        else:
            menu.exec(self.mapToGlobal(self.rect().center()))
    
    def _on_config_saved(self, server_name: str, config):
        """Handle configuration saved from config view"""
        try:
            # Determine if this is create or update
            existing_server = self.server_manager.get_server(server_name)
            
            if existing_server:
                # Update existing server
                self.server_manager.update_server(server_name, config)
                QMessageBox.information(
                    self,
                    tr("成功"),
                    f"{tr('服务器')} '{server_name}' {tr('已成功更新')}"
                )
            else:
                # Create new server
                self.server_manager.add_server(config)
                QMessageBox.information(
                    self,
                    tr("成功"),
                    f"{tr('服务器')} '{server_name}' {tr('已成功创建')}"
                )
            
            # Reload list and go back to list view
            self.list_view.load_servers()
            self.servers_modified.emit()
            self._show_list_view()
            
        except ValueError as e:
            QMessageBox.critical(
                self,
                tr("错误"),
                f"{tr('保存服务器失败')}: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("错误"),
                f"{tr('保存服务器时发生错误')}: {str(e)}"
            )
    
    def _on_config_cancelled(self):
        """Handle configuration cancelled from config view"""
        # Go back to list view
        self._show_list_view()

