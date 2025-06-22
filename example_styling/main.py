import sys
import os
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QGroupBox, QSlider, QFileDialog)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPalette, QBrush, QPixmap, QPainter, QLinearGradient, QColor


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
        painter.setOpacity(1.0 - self.background_opacity)
        if self.dark_mode:
            # In dark mode, use a dark overlay instead of white
            painter.fillRect(self.rect(), QBrush(QColor(30, 30, 30)))
        else:
            painter.fillRect(self.rect(), QBrush(Qt.white))
        
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
        
        # Track dark mode state
        self.dark_mode = False
        
        # Create custom central widget with background support
        self.central_widget = TransparentWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Top controls section
        self.controls_group = QGroupBox("Native Qt Controls")
        self.controls_group.setObjectName("controls_group")
        self.controls_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 150);
                border: 2px solid #4a90e2;
                border-radius: 10px;
                padding-top: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 10px;
                color: #2c3e50;
            }
        """)
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
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        self.style_button(self.dark_mode_btn)
        
        button_layout.addWidget(self.load_bg_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.demo_btn)
        button_layout.addWidget(self.clear_bg_btn)
        button_layout.addWidget(self.dark_mode_btn)
        button_layout.addStretch()
        
        # Opacity slider
        slider_layout = QHBoxLayout()
        self.slider_label = QLabel("Background Opacity:")
        self.slider_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(self.update_background_opacity)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #ddd;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a90e2;
                width: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
        """)
        self.opacity_label = QLabel("70%")
        self.opacity_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        slider_layout.addWidget(self.slider_label)
        slider_layout.addWidget(self.opacity_slider)
        slider_layout.addWidget(self.opacity_label)
        slider_layout.addStretch()
        
        controls_layout.addLayout(button_layout)
        controls_layout.addLayout(slider_layout)
        self.controls_group.setLayout(controls_layout)
        
        # Content area with webview and native widget
        content_layout = QHBoxLayout()
        
        # WebView section
        self.webview_group = QGroupBox("Web Content")
        self.webview_group.setObjectName("webview_group")
        self.webview_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 120);
                border: 2px solid #27ae60;
                border-radius: 10px;
                padding-top: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 10px;
                color: #2c3e50;
            }
        """)
        webview_layout = QVBoxLayout()
        
        self.webview = StyledWebView()
        self.load_initial_content()
        
        webview_layout.addWidget(self.webview)
        self.webview_group.setLayout(webview_layout)
        
        # Native Qt widget section
        self.native_group = QGroupBox("Native Qt Widget")
        self.native_group.setObjectName("native_group")
        self.native_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 120);
                border: 2px solid #e74c3c;
                border-radius: 10px;
                padding-top: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 10px;
                color: #2c3e50;
            }
        """)
        native_layout = QVBoxLayout()
        
        info_label = QLabel("This is a native Qt widget area.\nNotice how the background image shows through both sections!")
        info_label.setWordWrap(True)
        self.info_label = info_label  # Store reference
        info_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 13px;
                padding: 10px;
                background-color: rgba(255, 255, 255, 80);
                border-radius: 5px;
            }
        """)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type something here...")
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
                color: #2c3e50;
            }
        """)
        
        native_layout.addWidget(info_label)
        native_layout.addWidget(self.text_edit)
        self.native_group.setLayout(native_layout)
        
        # Add to content layout
        content_layout.addWidget(self.webview_group, 2)
        content_layout.addWidget(self.native_group, 1)
        
        # Add all to main layout
        main_layout.addWidget(self.controls_group)
        main_layout.addLayout(content_layout)
        
        # Status label
        self.status_label = QLabel("Background: Default gradient")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 5px;
                background-color: rgba(255, 255, 255, 120);
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.status_label)
    
    def style_button(self, button):
        if self.dark_mode:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: #ecf0f1;
                    border: 1px solid #7f8c8d;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2c3e50;
                    border-color: #95a5a6;
                }
                QPushButton:pressed {
                    background-color: #1a252f;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #357abd;
                }
                QPushButton:pressed {
                    background-color: #2968a3;
                }
            """)
    
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.central_widget.dark_mode = self.dark_mode
        self.central_widget.update()  # Trigger repaint
        
        # Update button text and icon
        if self.dark_mode:
            self.dark_mode_btn.setText("☀️ Light Mode")
        else:
            self.dark_mode_btn.setText("🌙 Dark Mode")
        
        # Update all button styles
        for button in [self.load_bg_btn, self.refresh_btn, self.demo_btn, 
                      self.clear_bg_btn, self.dark_mode_btn]:
            self.style_button(button)
        
        # Update group box styles
        if self.dark_mode:
            group_style_controls = """
                QGroupBox {
                    background-color: rgba(44, 62, 80, 150);
                    border: 2px solid #3498db;
                    border-radius: 10px;
                    padding-top: 20px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #ecf0f1;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    padding: 0 10px;
                    color: #ecf0f1;
                }
            """
            group_style_webview = """
                QGroupBox {
                    background-color: rgba(44, 62, 80, 120);
                    border: 2px solid #2ecc71;
                    border-radius: 10px;
                    padding-top: 20px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #ecf0f1;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    padding: 0 10px;
                    color: #ecf0f1;
                }
            """
            group_style_native = """
                QGroupBox {
                    background-color: rgba(44, 62, 80, 120);
                    border: 2px solid #e74c3c;
                    border-radius: 10px;
                    padding-top: 20px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #ecf0f1;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    padding: 0 10px;
                    color: #ecf0f1;
                }
            """
            label_style = """
                QLabel {
                    color: #ecf0f1;
                    font-size: 13px;
                    padding: 10px;
                    background-color: rgba(52, 73, 94, 80);
                    border-radius: 5px;
                }
            """
            text_edit_style = """
                QTextEdit {
                    background-color: rgba(52, 73, 94, 100);
                    border: 1px solid #7f8c8d;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 13px;
                    color: #ecf0f1;
                }
            """
            slider_style = """
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #34495e;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #3498db;
                    width: 20px;
                    margin: -6px 0;
                    border-radius: 10px;
                }
            """
            status_style = """
                QLabel {
                    color: #ecf0f1;
                    font-size: 12px;
                    padding: 5px;
                    background-color: rgba(44, 62, 80, 120);
                    border-radius: 3px;
                }
            """
            slider_label_style = "color: #ecf0f1; font-weight: bold;"
        else:
            group_style_controls = """
                QGroupBox {
                    background-color: rgba(255, 255, 255, 150);
                    border: 2px solid #4a90e2;
                    border-radius: 10px;
                    padding-top: 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    padding: 0 10px;
                    color: #2c3e50;
                }
            """
            group_style_webview = """
                QGroupBox {
                    background-color: rgba(255, 255, 255, 120);
                    border: 2px solid #27ae60;
                    border-radius: 10px;
                    padding-top: 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    padding: 0 10px;
                    color: #2c3e50;
                }
            """
            group_style_native = """
                QGroupBox {
                    background-color: rgba(255, 255, 255, 120);
                    border: 2px solid #e74c3c;
                    border-radius: 10px;
                    padding-top: 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    padding: 0 10px;
                    color: #2c3e50;
                }
            """
            label_style = """
                QLabel {
                    color: #2c3e50;
                    font-size: 13px;
                    padding: 10px;
                    background-color: rgba(255, 255, 255, 80);
                    border-radius: 5px;
                }
            """
            text_edit_style = """
                QTextEdit {
                    background-color: rgba(255, 255, 255, 100);
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 13px;
                    color: #2c3e50;
                }
            """
            slider_style = """
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #ddd;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #4a90e2;
                    width: 20px;
                    margin: -6px 0;
                    border-radius: 10px;
                }
            """
            status_style = """
                QLabel {
                    color: #2c3e50;
                    font-size: 12px;
                    padding: 5px;
                    background-color: rgba(255, 255, 255, 120);
                    border-radius: 3px;
                }
            """
            slider_label_style = "color: #2c3e50; font-weight: bold;"
        
        # Find and update all widgets
        self.controls_group.setStyleSheet(group_style_controls)
        self.webview_group.setStyleSheet(group_style_webview)
        self.native_group.setStyleSheet(group_style_native)
        
        # Update other widgets
        self.slider_label.setStyleSheet(slider_label_style)
        self.opacity_label.setStyleSheet(slider_label_style)
        self.info_label.setStyleSheet(label_style)
        
        self.text_edit.setStyleSheet(text_edit_style)
        self.opacity_slider.setStyleSheet(slider_style)
        self.status_label.setStyleSheet(status_style)
        
        # Update webview content with dark mode
        self.apply_dark_mode_to_webview()
    
    def apply_dark_mode_to_webview(self):
        if self.dark_mode:
            dark_css = """
                body { 
                    background-color: transparent !important; 
                    color: #ecf0f1 !important;
                }
                .container, .card { 
                    background-color: rgba(44, 62, 80, 0.6) !important;
                    color: #ecf0f1 !important;
                }
                h1, h2 { 
                    color: #3498db !important; 
                }
                .highlight { 
                    background-color: rgba(52, 152, 219, 0.3) !important; 
                }
                button {
                    background-color: #2ecc71 !important;
                    color: white !important;
                    border: 1px solid #27ae60 !important;
                }
                button:hover {
                    background-color: #27ae60 !important;
                }
                input[type="text"] {
                    background-color: rgba(52, 73, 94, 0.5) !important;
                    color: #ecf0f1 !important;
                    border-color: #7f8c8d !important;
                }
                .progress-bar {
                    background-color: rgba(127, 140, 141, 0.5) !important;
                }
                p {
                    color: #ecf0f1 !important;
                }
            """
        else:
            dark_css = """
                /* Reset to light mode by removing dark mode overrides */
                body { background-color: transparent !important; }
            """
        
        # Inject CSS into the webview
        script = f"""
            (function() {{
                var style = document.getElementById('dark-mode-style');
                if (!style) {{
                    style = document.createElement('style');
                    style.id = 'dark-mode-style';
                    document.head.appendChild(style);
                }}
                style.textContent = `{dark_css}`;
            }})();
        """
        self.webview.page().runJavaScript(script)
    
    def load_background(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.central_widget.set_background_image(pixmap)
                self.status_label.setText(f"Background: {os.path.basename(file_path)}")
            else:
                self.status_label.setText("Error: Could not load image")
    
    def clear_background(self):
        self.central_widget.set_background_image(None)
        self.status_label.setText("Background: Default gradient")
    
    def update_background_opacity(self, value):
        opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.central_widget.set_background_opacity(opacity)
    
    def load_initial_content(self):
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: transparent;
                    color: #2c3e50;
                }
                .container {
                    background-color: rgba(255, 255, 255, 0.6);
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #27ae60;
                    text-align: center;
                }
                p {
                    line-height: 1.6;
                }
                .highlight {
                    background-color: rgba(46, 204, 113, 0.3);
                    padding: 2px 6px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>WebView Content</h1>
                <p>This is content rendered in a <span class="highlight">QWebEngineView</span>.</p>
                <p>Notice how the background image shows through the semi-transparent areas!</p>
                <p>The styling is designed to complement the native Qt widgets.</p>
            </div>
        </body>
        </html>
        """
        self.webview.setHtml(html_content)
        # Apply dark mode if active
        if self.dark_mode:
            # Small delay to ensure content is loaded
            QTimer.singleShot(100, self.apply_dark_mode_to_webview)
    
    def load_demo_content(self):
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: transparent;
                    color: #2c3e50;
                }
                .card {
                    background-color: rgba(255, 255, 255, 0.65);
                    padding: 20px;
                    margin: 10px 0;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: transform 0.2s;
                }
                .card:hover {
                    transform: translateY(-5px);
                }
                h2 {
                    color: #4a90e2;
                    margin-top: 0;
                }
                button {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    margin: 5px;
                }
                button:hover {
                    background-color: #229954;
                }
                .progress-bar {
                    width: 100%;
                    height: 20px;
                    background-color: rgba(189, 195, 199, 0.5);
                    border-radius: 10px;
                    overflow: hidden;
                    margin: 10px 0;
                }
                .progress-fill {
                    height: 100%;
                    background-color: #3498db;
                    width: 75%;
                    transition: width 0.3s;
                }
                input[type="text"] {
                    padding: 8px;
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    margin: 5px;
                    background-color: rgba(255, 255, 255, 0.5);
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Interactive Demo</h2>
                <p>This demonstrates more complex web content with interactivity.</p>
                <button onclick="alert('Hello from WebView!')">Click Me!</button>
                <button onclick="changeProgress()">Change Progress</button>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress"></div>
                </div>
                <input type="text" placeholder="Type here to test transparency" style="width: 90%;">
            </div>
            
            <div class="card">
                <h2>Transparent Integration</h2>
                <p>The semi-transparent cards let the background show through,
                creating a unified look between web and native content.</p>
                <p style="background-color: rgba(52, 152, 219, 0.2); padding: 10px; border-radius: 5px;">
                    This paragraph has a semi-transparent blue background!
                </p>
            </div>
            
            <script>
                function changeProgress() {
                    const progress = document.getElementById('progress');
                    const random = Math.floor(Math.random() * 100);
                    progress.style.width = random + '%';
                }
            </script>
        </body>
        </html>
        """
        self.webview.setHtml(html_content)
        # Apply dark mode if active
        if self.dark_mode:
            QTimer.singleShot(100, self.apply_dark_mode_to_webview)
    
    def refresh_webview(self):
        self.webview.reload()
        # Reapply dark mode after reload
        if self.dark_mode:
            QTimer.singleShot(500, self.apply_dark_mode_to_webview)


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