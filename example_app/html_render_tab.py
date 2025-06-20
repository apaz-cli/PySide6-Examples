"""
HTML Render Tab - HTML and CSS rendering with live preview
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSplitter, QPlainTextEdit, QFileDialog,
                               QMessageBox, QTextBrowser)
from PySide6.QtCore import Qt

# Try to import QWebEngineView for better HTML rendering
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False


class HTMLRenderTab(QWidget):
    """HTML rendering tab with live preview"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the HTML renderer interface"""
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load HTML File")
        load_btn.clicked.connect(self.load_html_file)
        load_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        
        save_btn = QPushButton("Save HTML File")
        save_btn.clicked.connect(self.save_html_file)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        reload_btn = QPushButton("Reload Preview")
        reload_btn.clicked.connect(self.reload_content)
        reload_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 8px;")
        
        sample_btn = QPushButton("Load Sample HTML")
        sample_btn.clicked.connect(self.load_sample_html)
        sample_btn.setStyleSheet("background-color: #9c27b0; color: white; font-weight: bold; padding: 8px;")
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_content)
        clear_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        
        controls_layout.addWidget(load_btn)
        controls_layout.addWidget(save_btn)
        controls_layout.addWidget(reload_btn)
        controls_layout.addWidget(sample_btn)
        controls_layout.addWidget(clear_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Engine info
        if not WEB_ENGINE_AVAILABLE:
            info_label = QLabel("⚠️ QWebEngineView not available. Using QTextBrowser for basic HTML rendering.")
            info_label.setStyleSheet("color: #ff9800; background-color: #fff3cd; padding: 8px; border-radius: 4px;")
            layout.addWidget(info_label)
        
        # Splitter for HTML input and rendered output
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # HTML input area
        input_widget = QWidget()
        input_layout = QVBoxLayout()
        
        input_header = QLabel("HTML + CSS Code:")
        input_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        input_layout.addWidget(input_header)
        
        self.html_input = QPlainTextEdit()
        self.html_input.setPlainText(self.get_sample_html())
        self.html_input.textChanged.connect(self.update_preview)
        self.html_input.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        
        input_layout.addWidget(self.html_input)
        input_widget.setLayout(input_layout)
        
        # Preview area
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        
        preview_header = QLabel("Live Preview:")
        preview_header.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        preview_layout.addWidget(preview_header)
        
        # Choose appropriate rendering widget
        if WEB_ENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
        else:
            # Fallback to QTextBrowser if WebEngine is not available
            self.web_view = QTextBrowser()
            
        self.web_view.setStyleSheet("border: 1px solid #ddd; border-radius: 4px;")
        preview_layout.addWidget(self.web_view)
        preview_widget.setLayout(preview_layout)
        
        splitter.addWidget(input_widget)
        splitter.addWidget(preview_widget)
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
        
        # Instructions
        instructions = QLabel("""
Instructions: Edit the HTML/CSS code on the left to see live preview on the right. 
Load sample HTML to see advanced CSS features, or start with your own code.
        """.strip())
        instructions.setStyleSheet("color: #666; font-style: italic; padding: 10px; background-color: #f9f9f9; border-radius: 4px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        self.setLayout(layout)
        
        # Initial load
        self.update_preview()
        
    def get_sample_html(self):
        """Get sample HTML with modern CSS features"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modern CSS Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(15px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.2);
            padding: 25px;
            margin: 20px 0;
            border-radius: 15px;
            border-left: 5px solid #ff6b6b;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
            border-left-color: #4ecdc4;
        }
        
        .btn {
            background: linear-gradient(45deg, #ff6b6b, #ff8e53);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }
        
        .btn:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        
        .grid-item {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .grid-item:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: scale(1.05);
        }
        
        .icon {
            font-size: 2.5em;
            margin-bottom: 15px;
            display: block;
        }
        
        .feature-text {
            font-size: 1.1em;
            margin-top: 10px;
            opacity: 0.9;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        .highlight {
            background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
            color: #333;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="pulse">🎨 Modern CSS Showcase</h1>
        
        <div class="card">
            <h2>Welcome to the HTML/CSS Renderer!</h2>
            <p>This demonstration showcases modern CSS features including:</p>
            <ul style="margin: 15px 0; padding-left: 20px;">
                <li><span class="highlight">Glassmorphism</span> effects with backdrop-filter</li>
                <li><span class="highlight">CSS Grid</span> and Flexbox layouts</li>
                <li><span class="highlight">Gradient backgrounds</span> and text effects</li>
                <li><span class="highlight">Smooth animations</span> and transitions</li>
                <li><span class="highlight">Modern shadows</span> and borders</li>
            </ul>
            <button class="btn">Interactive Button</button>
        </div>
        
        <div class="card">
            <h2>Feature Grid</h2>
            <div class="grid">
                <div class="grid-item">
                    <span class="icon">🌈</span>
                    <h3>Gradients</h3>
                    <p class="feature-text">Beautiful color transitions and gradient effects</p>
                </div>
                <div class="grid-item">
                    <span class="icon">✨</span>
                    <h3>Glassmorphism</h3>
                    <p class="feature-text">Frosted glass effects with backdrop blur</p>
                </div>
                <div class="grid-item">
                    <span class="icon">🎭</span>
                    <h3>Animations</h3>
                    <p class="feature-text">Smooth CSS transitions and keyframe animations</p>
                </div>
                <div class="grid-item">
                    <span class="icon">📱</span>
                    <h3>Responsive</h3>
                    <p class="feature-text">Mobile-first responsive grid layouts</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Edit and Experiment</h2>
            <p>Try modifying the CSS code to see real-time changes! You can:</p>
            <ul style="margin: 15px 0; padding-left: 20px;">
                <li>Change colors in the gradient backgrounds</li>
                <li>Modify transition durations and effects</li>
                <li>Add new CSS properties and see them applied</li>
                <li>Create your own custom styles</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
        
    def update_preview(self):
        """Update the preview with current HTML content"""
        html_content = self.html_input.toPlainText()
        try:
            self.web_view.setHtml(html_content)
        except Exception as e:
            print(f"Error updating preview: {e}")
            
    def load_html_file(self):
        """Load HTML content from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open HTML File", "", 
            "HTML Files (*.html *.htm);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.html_input.setPlainText(content)
                    QMessageBox.information(self, "Success", f"Loaded: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load file: {str(e)}")
                
    def save_html_file(self):
        """Save current HTML content to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save HTML File", "", 
            "HTML Files (*.html);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.html_input.toPlainText())
                    QMessageBox.information(self, "Success", f"Saved: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
                
    def reload_content(self):
        """Reload the preview content"""
        self.update_preview()
        QMessageBox.information(self, "Reloaded", "Preview has been reloaded.")
        
    def load_sample_html(self):
        """Load the sample HTML content"""
        self.html_input.setPlainText(self.get_sample_html())
        
    def clear_content(self):
        """Clear the HTML input"""
        reply = QMessageBox.question(
            self, "Clear Content", 
            "Are you sure you want to clear all HTML content?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.html_input.clear()