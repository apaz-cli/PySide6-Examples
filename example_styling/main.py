import sys
import os
from PySide6.QtCore import Qt, QUrl, QTimer, QDir, QFileInfo
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QGroupBox, QSlider, QFileDialog, QTreeView, QComboBox,
                               QFileSystemModel)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPalette, QBrush, QPixmap, QPainter, QLinearGradient, QColor
from monaco_widget import MonacoEditorWidget


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
        
        # Content area with file explorer, webview and native widget
        content_layout = QHBoxLayout()
        
        # File Explorer section
        self.explorer_group = QGroupBox("File Explorer")
        self.explorer_group.setObjectName("explorer_group")
        self.explorer_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 120);
                border: 2px solid #9b59b6;
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
        explorer_layout = QVBoxLayout()
        
        # Directory dropdown
        self.dir_combo = QComboBox()
        self.dir_combo.addItem("Current Directory", os.getcwd())
        self.dir_combo.addItem("Home Directory", os.path.expanduser("~"))
        self.dir_combo.addItem("Root Directory", "/")
        self.dir_combo.currentTextChanged.connect(self.change_directory)
        self.dir_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                color: #2c3e50;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        
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
        self.file_tree.setStyleSheet("""
            QTreeView {
                background-color: rgba(255, 255, 255, 80);
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 12px;
                color: #2c3e50;
            }
            QTreeView::item {
                padding: 2px;
            }
            QTreeView::item:selected {
                background-color: rgba(74, 144, 226, 0.3);
            }
            QTreeView::item:hover {
                background-color: rgba(74, 144, 226, 0.1);
            }
        """)
        
        # Selected file label
        self.selected_file_label = QLabel("No file selected")
        self.selected_file_label.setWordWrap(True)
        self.selected_file_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 11px;
                padding: 5px;
                background-color: rgba(255, 255, 255, 60);
                border-radius: 3px;
            }
        """)
        
        explorer_layout.addWidget(QLabel("Directory:"))
        explorer_layout.addWidget(self.dir_combo)
        explorer_layout.addWidget(self.file_tree)
        explorer_layout.addWidget(self.selected_file_label)
        self.explorer_group.setLayout(explorer_layout)
        
        # Monaco Editor section
        self.editor_group = QGroupBox("Monaco Editor")
        self.editor_group.setObjectName("editor_group")
        self.editor_group.setStyleSheet("""
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
        editor_layout = QVBoxLayout()
        
        self.monaco_editor = MonacoEditorWidget()
        self.monaco_editor.content_changed.connect(self.on_editor_content_changed)
        self.monaco_editor.set_language("python")
        self.monaco_editor.set_content("# Welcome to Monaco Editor\nprint('Hello World!')")
        
        editor_layout.addWidget(self.monaco_editor)
        self.editor_group.setLayout(editor_layout)
        
        # Placeholder section
        self.placeholder_group = QGroupBox("Placeholder Panel")
        self.placeholder_group.setObjectName("placeholder_group")
        self.placeholder_group.setStyleSheet("""
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
        placeholder_layout = QVBoxLayout()
        
        info_label = QLabel("This is a placeholder panel.\nFuture functionality will be added here.")
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
        
        placeholder_content = QLabel("Reserved for future features...")
        placeholder_content.setAlignment(Qt.AlignCenter)
        placeholder_content.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
                font-style: italic;
                padding: 20px;
                background-color: rgba(255, 255, 255, 50);
                border: 2px dashed #bdc3c7;
                border-radius: 5px;
            }
        """)
        
        placeholder_layout.addWidget(info_label)
        placeholder_layout.addWidget(placeholder_content)
        placeholder_layout.addStretch()
        self.placeholder_group.setLayout(placeholder_layout)
        
        # Add to content layout
        content_layout.addWidget(self.explorer_group, 1)
        content_layout.addWidget(self.editor_group, 2)
        content_layout.addWidget(self.placeholder_group, 1)
        
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
            group_style_explorer = """
                QGroupBox {
                    background-color: rgba(44, 62, 80, 120);
                    border: 2px solid #9b59b6;
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
            group_style_editor = """
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
            group_style_placeholder = """
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
            
            combo_style = """
                QComboBox {
                    background-color: rgba(52, 73, 94, 100);
                    border: 1px solid #7f8c8d;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 12px;
                    color: #ecf0f1;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
            """
            
            tree_style = """
                QTreeView {
                    background-color: rgba(52, 73, 94, 80);
                    border: 1px solid #7f8c8d;
                    border-radius: 5px;
                    font-size: 12px;
                    color: #ecf0f1;
                }
                QTreeView::item {
                    padding: 2px;
                }
                QTreeView::item:selected {
                    background-color: rgba(52, 152, 219, 0.3);
                }
                QTreeView::item:hover {
                    background-color: rgba(52, 152, 219, 0.1);
                }
            """
            
            file_label_style = """
                QLabel {
                    color: #ecf0f1;
                    font-size: 11px;
                    padding: 5px;
                    background-color: rgba(44, 62, 80, 60);
                    border-radius: 3px;
                }
            """
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
            group_style_explorer = """
                QGroupBox {
                    background-color: rgba(255, 255, 255, 120);
                    border: 2px solid #9b59b6;
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
            group_style_editor = """
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
            group_style_placeholder = """
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
            
            combo_style = """
                QComboBox {
                    background-color: rgba(255, 255, 255, 100);
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 12px;
                    color: #2c3e50;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
            """
            
            tree_style = """
                QTreeView {
                    background-color: rgba(255, 255, 255, 80);
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    font-size: 12px;
                    color: #2c3e50;
                }
                QTreeView::item {
                    padding: 2px;
                }
                QTreeView::item:selected {
                    background-color: rgba(74, 144, 226, 0.3);
                }
                QTreeView::item:hover {
                    background-color: rgba(74, 144, 226, 0.1);
                }
            """
            
            file_label_style = """
                QLabel {
                    color: #2c3e50;
                    font-size: 11px;
                    padding: 5px;
                    background-color: rgba(255, 255, 255, 60);
                    border-radius: 3px;
                }
            """
        
        # Find and update all widgets
        self.controls_group.setStyleSheet(group_style_controls)
        self.explorer_group.setStyleSheet(group_style_explorer)
        self.editor_group.setStyleSheet(group_style_editor)
        self.placeholder_group.setStyleSheet(group_style_placeholder)
        
        # Update other widgets
        self.slider_label.setStyleSheet(slider_label_style)
        self.opacity_label.setStyleSheet(slider_label_style)
        self.info_label.setStyleSheet(label_style)
        
        self.opacity_slider.setStyleSheet(slider_style)
        self.status_label.setStyleSheet(status_style)
        
        # Update explorer widgets
        self.dir_combo.setStyleSheet(combo_style)
        self.file_tree.setStyleSheet(tree_style)
        self.selected_file_label.setStyleSheet(file_label_style)
        
        # Update Monaco editor theme
        self.apply_dark_mode_to_editor()
    
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

    def apply_dark_mode_to_editor(self):
        if self.dark_mode:
            self.monaco_editor.set_theme('vs-dark')
        else:
            self.monaco_editor.set_theme('vs')
    
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
