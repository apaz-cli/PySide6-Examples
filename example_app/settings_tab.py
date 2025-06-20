"""
Settings Tab - Application preferences and configuration
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QCheckBox, QRadioButton, QSpinBox,
                               QGroupBox, QButtonGroup, QMessageBox, QFontDialog,
                               QGridLayout, QSlider, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class SettingsTab(QWidget):
    """Settings and preferences tab"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Theme settings
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QVBoxLayout()
        
        self.theme_group = QButtonGroup()
        light_radio = QRadioButton("Light Theme")
        dark_radio = QRadioButton("Dark Theme")
        light_radio.setChecked(True)
        
        self.theme_group.addButton(light_radio, 0)
        self.theme_group.addButton(dark_radio, 1)
        
        theme_layout.addWidget(light_radio)
        theme_layout.addWidget(dark_radio)
        theme_group.setLayout(theme_layout)
        
        # Font settings
        font_group = QGroupBox("Font Settings")
        font_layout = QGridLayout()
        
        font_layout.addWidget(QLabel("Font Size:"), 0, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(12)
        font_layout.addWidget(self.font_size_spin, 0, 1)
        
        font_btn = QPushButton("Choose Font")
        font_btn.clicked.connect(self.choose_font)
        font_layout.addWidget(font_btn, 1, 0, 1, 2)
        
        font_group.setLayout(font_layout)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout()
        
        self.auto_save_check = QCheckBox("Auto-save enabled")
        self.notifications_check = QCheckBox("Show notifications")
        self.sound_check = QCheckBox("Sound effects")
        
        self.auto_save_check.setChecked(True)
        self.notifications_check.setChecked(True)
        
        general_layout.addWidget(self.auto_save_check)
        general_layout.addWidget(self.notifications_check)
        general_layout.addWidget(self.sound_check)
        
        general_group.setLayout(general_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self.apply_settings)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_settings)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        
        # Add all to main layout
        layout.addWidget(theme_group)
        layout.addWidget(font_group)
        layout.addWidget(general_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def choose_font(self):
        ok, font = QFontDialog.getFont()
        if ok:
            self.setFont(font)
            QMessageBox.information(self, "Font Selected", f"Selected font: {font.family()}, Size: {font.pointSize()}")
            
    def apply_settings(self):
        theme = "Light" if self.theme_group.checkedId() == 0 else "Dark"
        font_size = self.font_size_spin.value()
        auto_save = self.auto_save_check.isChecked()
        notifications = self.notifications_check.isChecked()
        sound = self.sound_check.isChecked()
        
        settings_text = f"""Settings Applied:
Theme: {theme}
Font Size: {font_size}
Auto-save: {auto_save}
Notifications: {notifications}
Sound Effects: {sound}"""
        
        QMessageBox.information(self, "Settings Applied", settings_text)
        
    def reset_settings(self):
        self.theme_group.button(0).setChecked(True)
        self.font_size_spin.setValue(12)
        self.auto_save_check.setChecked(True)
        self.notifications_check.setChecked(True)
        self.sound_check.setChecked(False)
        QMessageBox.information(self, "Settings Reset", "All settings have been reset to default values.")
