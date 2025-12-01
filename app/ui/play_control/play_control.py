"""
PlayControlWidget - A playback control toolbar component

This component provides playback controls for the timeline:
- Previous segment button (left)
- Play/Pause toggle button (center)
- Next segment button (right)

Designed to fit in a 28px height bottom bar with dark theme styling.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal, QTimer, QElapsedTimer
from PySide6.QtGui import QFont
from ..base_widget import BaseWidget
from ...data.workspace import Workspace
from ..signals import Signals


class PlayControlWidget(BaseWidget):
    """
    Play control widget for timeline playback control.
    
    Layout: [Previous] [Play/Pause] [Next]
    - Fixed height: 28px (fits in bottom bar)
    - Dark theme styling
    - Uses iconfont icons
    
    Signals:
        previous_clicked: Emitted when previous segment button is clicked
        play_pause_clicked: Emitted when play/pause button is clicked (bool: is_playing)
        next_clicked: Emitted when next segment button is clicked
    """
    # Signals for control actions
    previous_clicked = Signal()
    play_pause_clicked = Signal(bool)  # True if playing, False if paused
    next_clicked = Signal()
    
    def __init__(self, workspace: Workspace, parent=None):
        super(PlayControlWidget, self).__init__(workspace)
        self.parent = parent
        self.workspace = workspace
        
        # Playback state
        self._is_playing = False
        
        # High-precision timer for playback
        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(1)  # 1ms interval
        self._playback_timer.setTimerType(Qt.PreciseTimer)  # Use precise timer
        self._playback_timer.timeout.connect(self._on_playback_tick)
        
        # Elapsed timer for accurate time tracking
        self._elapsed_timer = QElapsedTimer()
        self._last_position = 0.0  # Last position in seconds
        
        # Connect to UI signal manager for timeline position clicked
        Signals().connect(Signals.TIMELINE_POSITION_CLICKED, self._on_timeline_position_clicked)
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Fixed height for bottom bar
        self.setFixedHeight(28)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Icon font
        icon_font = QFont("iconfont", 12)
        
        # Previous segment button (left-double-arrow: \ue841)
        self.previous_button = QPushButton("\ue665")
        self.previous_button.setObjectName("play_control_previous")
        self.previous_button.setFont(icon_font)
        self.previous_button.setFixedSize(24, 24)
        self.previous_button.setToolTip("Previous segment")
        self.previous_button.clicked.connect(self._on_previous_clicked)
        layout.addWidget(self.previous_button)
        
        # Play/Pause button (center) - playcircle: \ue6af
        self.play_pause_button = QPushButton("\ue65f")
        self.play_pause_button.setObjectName("play_control_play_pause")
        self.play_pause_button.setFont(icon_font)
        self.play_pause_button.setFixedSize(24, 24)
        self.play_pause_button.setToolTip("Play")
        self.play_pause_button.setCheckable(True)
        self.play_pause_button.clicked.connect(self._on_play_pause_clicked)
        layout.addWidget(self.play_pause_button)
        
        # Next segment button (right-double-arrow: \ue847)
        self.next_button = QPushButton("\ue664")
        self.next_button.setObjectName("play_control_next")
        self.next_button.setFont(icon_font)
        self.next_button.setFixedSize(24, 24)
        self.next_button.setToolTip("Next segment")
        self.next_button.clicked.connect(self._on_next_clicked)
        layout.addWidget(self.next_button)
        
        # Apply dark theme styling
        self._apply_styles()
    
    def _apply_styles(self):
        """Apply dark theme styling to match overall application style."""
        style = """
            QPushButton {
                background-color: #3c3f41;
                color: #E1E1E1;
                border: 1px solid #555555;
                border-radius: 4px;
                font-family: iconfont;
            }
            QPushButton:hover {
                background-color: #4c5052;
                color: #ffffff;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #2c2f31;
            }
            QPushButton:checked {
                background-color: #4080ff;
                color: #ffffff;
                border: 1px solid #4080ff;
            }
        """
        self.setStyleSheet(style)
    
    def _on_previous_clicked(self):
        """Handle previous segment button click."""
        self.previous_clicked.emit()
    
    def _on_play_pause_clicked(self, checked):
        """Handle play/pause button click."""
        self._is_playing = checked
        
        # Update button icon and tooltip based on state
        if self._is_playing:
            # Change to pause icon - using close circle as pause alternative
            self.play_pause_button.setText("\uea5c")
            self.play_pause_button.setToolTip("Pause")
            # Start playback
            self._start_playback()
        else:
            # Change to play icon
            self.play_pause_button.setText("\ue65f")
            self.play_pause_button.setToolTip("Play")
            # Stop playback
            self._stop_playback()
        
        # Emit signal with current state
        self.play_pause_clicked.emit(self._is_playing)
    
    def _on_next_clicked(self):
        """Handle next segment button click."""
        self.next_clicked.emit()
    
    def _on_timeline_position_clicked(self, sender, params=None, **kwargs):
        if self._is_playing:
            # Pause playback
            self.set_playing(False)
    
    def is_playing(self) -> bool:
        """
        Get the current playback state.
        
        Returns:
            bool: True if playing, False if paused
        """
        return self._is_playing
    
    def set_playing(self, playing: bool):
        """
        Set the playback state programmatically.
        
        Args:
            playing (bool): True to set to playing, False to set to paused
        """
        if self._is_playing != playing:
            self.play_pause_button.setChecked(playing)
            self._on_play_pause_clicked(playing)
    
    def _start_playback(self):
        """
        Start the playback timer.
        Initialize elapsed timer for accurate time tracking.
        """
        # Get current position from project
        project = self.workspace.get_project()
        self._last_position = project.get_timeline_position()
        
        # Start high-precision elapsed timer
        self._elapsed_timer.start()
        
        # Start the playback timer (1ms interval)
        self._playback_timer.start()
    
    def _stop_playback(self):
        """
        Stop the playback timer and save final position.
        Emits TIMELINE_POSITION_STOPPED signal with position and x coordinate.
        """
        # Stop the timer
        self._playback_timer.stop()
        
        # Save the last position
        if self._elapsed_timer.isValid():
            elapsed_ms = self._elapsed_timer.elapsed()
            elapsed_sec = elapsed_ms / 1000.0
            new_position = self._last_position + elapsed_sec
            
            # Round to millisecond precision (3 decimal places = 0.001s)
            new_position = round(new_position, 3)
            
            project = self.workspace.get_project()
            timeline_duration = project.get_timeline_duration()
            
            # Handle looping
            if timeline_duration > 0:
                new_position = new_position % timeline_duration
                # Round again after modulo operation to maintain millisecond precision
                new_position = round(new_position, 3)
            
            # Update project position with immediate flush
            project.set_timeline_position(new_position, flush=True)
            # Send signal with timeline_position, timeline_x, and card_number
            Signals().send(Signals.TIMELINE_POSITION_STOPPED, params=new_position)
    
    def _on_playback_tick(self):
        """
        Called every 1ms during playback.
        Updates timeline position with high precision using debounced writes.
        """
        if not self._elapsed_timer.isValid():
            return
        
        # Get elapsed time in milliseconds
        elapsed_ms = self._elapsed_timer.elapsed()
        elapsed_sec = elapsed_ms / 1000.0
        
        # Calculate new position
        new_position = self._last_position + elapsed_sec
        
        # Round to millisecond precision (3 decimal places = 0.001s)
        new_position = round(new_position, 3)
        
        # Get project and timeline duration
        project = self.workspace.get_project()
        timeline_duration = project.get_timeline_duration()
        
        # Handle looping when exceeding timeline duration
        if timeline_duration > 0 and new_position >= timeline_duration:
            # Loop back to start
            new_position = new_position % timeline_duration
            # Round again after modulo operation to maintain millisecond precision
            new_position = round(new_position, 3)
            # Reset timers for next loop
            self._last_position = 0.0
            self._elapsed_timer.restart()
        
        # Update project position with debounced write (flush=False)
        # This will batch writes and only save every 500ms
        project.set_timeline_position(new_position, flush=False)
    
    def reset(self):
        """Reset the control to initial paused state."""
        self._stop_playback()
        self.set_playing(False)
        
        # Reset position to 0 with immediate flush
        project = self.workspace.get_project()
        project.set_timeline_position(0.0, flush=True)
