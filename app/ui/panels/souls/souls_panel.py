"""Souls panel for managing AI souls with character card layout and radar charts."""

import logging
from typing import TYPE_CHECKING, Optional
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QDialog, QTabWidget, QTextEdit,
    QFormLayout, QLineEdit, QDoubleSpinBox, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QPolygonF
from PySide6.QtCharts import QChart, QChartView, QPolygonF, QValueAxis, QCategoryAxis
import math

from app.ui.panels.base_panel import BasePanel
from app.data.workspace import Workspace
from utils.i18n_utils import tr
from agent.soul.soul_service import SoulService
from agent.soul.soul import Soul

if TYPE_CHECKING:
    from agent.soul.soul_service import SoulService

logger = logging.getLogger(__name__)


class SoulsPanel(BasePanel):
    """Panel for managing AI souls with character card layout and radar charts."""

    def __init__(self, workspace: Workspace, parent=None):
        """Initialize the souls panel."""
        super().__init__(workspace, parent)
        self.soul_service: Optional[SoulService] = None
        self.soul_widgets = []  # Store references to soul widgets

    def setup_ui(self):
        """Set up the UI components with card layout for souls."""
        self.set_panel_title(tr("Souls"))

        # Add refresh button to toolbar
        self.add_toolbar_button("\ue682", self._refresh_souls, tr("Refresh Souls List"))  # Refresh icon

        # Add add soul button to toolbar
        self.add_toolbar_button("\ue62e", self._add_soul, tr("Add New Soul"))  # Plus icon

    def load_data(self):
        """Load souls data from SoulService."""
        # Initialize soul service with workspace
        # For now, we'll use default paths - in a real implementation, we'd pass the workspace path
        self.soul_service = SoulService()

        # Show loading indicator
        self.show_loading(tr("Loading souls..."))

        # Defer loading to avoid blocking UI
        QTimer.singleShot(0, self._load_souls_async)

    def _load_souls_async(self):
        """Load souls asynchronously."""
        try:
            # Get all souls
            souls = self.soul_service.get_all_souls()

            # Clear existing content
            self._clear_content()

            # Create scroll area for souls grid
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

            # Create content widget for scroll area
            content_widget = QWidget()
            content_widget.setObjectName("soulsGridContainer")
            content_widget.setStyleSheet("""
                QWidget#soulsGridContainer {
                    background-color: #252526;
                }
            """)

            # Create grid layout for souls
            grid_layout = QGridLayout(content_widget)
            grid_layout.setContentsMargins(10, 10, 10, 10)
            grid_layout.setSpacing(15)

            # Calculate columns based on available width
            # For now, use 3 columns as default for larger cards
            cols = 3

            # Add souls to grid
            for idx, soul in enumerate(souls):
                row = idx // cols
                col = idx % cols

                soul_widget = self._create_soul_widget(soul)
                grid_layout.addWidget(soul_widget, row, col)

            # Add stretch to fill remaining space
            grid_layout.setRowStretch(grid_layout.rowCount(), 1)
            grid_layout.setColumnStretch(grid_layout.columnCount(), 1)

            scroll_area.setWidget(content_widget)
            self.content_layout.addWidget(scroll_area)

            # Hide loading indicator
            self.hide_loading()

        except Exception as e:
            logger.error(f"Error loading souls: {e}")
            self.hide_loading()
            QMessageBox.critical(self, tr("Error"), f"{tr('Error loading souls')}: {str(e)}")

    def _create_soul_widget(self, soul: Soul) -> QWidget:
        """Create a widget representing a single soul in character card format."""
        # Main container widget
        container = QWidget()
        container.setObjectName("soulCard")
        container.setFixedWidth(250)  # Fixed width for card-like appearance
        container.setStyleSheet("""
            QWidget#soulCard {
                background-color: #3C3C3C;
                border-radius: 12px;
                border: 1px solid #454545;
                padding: 10px;
            }
            QWidget#soulCard:hover {
                background-color: #454545;
                border: 1px solid #555555;
            }
        """)

        # Main layout for the soul card
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Soul name label
        name_label = QLabel()
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        name_label.setText(soul.name)
        layout.addWidget(name_label)

        # Placeholder for soul image/photo
        photo_frame = QLabel()
        photo_frame.setAlignment(Qt.AlignCenter)
        photo_frame.setFixedSize(100, 100)
        photo_frame.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                border-radius: 8px;
                color: #AAAAAA;
                font-family: "iconfont";
                font-size: 24px;
            }
        """)
        photo_frame.setText("\ue704")  # Default avatar icon
        layout.addWidget(photo_frame)

        # Radar chart for soul abilities
        radar_chart = self._create_radar_chart(soul)
        radar_chart.setFixedHeight(120)
        layout.addWidget(radar_chart)

        # Short description label
        desc_label = QLabel()
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 10px;
                margin-top: 4px;
            }
        """)
        # Get description from knowledge if available
        desc_text = soul.knowledge[:60] + "..." if soul.knowledge and len(soul.knowledge) > 60 else (soul.knowledge or tr("No description"))
        desc_label.setText(desc_text)
        layout.addWidget(desc_label)

        # Button container for actions
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        button_layout.setContentsMargins(0, 8, 0, 0)

        # View/Edit button
        view_btn = QPushButton(tr("View"))
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border-radius: 4px;
                font-size: 9px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #0088EE;
            }
        """)
        view_btn.clicked.connect(lambda: self._view_soul_details(soul))
        button_layout.addWidget(view_btn)

        # Delete button
        delete_btn = QPushButton(tr("Delete"))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #CC0000;
                color: white;
                border-radius: 4px;
                font-size: 9px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #EE0000;
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_soul(soul))
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        # Store soul reference in widget for later use
        container.soul = soul

        return container

    def _create_radar_chart(self, soul: Soul) -> QWidget:
        """Create a radar chart showing soul abilities."""
        # Create a custom widget to draw the radar chart
        radar_widget = QWidget()
        radar_widget.setStyleSheet("background: transparent;")
        
        # For now, we'll create a simple placeholder
        # In a real implementation, we would parse the soul's metadata to get ability values
        abilities = [tr("Wisdom"), tr("Strength"), tr("Charisma"), tr("Agility"), tr("Endurance"), tr("Perception")]

        # Create a simple radar chart representation
        chart_label = QLabel()
        chart_label.setAlignment(Qt.AlignCenter)
        chart_label.setText(tr("Hexagonal Ability Chart"))
        chart_label.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                border-radius: 8px;
                color: #AAAAAA;
                font-size: 10px;
                padding: 4px;
            }
        """)
        
        # Add to layout
        layout = QVBoxLayout(radar_widget)
        layout.addWidget(chart_label)
        layout.setContentsMargins(0, 0, 0, 0)
        
        return radar_widget

    def _clear_content(self):
        """Clear all content from the panel."""
        # Remove all widgets from content layout
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def _refresh_souls(self):
        """Refresh the souls list."""
        self.load_data()

    def _add_soul(self):
        """Add a new soul."""
        # For now, just show a message box since we don't have a form to create souls
        QMessageBox.information(
            self,
            tr("Information"),
            tr("Add soul functionality will be implemented in a future version. Currently you can create new souls directly in the souls folder in the project directory.")
        )

    def _view_soul_details(self, soul: Soul):
        """View and edit the selected soul details."""
        dialog = SoulDetailsDialog(soul, self)
        dialog.exec_()

    def _delete_soul(self, soul: Soul):
        """Delete the selected soul."""
        reply = QMessageBox.question(
            self,
            tr("Confirm Deletion"),
            f"{tr('Are you sure you want to delete the soul')} '{soul.name}' {tr('? This action cannot be undone.')}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # For now, just show a message since we don't have a delete implementation
            QMessageBox.information(
                self,
                tr("Information"),
                f"{tr('Delete soul functionality will be implemented in a future version.')}\n{tr('Soul path')}: {soul.description_file}"
            )

    def on_activated(self):
        """Called when the panel becomes visible."""
        super().on_activated()
        # Refresh data when panel is activated
        if self._data_loaded:
            QTimer.singleShot(0, self._refresh_souls)


class SoulDetailsDialog(QDialog):
    """Dialog for viewing and editing soul details."""

    def __init__(self, soul: Soul, parent=None):
        super().__init__(parent)
        self.soul = soul
        self.setWindowTitle(f"{tr('Soul Details')} - {soul.name}")
        self.resize(600, 500)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Create tab widget for different sections
        tab_widget = QTabWidget()

        # Basic Info Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)

        # Name
        self.name_edit = QLineEdit(self.soul.name)
        self.name_edit.setReadOnly(True)  # For now, make it read-only
        basic_layout.addRow(tr("Name:"), self.name_edit)

        # Skills
        self.skills_edit = QTextEdit()
        self.skills_edit.setPlainText(", ".join(self.soul.skills))
        self.skills_edit.setMaximumHeight(80)
        basic_layout.addRow(tr("Skills:"), self.skills_edit)

        tab_widget.addTab(basic_tab, tr("Basic Information"))

        # Knowledge Tab
        knowledge_tab = QWidget()
        knowledge_layout = QVBoxLayout(knowledge_tab)

        self.knowledge_edit = QTextEdit()
        self.knowledge_edit.setPlainText(self.soul.knowledge or "")
        self.knowledge_edit.setReadOnly(True)  # For now, make it read-only
        knowledge_layout.addWidget(self.knowledge_edit)

        tab_widget.addTab(knowledge_tab, tr("Knowledge Base"))

        # Abilities/Radar Chart Tab
        abilities_tab = QWidget()
        abilities_layout = QVBoxLayout(abilities_tab)

        # Placeholder for radar chart
        radar_placeholder = QLabel(tr("Ability radar chart will be implemented in a future version"))
        radar_placeholder.setAlignment(Qt.AlignCenter)
        radar_placeholder.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                border-radius: 8px;
                padding: 20px;
                color: #AAAAAA;
                font-size: 12px;
            }
        """)
        abilities_layout.addWidget(radar_placeholder)

        tab_widget.addTab(abilities_tab, tr("Abilities Chart"))

        layout.addWidget(tab_widget)

        # Buttons
        button_layout = QHBoxLayout()

        self.edit_button = QPushButton(tr("Edit"))
        self.edit_button.clicked.connect(self._toggle_edit_mode)
        button_layout.addWidget(self.edit_button)

        close_button = QPushButton(tr("Close"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # Set initial state
        self._set_edit_mode(False)

    def _toggle_edit_mode(self):
        """Toggle edit mode."""
        is_read_only = not self.knowledge_edit.isReadOnly()
        self._set_edit_mode(is_read_only)

    def _set_edit_mode(self, editable: bool):
        """Set the edit mode for controls."""
        self.knowledge_edit.setReadOnly(not editable)
        self.name_edit.setReadOnly(not editable)
        
        if editable:
            self.edit_button.setText(tr("Save"))
            self.edit_button.clicked.disconnect()
            self.edit_button.clicked.connect(self._save_changes)
        else:
            self.edit_button.setText(tr("Edit"))
            self.edit_button.clicked.disconnect()
            self.edit_button.clicked.connect(self._toggle_edit_mode)

    def _save_changes(self):
        """Save changes to the soul."""
        # For now, just show a message since we don't have save implementation
        QMessageBox.information(
            self,
            tr("Information"),
            tr("Save functionality will be implemented in a future version.")
        )
        self._set_edit_mode(False)