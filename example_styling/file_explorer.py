"""
File Explorer Widget
A consolidated file explorer with directory navigation and file selection.
"""

import os
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QFileInfo
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QTreeView, QFileSystemModel, QGroupBox)
from theme_manager import theme_manager


class FileExplorer(QWidget):
    """Consolidated file explorer widget with theming support"""
    
    file_selected = Signal(str)  # Emitted when a file is selected
    content_ready = Signal(str, str)  # Emitted with (content, language) for text files
    
    # Supported text file extensions
    TEXT_EXTENSIONS = {
        '.txt': 'plaintext', '.py': 'python', '.js': 'javascript', 
        '.ts': 'typescript', '.html': 'html', '.htm': 'html',
        '.css': 'css', '.scss': 'scss', '.json': 'json', 
        '.xml': 'xml', '.md': 'markdown', '.sql': 'sql',
        '.cpp': 'cpp', '.c': 'cpp', '.h': 'cpp', '.java': 'java',
        '.cs': 'csharp', '.php': 'php', '.rb': 'ruby', '.go': 'go',
        '.rs': 'rust', '.swift': 'swift', '.kt': 'kotlin'
    }
    
    # Maximum file size to load (50KB)
    MAX_FILE_SIZE = 50000
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the file explorer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create group box
        self.group_box = QGroupBox("File Explorer")
        self.group_box.setObjectName("explorer_group")
        group_layout = QVBoxLayout()
        
        # Directory selection
        self.setup_directory_selector(group_layout)
        
        # File tree view
        self.setup_file_tree(group_layout)
        
        # File info display
        self.setup_file_info(group_layout)
        
        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)
    
    def setup_directory_selector(self, layout):
        """Setup directory selection dropdown"""
        layout.addWidget(QLabel("Directory:"))
        
        self.dir_combo = QComboBox()
        self.populate_directory_combo()
        layout.addWidget(self.dir_combo)
    
    def setup_file_tree(self, layout):
        """Setup file tree view"""
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(os.getcwd())
        
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(os.getcwd()))
        
        # Configure tree view appearance
        self.file_tree.setColumnWidth(0, 200)
        self.file_tree.hideColumn(1)  # Size
        self.file_tree.hideColumn(2)  # Type
        self.file_tree.hideColumn(3)  # Date
        self.file_tree.setHeaderHidden(True)
        
        layout.addWidget(self.file_tree)
    
    def setup_file_info(self, layout):
        """Setup file information display"""
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setWordWrap(True)
        layout.addWidget(self.file_info_label)
    
    def populate_directory_combo(self):
        """Populate directory combo box with common directories"""
        directories = [
            ("Current Directory", os.getcwd()),
            ("Home Directory", os.path.expanduser("~")),
            ("Root Directory", "/")
        ]
        
        for name, path in directories:
            self.dir_combo.addItem(name, path)
    
    def connect_signals(self):
        """Connect all signals"""
        self.dir_combo.currentTextChanged.connect(self.change_directory)
        self.file_tree.clicked.connect(self.on_file_clicked)
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def change_directory(self):
        """Change the current directory"""
        current_data = self.dir_combo.currentData()
        if current_data and os.path.exists(current_data):
            self.file_model.setRootPath(current_data)
            self.file_tree.setRootIndex(self.file_model.index(current_data))
            self.file_info_label.setText("No file selected")
    
    def on_file_clicked(self, index):
        """Handle file/directory selection"""
        file_path = self.file_model.filePath(index)
        file_info = QFileInfo(file_path)
        
        if file_info.isFile():
            self.handle_file_selection(file_path, file_info)
        else:
            self.handle_directory_selection(file_info)
    
    def handle_file_selection(self, file_path, file_info):
        """Handle file selection and loading"""
        file_name = file_info.fileName()
        file_size = file_info.size()
        size_str = self.format_file_size(file_size)
        
        # Update info display
        self.file_info_label.setText(f"Selected: {file_name}\nSize: {size_str}")
        
        # Emit file selected signal
        self.file_selected.emit(file_path)
        
        # Try to load text files
        if self.is_text_file(file_name) and file_size < self.MAX_FILE_SIZE:
            content, language = self.load_text_file(file_path, file_name)
            if content is not None:
                self.content_ready.emit(content, language)
    
    def handle_directory_selection(self, file_info):
        """Handle directory selection"""
        self.file_info_label.setText(f"Directory: {file_info.fileName()}")
    
    def is_text_file(self, filename):
        """Check if file is a supported text file"""
        return any(filename.lower().endswith(ext) for ext in self.TEXT_EXTENSIONS.keys())
    
    def get_language_for_file(self, filename):
        """Get Monaco language identifier for file"""
        ext = Path(filename).suffix.lower()
        return self.TEXT_EXTENSIONS.get(ext, 'plaintext')
    
    def load_text_file(self, file_path, filename):
        """Load text file content and determine language"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                language = self.get_language_for_file(filename)
                return content, language
        except Exception as e:
            error_content = f"# Error reading file: {str(e)}"
            return error_content, 'plaintext'
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def apply_theme(self):
        """Apply current theme to the widget"""
        self.group_box.setStyleSheet(theme_manager.get_widget_style('group_box', border_color='purple'))
        self.dir_combo.setStyleSheet(theme_manager.get_widget_style('input'))
        self.file_tree.setStyleSheet(theme_manager.get_widget_style('tree'))
        self.file_info_label.setStyleSheet(theme_manager.get_widget_style('label', font_size=8.0, padding=5, background_alpha=60))
    
    def get_selected_file(self):
        """Get currently selected file path"""
        current_index = self.file_tree.currentIndex()
        if current_index.isValid():
            return self.file_model.filePath(current_index)
        return None
    
    def set_root_directory(self, path):
        """Set the root directory programmatically"""
        if os.path.exists(path):
            self.file_model.setRootPath(path)
            self.file_tree.setRootIndex(self.file_model.index(path))
            
            # Update combo box if needed
            for i in range(self.dir_combo.count()):
                if self.dir_combo.itemData(i) == path:
                    self.dir_combo.setCurrentIndex(i)
                    break
