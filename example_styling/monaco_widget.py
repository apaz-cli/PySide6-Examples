"""
Styled Monaco Editor Widget
A Monaco Editor widget that integrates with the theme system.
"""

import os
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel
from theme_manager import theme_manager


class MonacoInterface(QObject):
    """Interface between Python and Monaco Editor JavaScript"""
    
    content_changed = Signal(str)
    editor_ready = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_content = ""
        self._editor_ready = False
    
    @Slot(str)
    def update_content(self, content):
        """Called from JavaScript when editor content changes"""
        self.current_content = content
        self.content_changed.emit(content)
    
    @Slot()
    def editor_initialized(self):
        """Called from JavaScript when editor is ready"""
        self._editor_ready = True
        self.editor_ready.emit()
    
    @property
    def is_ready(self):
        """Check if the editor is ready to receive commands"""
        return self._editor_ready


class MonacoEditorWidget(QWidget):
    """
    Monaco Editor widget with integrated theming and fallback support.
    
    Signals:
        content_changed(str): Emitted when the editor content changes
        editor_ready(): Emitted when the editor is fully loaded and ready
    """
    
    content_changed = Signal(str)
    editor_ready = Signal()
    
    def __init__(self, parent=None, monaco_path=None):
        """
        Initialize the Monaco Editor widget.
        
        Args:
            parent: Parent widget
            monaco_path: Path to monaco-editor folder (auto-detected if None)
        """
        super().__init__(parent)
        
        # Find Monaco Editor path
        if monaco_path:
            self.monaco_path = Path(monaco_path)
        else:
            self.monaco_path = Path(__file__).parent / "monaco-editor"
        
        # Check if Monaco is available
        self.editor_available = self._verify_monaco_installation()
        
        if self.editor_available:
            # Create the Monaco interface
            self.monaco_interface = MonacoInterface()
            
            # Connect signals
            self.monaco_interface.content_changed.connect(self.content_changed.emit)
            self.monaco_interface.editor_ready.connect(self.editor_ready.emit)
            self.monaco_interface.editor_ready.connect(self.on_editor_ready)
            
            # Set up Monaco UI
            self._setup_monaco_ui()
            self._create_monaco_html()
        else:
            # Set up fallback UI
            self._setup_fallback_ui()
        
        # Connect to theme manager
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def _verify_monaco_installation(self):
        """Verify that Monaco Editor is properly installed"""
        if not self.monaco_path.exists():
            return False
        
        loader_path = self.monaco_path / "min" / "vs" / "loader.js"
        return loader_path.exists()
    
    def on_editor_ready(self):
        """Called when Monaco editor is ready"""
        self.apply_theme()
        
        # Apply any pending content or language
        if hasattr(self, '_pending_content'):
            self.set_content(self._pending_content)
            delattr(self, '_pending_content')
        
        if hasattr(self, '_pending_language'):
            self.set_language(self._pending_language)
            delattr(self, '_pending_language')
    
    def apply_theme(self):
        """Apply current theme to the widget"""
        if self.editor_available and self.is_ready():
            # Apply Monaco theme
            monaco_theme = theme_manager.get_monaco_theme()
            self.set_theme(monaco_theme)
        elif not self.editor_available:
            # Update fallback UI styling
            colors = theme_manager.get_colors()
            self.fallback_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['accent']};
                    font-size: 14px;
                    font-weight: bold;
                    padding: 20px;
                    background-color: {colors['input_bg']};
                    border: 2px dashed {colors['accent']};
                    border-radius: 10px;
                }}
            """)
            
            self.info_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text_secondary']};
                    font-size: 12px;
                    padding: 10px;
                    background-color: {colors['background'].replace('120', '80')};
                    border-radius: 5px;
                }}
            """)
    
    def _setup_monaco_ui(self):
        """Set up Monaco editor UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Web view for Monaco Editor
        self.web_view = QWebEngineView()
        self.web_view.page().setBackgroundColor(Qt.transparent)
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)
        self.web_view.setStyleSheet("background: transparent;")
        
        # Make widget transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        layout.addWidget(self.web_view)
    
    def _setup_fallback_ui(self):
        """Set up fallback UI when Monaco is not available"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.fallback_label = QLabel("Monaco Editor not available")
        self.fallback_label.setAlignment(Qt.AlignCenter)
        
        self.info_label = QLabel(
            "To use Monaco Editor:\n"
            "1. Download from: https://github.com/microsoft/monaco-editor/releases\n"
            "2. Extract to 'monaco-editor' folder\n"
            "3. Ensure structure: monaco-editor/min/vs/loader.js"
        )
        self.info_label.setWordWrap(True)
        
        layout.addWidget(self.fallback_label)
        layout.addWidget(self.info_label)
        layout.addStretch()
    
    def _create_monaco_html(self):
        """Create and load the Monaco Editor HTML"""
        html_file = self._create_html_file()
        
        # Set up web channel
        self.web_channel = QWebChannel()
        self.web_channel.registerObject("monaco_interface", self.monaco_interface)
        self.web_view.page().setWebChannel(self.web_channel)
        
        # Load the HTML file
        self.web_view.load(QUrl.fromLocalFile(str(html_file.resolve())))
    
    def _create_html_file(self):
        """Create the HTML file for Monaco Editor"""
        template_file = Path(__file__).parent / "monaco_template.html"
        html_file = Path(__file__).parent / "monaco_editor_widget.html"
        monaco_abs_path = self.monaco_path.resolve().as_posix()
        
        # Read template and replace placeholder
        with open(template_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Replace placeholders
        html_content = html_content.replace('MONACO_PATH_PLACEHOLDER', f'file:///{monaco_abs_path}')
        initial_theme = theme_manager.get_monaco_theme()
        html_content = html_content.replace('INITIAL_THEME_PLACEHOLDER', initial_theme)
        
        # Write HTML file
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    # Public API methods
    
    def set_content(self, content):
        """Set the content of the editor"""
        if not self.editor_available:
            return
        
        if content is None:
            content = ""
        
        if self.is_ready():
            # Escape content for JavaScript
            escaped_content = content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
            self.web_view.page().runJavaScript(f"setEditorContent(`{escaped_content}`);")
        else:
            # Store content to set when ready
            self._pending_content = content
    
    def get_content(self):
        """Get the current content of the editor"""
        if self.editor_available:
            return self.monaco_interface.current_content
        return ""
    
    def set_language(self, language):
        """Set the programming language for syntax highlighting"""
        if not self.editor_available:
            return
        
        if self.is_ready():
            self.web_view.page().runJavaScript(f"setEditorLanguage('{language}');")
        else:
            # Store language to set when ready
            self._pending_language = language
    
    def set_theme(self, theme):
        """Set the editor theme"""
        if self.editor_available and self.is_ready():
            self.web_view.page().runJavaScript(f"setEditorTheme('{theme}');")
    
    def format_document(self):
        """Format the entire document using Monaco's formatter"""
        if self.editor_available:
            self.web_view.page().runJavaScript("formatDocument();")
    
    def focus(self):
        """Focus the editor"""
        if self.editor_available:
            self.web_view.page().runJavaScript("focusEditor();")
    
    def insert_text(self, text):
        """Insert text at the current cursor position"""
        if self.editor_available:
            escaped_text = text.replace('\\', '\\\\').replace("'", "\\'")
            self.web_view.page().runJavaScript(f"insertText('{escaped_text}');")
    
    def set_editor_options(self, **options):
        """Set editor options"""
        if self.editor_available:
            import json
            options_json = json.dumps(options)
            self.web_view.page().runJavaScript(f"setEditorOptions({options_json});")
    
    def is_ready(self):
        """Check if the editor is ready to receive commands"""
        if self.editor_available:
            return self.monaco_interface.is_ready
        return False
    
    def detect_language_from_filename(self, filename):
        """
        Detect and set language based on file extension.
        
        Args:
            filename (str): Filename to detect language from
        """
        ext = Path(filename).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.java': 'java',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.txt': 'plaintext'
        }
        
        language = language_map.get(ext, 'plaintext')
        self.set_language(language)
        return language
    
    def cleanup(self):
        """Clean up temporary files (call when widget is destroyed)"""
        html_file = Path(__file__).parent / "monaco_editor_widget.html"
        if html_file.exists():
            try:
                html_file.unlink()
            except:
                pass  # Ignore cleanup errors
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup()
        super().closeEvent(event)


# Merge StyledMonacoWidget functionality into MonacoEditorWidget
