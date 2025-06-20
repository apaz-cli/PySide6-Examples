"""
Media Player Tab - Video and audio player with controls
"""

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSlider, QFileDialog, QMessageBox,
                               QGroupBox, QComboBox, QSpinBox)
from PySide6.QtCore import Qt, QUrl, QTimer

# Try to import multimedia components
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False


class MediaPlayerTab(QWidget):
    """File chooser and media player"""
    def __init__(self):
        super().__init__()
        if MULTIMEDIA_AVAILABLE:
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        if not MULTIMEDIA_AVAILABLE:
            layout.addWidget(QLabel("Multimedia components not available.\nInstall PySide6-Addons for media support."))
            self.setLayout(layout)
            return
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        choose_file_btn = QPushButton("Choose Media File")
        choose_file_btn.clicked.connect(self.choose_file)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(choose_file_btn)
        
        layout.addLayout(file_layout)
        
        # Video widget (for video files)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(300)
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)
        
        # Media controls
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_pause)
        self.play_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        
        # Volume control
        volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(volume_label)
        controls_layout.addWidget(self.volume_slider)
        
        layout.addLayout(controls_layout)
        
        # Position slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        layout.addWidget(self.position_slider)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect media player signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.state_changed)
        
        # Set initial volume
        self.set_volume(50)
        
    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose Media File", "",
            "Media Files (*.mp4 *.avi *.mov *.mp3 *.wav *.flac *.ogg);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)
            
    def load_file(self, file_path):
        try:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.file_label.setText(f"File: {os.path.basename(file_path)}")
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"Loaded: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load media file: {str(e)}")
            
    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def stop(self):
        self.media_player.stop()
        
    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)
        
    def set_position(self, position):
        self.media_player.setPosition(position)
        
    def position_changed(self, position):
        self.position_slider.setValue(position)
        
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        
    def state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("Pause")
            self.status_label.setText("Playing")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_btn.setText("Play")
            self.status_label.setText("Paused")
        else:
            self.play_btn.setText("Play")
            self.status_label.setText("Stopped")