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
    A reusable Monaco Editor widget for PySide6 applications.
    
    Signals:
        content_changed(str): Emitted when the editor content changes
        editor_ready(): Emitted when the editor is fully loaded and ready
    """
    
    # Expose signals from the interface
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
            # Look for monaco-editor in same directory as this file
            self.monaco_path = Path(__file__).parent / "monaco-editor"
        
        # Verify Monaco Editor exists
        if not self._verify_monaco_installation():
            return
        
        # Create the Monaco interface
        self.monaco_interface = MonacoInterface()
        
        # Connect signals
        self.monaco_interface.content_changed.connect(self.content_changed.emit)
        self.monaco_interface.editor_ready.connect(self.editor_ready.emit)
        
        # Set up the widget
        self._setup_ui()
        self._create_monaco_html()
    
    def _verify_monaco_installation(self):
        """Verify that Monaco Editor is properly installed"""
        if not self.monaco_path.exists():
            self._show_setup_error("Monaco Editor folder not found", 
                                 f"Expected location: {self.monaco_path}")
            return False
        
        loader_path = self.monaco_path / "min" / "vs" / "loader.js"
        if not loader_path.exists():
            self._show_setup_error("Monaco Editor files incomplete", 
                                 f"Missing: {loader_path}")
            return False
        
        return True
    
    def _show_setup_error(self, title, message):
        """Show setup error message"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText("Monaco Editor setup required!")
        msg.setInformativeText(
            f"{message}\n\n"
            "To fix this:\n"
            "1. Download Monaco Editor from: https://github.com/microsoft/monaco-editor/releases\n"
            "2. Extract to 'monaco-editor' folder\n"
            "3. Ensure structure: monaco-editor/min/vs/loader.js"
        )
        msg.exec()
    
    def _setup_ui(self):
        """Set up the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Web view for Monaco Editor
        self.web_view = QWebEngineView()
        self.web_view.page().setBackgroundColor(Qt.transparent)
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)
        self.web_view.setStyleSheet("background: transparent;")
        layout.addWidget(self.web_view)
    
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
        html_file = Path(__file__).parent / "monaco_editor_widget.html"
        monaco_abs_path = self.monaco_path.resolve().as_posix()
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monaco Editor Widget</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        #container {{
            width: 100vw;
            height: 100vh;
        }}
        .loading {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #666;
            gap: 20px;
        }}
        .spinner {{
            width: 30px;
            height: 30px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007acc;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="container">
        <div class="loading">
            <div class="spinner"></div>
            <div>Loading Monaco Editor...</div>
        </div>
    </div>
    
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        let editor;
        let monacoInterface;
        
        // Initialize Qt Web Channel
        new QWebChannel(qt.webChannelTransport, function(channel) {{
            monacoInterface = channel.objects.monaco_interface;
        }});
        
        // Load Monaco Editor
        async function initMonaco() {{
            try {{
                // Load Monaco loader
                await loadScript('file:///{monaco_abs_path}/min/vs/loader.js');
                
                // Configure require paths
                require.config({{ 
                    paths: {{ 
                        'vs': 'file:///{monaco_abs_path}/min/vs' 
                    }}
                }});
                
                // Load Monaco editor
                require(['vs/editor/editor.main'], function() {{
                    // Clear loading message
                    document.getElementById('container').innerHTML = '';
                    
                    // Define transparent themes
                    monaco.editor.defineTheme('transparent-dark', {{
                        base: 'vs-dark',
                        inherit: true,
                        rules: [],
                        colors: {{
                            'editor.background': '#00000000',
                            'editor.lineHighlightBackground': '#ffffff08',
                            'editorLineNumber.foreground': '#858585',
                            'editorGutter.background': '#00000000',
                            'editorWidget.background': '#2d2d30cc',
                            'editorSuggestWidget.background': '#2d2d30cc',
                            'editorHoverWidget.background': '#2d2d30cc',
                            'scrollbar.shadow': '#00000000',
                            'scrollbarSlider.background': '#79797966',
                            'scrollbarSlider.hoverBackground': '#646464b3',
                            'scrollbarSlider.activeBackground': '#bfbfbf66',
                            'minimap.background': '#00000000',
                            'minimapSlider.background': '#79797966',
                            'minimapSlider.hoverBackground': '#646464b3',
                            'minimapSlider.activeBackground': '#bfbfbf66'
                        }}
                    }});
                    
                    monaco.editor.defineTheme('transparent-light', {{
                        base: 'vs',
                        inherit: true,
                        rules: [],
                        colors: {{
                            'editor.background': '#00000000',
                            'editor.lineHighlightBackground': '#00000008',
                            'editorLineNumber.foreground': '#237893',
                            'editorGutter.background': '#00000000',
                            'editorWidget.background': '#f3f3f3cc',
                            'editorSuggestWidget.background': '#f3f3f3cc',
                            'editorHoverWidget.background': '#f3f3f3cc',
                            'scrollbar.shadow': '#00000000',
                            'scrollbarSlider.background': '#64646466',
                            'scrollbarSlider.hoverBackground': '#646464b3',
                            'scrollbarSlider.activeBackground': '#00000066',
                            'minimap.background': '#00000000',
                            'minimapSlider.background': '#64646466',
                            'minimapSlider.hoverBackground': '#646464b3',
                            'minimapSlider.activeBackground': '#00000066'
                        }}
                    }});
                    
                    // Create editor
                    editor = monaco.editor.create(document.getElementById('container'), {{
                        value: '',
                        language: 'javascript',
                        theme: 'transparent-dark',
                        automaticLayout: true,
                        fontSize: 14,
                        minimap: {{ enabled: true }},
                        scrollBeyondLastLine: false,
                        wordWrap: 'on',
                        lineNumbers: 'on',
                        folding: true,
                        formatOnPaste: true,
                        formatOnType: true,
                        renderWhitespace: 'selection',
                        mouseWheelZoom: true
                    }});
                    
                    // Listen for content changes
                    editor.onDidChangeModelContent(function() {{
                        if (monacoInterface) {{
                            const content = editor.getValue();
                            monacoInterface.update_content(content);
                        }}
                    }});
                    
                    // Notify that editor is ready
                    if (monacoInterface) {{
                        monacoInterface.editor_initialized();
                    }}
                    
                    // Focus the editor
                    editor.focus();
                }});
                
            }} catch (error) {{
                showError('Failed to load Monaco Editor', error.message);
            }}
        }}
        
        function loadScript(src) {{
            return new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
        }}
        
        function showError(title, message) {{
            document.getElementById('container').innerHTML = `
                <div class="loading">
                    <div style="color: #d32f2f;">${{title}}</div>
                    <div style="font-size: 12px; margin-top: 10px;">${{message}}</div>
                </div>`;
        }}
        
        // API functions called from Python
        function setEditorContent(content) {{
            if (editor) {{
                editor.setValue(content);
            }}
        }}
        
        function getEditorContent() {{
            return editor ? editor.getValue() : '';
        }}
        
        function setEditorLanguage(language) {{
            if (editor) {{
                const model = editor.getModel();
                monaco.editor.setModelLanguage(model, language);
            }}
        }}
        
        function setEditorTheme(theme) {{
            if (editor) {{
                monaco.editor.setTheme(theme);
            }}
        }}
        
        function setEditorOptions(options) {{
            if (editor) {{
                editor.updateOptions(options);
            }}
        }}
        
        function formatDocument() {{
            if (editor) {{
                editor.getAction('editor.action.formatDocument').run();
            }}
        }}
        
        function focusEditor() {{
            if (editor) {{
                editor.focus();
            }}
        }}
        
        function insertText(text) {{
            if (editor) {{
                const position = editor.getPosition();
                const range = new monaco.Range(
                    position.lineNumber, 
                    position.column, 
                    position.lineNumber, 
                    position.column
                );
                editor.executeEdits('insert-text', [{{
                    range: range,
                    text: text
                }}]);
            }}
        }}
        
        // Start initialization
        initMonaco();
    </script>
</body>
</html>'''
        
        # Write HTML file
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    # Public API methods
    
    def set_content(self, content):
        """
        Set the content of the editor.
        
        Args:
            content (str): The text content to set
        """
        if content is None:
            content = ""
        
        # Escape content for JavaScript
        escaped_content = content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
        self.web_view.page().runJavaScript(f"setEditorContent(`{escaped_content}`);")
    
    def get_content(self):
        """
        Get the current content of the editor.
        
        Returns:
            str: The current editor content
        """
        return self.monaco_interface.current_content
    
    def set_language(self, language):
        """
        Set the programming language for syntax highlighting.
        
        Args:
            language (str): Language identifier (e.g., 'python', 'javascript', 'html')
        """
        self.web_view.page().runJavaScript(f"setEditorLanguage('{language}');")
    
    def set_theme(self, theme):
        """
        Set the editor theme.
        
        Args:
            theme (str): Theme name ('vs', 'vs-dark', 'hc-black')
        """
        self.web_view.page().runJavaScript(f"setEditorTheme('{theme}');")
    
    def format_document(self):
        """Format the entire document using Monaco's formatter."""
        self.web_view.page().runJavaScript("formatDocument();")
    
    def focus(self):
        """Focus the editor."""
        self.web_view.page().runJavaScript("focusEditor();")
    
    def insert_text(self, text):
        """
        Insert text at the current cursor position.
        
        Args:
            text (str): Text to insert
        """
        escaped_text = text.replace('\\', '\\\\').replace("'", "\\'")
        self.web_view.page().runJavaScript(f"insertText('{escaped_text}');")
    
    def set_editor_options(self, **options):
        """
        Set editor options.
        
        Args:
            **options: Monaco editor options (fontSize, wordWrap, etc.)
        """
        import json
        options_json = json.dumps(options)
        self.web_view.page().runJavaScript(f"setEditorOptions({options_json});")
    
    def is_ready(self):
        """
        Check if the editor is ready to receive commands.
        
        Returns:
            bool: True if editor is ready
        """
        return self.monaco_interface.is_ready
    
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


class StyledMonacoWidget(QWidget):
    """Monaco Editor widget with integrated theming"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_theme()
    
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create Monaco editor
        self.monaco_editor = MonacoEditorWidget()
        
        # Check if Monaco is available
        if hasattr(self.monaco_editor, 'monaco_interface'):
            # Make the Monaco editor widget transparent
            self.monaco_editor.setAttribute(Qt.WA_TranslucentBackground)
            self.monaco_editor.setStyleSheet("background: transparent;")
            layout.addWidget(self.monaco_editor)
            self.editor_available = True
            # Wait for editor to be ready before applying theme
            self.monaco_editor.editor_ready.connect(self.on_editor_ready)
        else:
            # Fallback if Monaco is not available
            self.create_fallback_ui(layout)
            self.editor_available = False
            self.apply_theme()
    
    def create_fallback_ui(self, layout):
        """Create fallback UI when Monaco is not available"""
        fallback_label = QLabel("Monaco Editor not available")
        fallback_label.setAlignment(Qt.AlignCenter)
        fallback_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 14px;
                font-weight: bold;
                padding: 20px;
                background-color: rgba(255, 255, 255, 100);
                border: 2px dashed #e74c3c;
                border-radius: 10px;
            }
        """)
        
        info_label = QLabel(
            "To use Monaco Editor:\n"
            "1. Download from: https://github.com/microsoft/monaco-editor/releases\n"
            "2. Extract to 'monaco-editor' folder\n"
            "3. Ensure structure: monaco-editor/min/vs/loader.js"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
                padding: 10px;
                background-color: rgba(255, 255, 255, 80);
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(fallback_label)
        layout.addWidget(info_label)
        layout.addStretch()
    
    def connect_theme(self):
        """Connect to theme manager"""
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def on_editor_ready(self):
        """Called when Monaco editor is ready"""
        self.apply_theme()
        
        # Apply any pending content or language
        if hasattr(self, '_pending_content'):
            self.monaco_editor.set_content(self._pending_content)
            delattr(self, '_pending_content')
        
        if hasattr(self, '_pending_language'):
            self.monaco_editor.set_language(self._pending_language)
            delattr(self, '_pending_language')
    
    def apply_theme(self):
        """Apply current theme to the widget"""
        if self.editor_available and self.monaco_editor.is_ready():
            # Apply Monaco theme
            monaco_theme = theme_manager.get_monaco_theme()
            self.monaco_editor.set_theme(monaco_theme)
        elif not self.editor_available:
            # Update fallback UI styling
            colors = theme_manager.get_colors()
            fallback_style = f"""
                QLabel {{
                    color: {colors['accent']};
                    font-size: 14px;
                    font-weight: bold;
                    padding: 20px;
                    background-color: {colors['input_bg']};
                    border: 2px dashed {colors['accent']};
                    border-radius: 10px;
                }}
            """
            
            info_style = f"""
                QLabel {{
                    color: {colors['text_secondary']};
                    font-size: 12px;
                    padding: 10px;
                    background-color: {colors['background'].replace('120', '80')};
                    border-radius: 5px;
                }}
            """
            
            # Apply styles to fallback widgets
            for child in self.findChildren(QLabel):
                if "Monaco Editor not available" in child.text():
                    child.setStyleSheet(fallback_style)
                elif "To use Monaco Editor" in child.text():
                    child.setStyleSheet(info_style)
    
    # Proxy methods to Monaco editor
    def set_content(self, content):
        """Set editor content"""
        if self.editor_available and self.monaco_editor.is_ready():
            self.monaco_editor.set_content(content)
        elif self.editor_available:
            # Store content to set when ready
            self._pending_content = content
    
    def get_content(self):
        """Get editor content"""
        if self.editor_available:
            return self.monaco_editor.get_content()
        return ""
    
    def set_language(self, language):
        """Set editor language"""
        if self.editor_available and self.monaco_editor.is_ready():
            self.monaco_editor.set_language(language)
        elif self.editor_available:
            # Store language to set when ready
            self._pending_language = language
    
    def detect_language_from_filename(self, filename):
        """Detect and set language from filename"""
        if self.editor_available:
            return self.monaco_editor.detect_language_from_filename(filename)
        return "plaintext"
    
    def format_document(self):
        """Format the document"""
        if self.editor_available:
            self.monaco_editor.format_document()
    
    def focus(self):
        """Focus the editor"""
        if self.editor_available:
            self.monaco_editor.focus()
    
    def insert_text(self, text):
        """Insert text at cursor"""
        if self.editor_available:
            self.monaco_editor.insert_text(text)
    
    def is_ready(self):
        """Check if editor is ready"""
        if self.editor_available:
            return self.monaco_editor.is_ready()
        return False
    
    @property
    def content_changed(self):
        """Content changed signal"""
        if self.editor_available:
            return self.monaco_editor.content_changed
        # Return a dummy signal for fallback
        from PySide6.QtCore import Signal
        return Signal(str)
    
    @property
    def editor_ready(self):
        """Editor ready signal"""
        if self.editor_available:
            return self.monaco_editor.editor_ready
        # Return a dummy signal for fallback
        from PySide6.QtCore import Signal
        return Signal()
