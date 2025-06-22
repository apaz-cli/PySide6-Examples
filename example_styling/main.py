import sys
import os
from PySide6.QtCore import Qt, QUrl, QTimer, QDir, QFileInfo
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QGroupBox, QSlider, QFileDialog, QTreeView, QComboBox,
                               QFileSystemModel)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPalette, QBrush, QPixmap, QPainter, QLinearGradient, QColor
from styled_monaco_widget import StyledMonacoWidget
from theme_manager import theme_manager


class TransparentWidget(QWidget):
    """Base widget with background image support"""
    def __init__(self):
        super().__init__()
        self.background_pixmap = None
        self.background_opacity = 0.7
        self.dark_mode = False
        
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
        self.setWindowTitle("PySide6 WebView Integration Example")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create custom central widget with background support
        self.central_widget = TransparentWidget()
        self.setCentralWidget(self.central_widget)
        
        # Connect to theme manager
        theme_manager.theme_changed.connect(self.on_theme_changed)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Top controls section
        self.controls_group = QGroupBox("Native Qt Controls")
        self.controls_group.setObjectName("controls_group")
        controls_layout = QVBoxLayout()
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.load_bg_btn = QPushButton("Load Background Image")
        self.load_bg_btn.clicked.connect(self.load_background)
        self.style_button(self.load_bg_btn)
        
        self.refresh_btn = QPushButton("Refresh WebView")
        self.refresh_btn.clicked.connect(self.refresh_webview)
        self.style_button(self.refresh_btn)
        
        self.demo_btn = QPushButton("Load Demo Content")
        self.demo_btn.clicked.connect(self.load_demo_content)
        self.style_button(self.demo_btn)
        
        self.clear_bg_btn = QPushButton("Clear Background")
        self.clear_bg_btn.clicked.connect(self.clear_background)
        self.style_button(self.clear_bg_btn)
        
        self.dark_mode_btn = QPushButton("🌙 Dark Mode")
        self.dark_mode_btn.clicked.connect(theme_manager.toggle_dark_mode)
        
        button_layout.addWidget(self.load_bg_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.demo_btn)
        button_layout.addWidget(self.clear_bg_btn)
        button_layout.addWidget(self.dark_mode_btn)
        button_layout.addStretch()
        
        # Opacity slider
        slider_layout = QHBoxLayout()
        self.slider_label = QLabel("Background Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(self.update_background_opacity)
        self.opacity_label = QLabel("70%")
        
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
        self.explorer_group = QGroupBox("File Explorer")
        self.explorer_group.setObjectName("explorer_group")
        explorer_layout = QVBoxLayout()
        
        # Directory dropdown
        self.dir_combo = QComboBox()
        self.dir_combo.addItem("Current Directory", os.getcwd())
        self.dir_combo.addItem("Home Directory", os.path.expanduser("~"))
        self.dir_combo.addItem("Root Directory", "/")
        self.dir_combo.currentTextChanged.connect(self.change_directory)
        
        # File tree view
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(os.getcwd())
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(os.getcwd()))
        self.file_tree.setColumnWidth(0, 200)
        self.file_tree.hideColumn(1)  # Hide size column
        self.file_tree.hideColumn(2)  # Hide type column
        self.file_tree.hideColumn(3)  # Hide date column
        self.file_tree.setHeaderHidden(True)  # Hide the header with "Name"
        self.file_tree.clicked.connect(self.file_selected)
        
        # Selected file label
        self.selected_file_label = QLabel("No file selected")
        self.selected_file_label.setWordWrap(True)
        
        explorer_layout.addWidget(QLabel("Directory:"))
        explorer_layout.addWidget(self.dir_combo)
        explorer_layout.addWidget(self.file_tree)
        explorer_layout.addWidget(self.selected_file_label)
        self.explorer_group.setLayout(explorer_layout)
        
        # Monaco Editor section
        self.editor_group = QGroupBox("Monaco Editor")
        self.editor_group.setObjectName("editor_group")
        editor_layout = QVBoxLayout()
        
        self.monaco_editor = StyledMonacoWidget()
        self.monaco_editor.content_changed.connect(self.on_editor_content_changed)
        self.monaco_editor.set_language("python")
        self.monaco_editor.set_content("# Welcome to Monaco Editor\nprint('Hello World!')")
        
        editor_layout.addWidget(self.monaco_editor)
        self.editor_group.setLayout(editor_layout)
        
        # Placeholder section
        self.placeholder_group = QGroupBox("Placeholder Panel")
        self.placeholder_group.setObjectName("placeholder_group")
        placeholder_layout = QVBoxLayout()
        
        self.info_label = QLabel("This is a placeholder panel.\nFuture functionality will be added here.")
        self.info_label.setWordWrap(True)
        
        self.placeholder_content = QLabel("Reserved for future features...")
        self.placeholder_content.setAlignment(Qt.AlignCenter)
        
        placeholder_layout.addWidget(self.info_label)
        placeholder_layout.addWidget(self.placeholder_content)
        placeholder_layout.addStretch()
        self.placeholder_group.setLayout(placeholder_layout)
        
        # Add to content layout
        content_layout.addWidget(self.explorer_group, 1)
        content_layout.addWidget(self.editor_group, 2)
        content_layout.addWidget(self.placeholder_group, 1)
        
        # Add all to main layout
        main_layout.addWidget(self.controls_group)
        main_layout.addLayout(content_layout)
        
        # Apply initial theme
        self.apply_theme()
    
    def on_theme_changed(self, dark_mode):
        """Handle theme changes"""
        self.central_widget.set_dark_mode(dark_mode)
        
        # Update button text
        if dark_mode:
            self.dark_mode_btn.setText("☀️ Light Mode")
        else:
            self.dark_mode_btn.setText("🌙 Dark Mode")
        
        self.apply_theme()
    
    def apply_theme(self):
        """Apply current theme to all widgets"""
        # Apply group box styles
        self.controls_group.setStyleSheet(theme_manager.get_group_box_style('primary'))
        self.explorer_group.setStyleSheet(theme_manager.get_group_box_style('purple'))
        self.editor_group.setStyleSheet(theme_manager.get_group_box_style('secondary'))
        self.placeholder_group.setStyleSheet(theme_manager.get_group_box_style('accent'))
        
        # Apply button styles
        button_style = theme_manager.get_button_style()
        for button in [self.load_bg_btn, self.refresh_btn, self.demo_btn, 
                      self.clear_bg_btn, self.dark_mode_btn]:
            button.setStyleSheet(button_style)
        
        # Apply other widget styles
        self.slider_label.setStyleSheet(theme_manager.get_text_label_style())
        self.opacity_label.setStyleSheet(theme_manager.get_text_label_style())
        self.opacity_slider.setStyleSheet(theme_manager.get_slider_style())
        
        # Apply explorer widget styles
        self.dir_combo.setStyleSheet(theme_manager.get_combo_box_style())
        self.file_tree.setStyleSheet(theme_manager.get_tree_view_style())
        self.selected_file_label.setStyleSheet(theme_manager.get_small_label_style())
        
        # Apply placeholder styles
        self.info_label.setStyleSheet(theme_manager.get_label_style())
        self.placeholder_content.setStyleSheet(theme_manager.get_placeholder_content_style())
    
    
    def change_directory(self, text):
        """Change the file explorer directory"""
        current_data = self.dir_combo.currentData()
        if current_data and os.path.exists(current_data):
            self.file_model.setRootPath(current_data)
            self.file_tree.setRootIndex(self.file_model.index(current_data))
            self.selected_file_label.setText("No file selected")
    
    def file_selected(self, index):
        """Handle file selection in the tree view"""
        file_path = self.file_model.filePath(index)
        file_info = QFileInfo(file_path)
        
        if file_info.isFile():
            file_name = file_info.fileName()
            file_size = file_info.size()
            
            # Format file size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            self.selected_file_label.setText(f"Selected: {file_name}\nSize: {size_str}")
            
            # If it's a text file, load it into the Monaco editor
            text_extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.cpp', '.c', '.h', '.java']
            if any(file_name.lower().endswith(ext) for ext in text_extensions):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) < 50000:  # Only load reasonably sized files
                            self.monaco_editor.set_content(content)
                            self.monaco_editor.detect_language_from_filename(file_name)
                        else:
                            self.monaco_editor.set_content(f"# File too large to display ({size_str})")
                            self.monaco_editor.set_language("plaintext")
                except Exception as e:
                    self.monaco_editor.set_content(f"# Error reading file: {str(e)}")
                    self.monaco_editor.set_language("plaintext")
        else:
            self.selected_file_label.setText(f"Directory: {file_info.fileName()}")

    
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
    
    def clear_background(self):
        self.central_widget.set_background_image(None)
    
    def update_background_opacity(self, value):
        opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.central_widget.set_background_opacity(opacity)
    
    
    def load_demo_content(self):
        demo_content = '''# Monaco Editor Demo
# This is a demonstration of the Monaco Editor integration

def fibonacci(n):
    """Calculate the nth Fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")

# Try editing this code!
# The editor supports:
# - Syntax highlighting
# - Code completion
# - Error detection
# - Multiple languages

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        self.result += value
        return self
    
    def multiply(self, value):
        self.result *= value
        return self
    
    def get_result(self):
        return self.result

# Method chaining example
calc = Calculator()
result = calc.add(5).multiply(3).add(2).get_result()
print(f"Result: {result}")
'''
        self.monaco_editor.set_content(demo_content)
        self.monaco_editor.set_language("python")
    
    def refresh_webview(self):
        # Reset Monaco editor to initial content
        self.monaco_editor.set_content("# Welcome to Monaco Editor\nprint('Hello World!')")
        self.monaco_editor.set_language("python")


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
