import sys
import os
from PySide6.QtCore import Qt, QUrl, QTimer, QDir, QFileInfo
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QGroupBox, QSlider, QFileDialog, QFontDialog)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPalette, QBrush, QPixmap, QPainter, QLinearGradient, QColor
from monaco_widget import MonacoEditorWidget
from file_explorer import FileExplorer
from sandbox import SandboxWidget
from theme_manager import theme_manager
from settings import settings_manager


class BackgroundWidget(QWidget):
    """Base widget with background image support"""
    def __init__(self):
        super().__init__()
        self.background_pixmap = None
        self.background_opacity = 0.7
        self.dark_mode = theme_manager.dark_mode
        
    def set_background_image(self, pixmap):
        self.background_pixmap = pixmap
        self.update()
    
    def set_background_opacity(self, opacity):
        self.background_opacity = opacity
        self.update()
    
    def set_dark_mode(self, dark_mode):
        self.dark_mode = dark_mode
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw gradient background if no image
        if self.background_pixmap is None:
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(74, 144, 226))  # Blue
            gradient.setColorAt(0.5, QColor(39, 174, 96))  # Green
            gradient.setColorAt(1, QColor(231, 76, 60))    # Red
            painter.fillRect(self.rect(), QBrush(gradient))
        else:
            # Draw the background image
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            # Center the image
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        
        # Apply opacity overlay
        colors = theme_manager.get_colors()
        overlay_color = QColor(30, 30, 30) if self.dark_mode else Qt.white
        painter.setOpacity(1.0 - self.background_opacity)
        painter.fillRect(self.rect(), QBrush(overlay_color))
        
        painter.end()


class StyledWebView(QWebEngineView):
    def __init__(self):
        super().__init__()
        # Make the webview background transparent
        self.page().setBackgroundColor(Qt.transparent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PerfWizard")
        
        # Load settings first
        self._load_settings()
        
        # Create custom central widget with background support
        self.central_widget = BackgroundWidget()
        self.setCentralWidget(self.central_widget)
        
        # Connect to theme manager
        theme_manager.theme_changed.connect(self.on_theme_changed)
        theme_manager.font_changed.connect(self.on_font_changed)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Top controls section
        self.controls_group = QGroupBox("Settings")
        self.controls_group.setObjectName("controls_group")
        controls_layout = QVBoxLayout()
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.load_bg_btn = QPushButton("Load Background Image")
        self.load_bg_btn.clicked.connect(self.load_background)
        
        
        
        self.clear_bg_btn = QPushButton("Clear Background")
        self.clear_bg_btn.clicked.connect(self.clear_background)
        
        self.dark_mode_btn = QPushButton("🌙 Dark Mode")
        self.dark_mode_btn.clicked.connect(theme_manager.toggle_dark_mode)
        
        self.font_btn = QPushButton("🔤 Select Font")
        self.font_btn.clicked.connect(self.select_font)
        
        button_layout.addWidget(self.load_bg_btn)
        button_layout.addWidget(self.clear_bg_btn)
        button_layout.addWidget(self.dark_mode_btn)
        button_layout.addWidget(self.font_btn)
        button_layout.addStretch()
        
        # Set initial button text after button is created
        self._update_dark_mode_button_text()
        
        # Opacity slider
        slider_layout = QHBoxLayout()
        self.slider_label = QLabel("Background Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        
        # Load saved opacity or use default
        saved_opacity = settings_manager.get("ui", "background_opacity", 0.7)
        slider_value = int(saved_opacity * 100)
        self.opacity_slider.setValue(slider_value)
        self.opacity_slider.valueChanged.connect(self.update_background_opacity)
        self.opacity_label = QLabel(f"{slider_value}%")
        
        # Set initial opacity
        self.central_widget.set_background_opacity(saved_opacity)
        
        slider_layout.addWidget(self.slider_label)
        slider_layout.addWidget(self.opacity_slider)
        slider_layout.addWidget(self.opacity_label)
        slider_layout.addStretch()
        
        controls_layout.addLayout(button_layout)
        controls_layout.addLayout(slider_layout)
        self.controls_group.setLayout(controls_layout)
        
        # Content area with file explorer, webview and native widget
        content_layout = QHBoxLayout()
        
        # File Explorer section
        self.file_explorer = FileExplorer()
        self.file_explorer.content_ready.connect(self.load_file_content)
        self.file_explorer.file_selected.connect(self.on_file_selected)
        
        # Monaco Editor section
        self.editor_group = QGroupBox("Editor")
        self.editor_group.setObjectName("editor_group")
        editor_layout = QVBoxLayout()
        
        self.monaco_editor = MonacoEditorWidget()
        self.monaco_editor.content_changed.connect(self.on_editor_content_changed)
        self.monaco_editor.set_language("python")
        self.monaco_editor.set_content("# Welcome to Monaco Editor\nprint('Hello World!')")
        
        editor_layout.addWidget(self.monaco_editor)
        self.editor_group.setLayout(editor_layout)
        
        # Python Analysis section
        self.analysis_group = QGroupBox("Python Analysis")
        self.analysis_group.setObjectName("analysis_group")
        analysis_layout = QVBoxLayout()
        
        self.sandbox_widget = SandboxWidget()
        analysis_layout.addWidget(self.sandbox_widget)
        self.analysis_group.setLayout(analysis_layout)
        
        # Add to content layout
        content_layout.addWidget(self.file_explorer, 1)
        content_layout.addWidget(self.editor_group, 2)
        content_layout.addWidget(self.analysis_group, 1)
        
        # Add all to main layout
        main_layout.addWidget(self.controls_group)
        main_layout.addLayout(content_layout)
        
        # Apply initial theme
        self.apply_theme()
        
        # Load saved background image if any
        self._load_background_image()
    
    def _load_settings(self):
        """Load application settings"""
        settings_manager.load_settings()
        theme_manager.set_settings_manager(settings_manager)
        
        # Restore window geometry if saved
        saved_geometry = settings_manager.get("ui", "window_geometry")
        if saved_geometry:
            self.setGeometry(*saved_geometry)
        else:
            self.setGeometry(100, 100, 1000, 700)
    
    def _load_background_image(self):
        """Load saved background image"""
        saved_bg = settings_manager.get("ui", "background_image")
        if saved_bg and os.path.exists(saved_bg):
            pixmap = QPixmap(saved_bg)
            if not pixmap.isNull():
                self.central_widget.set_background_image(pixmap)
    
    def _save_window_geometry(self):
        """Save current window geometry"""
        geometry = self.geometry()
        settings_manager.set("ui", "window_geometry", [
            geometry.x(), geometry.y(), geometry.width(), geometry.height()
        ])
        settings_manager.save_settings()
    
    def on_theme_changed(self, dark_mode):
        """Handle theme changes"""
        self.central_widget.set_dark_mode(dark_mode)
        self._update_dark_mode_button_text()
        self.apply_theme()
    
    def _update_dark_mode_button_text(self):
        """Update dark mode button text based on current theme"""
        if theme_manager.dark_mode:
            self.dark_mode_btn.setText("☀️ Light Mode")
        else:
            self.dark_mode_btn.setText("🌙 Dark Mode")
    
    def apply_theme(self):
        """Apply current theme to all widgets"""
        # Apply group box styles
        self.controls_group.setStyleSheet(theme_manager.get_widget_style('group_box', border_color='primary'))
        self.editor_group.setStyleSheet(theme_manager.get_widget_style('group_box', border_color='secondary'))
        self.analysis_group.setStyleSheet(theme_manager.get_widget_style('group_box', border_color='accent'))
        
        # Apply button styles
        button_style = theme_manager.get_widget_style('button')
        for button in [self.load_bg_btn, self.clear_bg_btn, self.dark_mode_btn, self.font_btn]:
            button.setStyleSheet(button_style)
        
        # Apply other widget styles
        self.slider_label.setStyleSheet(theme_manager.get_widget_style('text'))
        self.opacity_label.setStyleSheet(theme_manager.get_widget_style('text'))
        self.opacity_slider.setStyleSheet(theme_manager.get_widget_style('slider'))
        
    
    def load_file_content(self, content, language):
        """Load file content into Monaco editor"""
        self.monaco_editor.set_content(content)
        self.monaco_editor.set_language(language)
    
    def on_file_selected(self, file_path):
        """Handle file selection for analysis"""
        self.sandbox_widget.analyze_file(file_path)
    
    def select_font(self):
        """Open font selection dialog"""
        from PySide6.QtGui import QFont
        
        # Create current font object
        current_font = QFont(theme_manager.current_font_family, int(theme_manager.current_font_size))
        
        # Open font dialog
        ok, font = QFontDialog.getFont(current_font, self, "Select Font")
        
        if ok:
            # Update theme manager with selected font
            theme_manager.set_font(font.family(), font.pointSizeF())
    
    def on_font_changed(self, font_family, font_size):
        """Handle font changes"""
        # Update Monaco editor font
        if self.monaco_editor.is_ready():
            self.monaco_editor.set_editor_options(
                fontFamily=f"{font_family}, monospace",
                fontSize=int(font_size)
            )

    
    def on_editor_content_changed(self, content):
        """Handle Monaco editor content changes"""
        # You can add logic here to respond to editor changes
        pass
    
    def load_background(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.central_widget.set_background_image(pixmap)
                # Save background image path
                settings_manager.set("ui", "background_image", file_path)
                settings_manager.save_settings()
    
    def clear_background(self):
        self.central_widget.set_background_image(None)
        # Clear saved background image
        settings_manager.set("ui", "background_image", None)
        settings_manager.save_settings()
    
    def update_background_opacity(self, value):
        opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.central_widget.set_background_opacity(opacity)
        # Save opacity setting
        settings_manager.set("ui", "background_opacity", opacity)
        settings_manager.save_settings()
    
    def closeEvent(self, event):
        """Handle application close event"""
        self._save_window_geometry()
        super().closeEvent(event)


def main():
    # Set high DPI attributes before creating QApplication
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
