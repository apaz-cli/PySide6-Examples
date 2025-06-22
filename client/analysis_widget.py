"""
Multi-language Code Analysis Widget
Provides AST parsing, bytecode disassembly, and analysis for multiple programming languages.
"""

from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit, QTextBrowser,
                               QLabel, QScrollArea)
from theme_manager import theme_manager
from api_client import AnalysisClient, AnalysisResult



class AnalysisWorker(QThread):
    """Worker thread for analysis operations"""
    analysis_complete = Signal(object)  # AnalysisResult
    
    def __init__(self, api_client, file_path, analyzer_type):
        super().__init__()
        self.api_client = api_client
        self.file_path = file_path
        self.analyzer_type = analyzer_type
    
    def run(self):
        result = self.api_client.analyze_file(self.file_path, self.analyzer_type)
        self.analysis_complete.emit(result)


class AnalysisWidget(QWidget):
    """Multi-language code analysis widget"""
    
    def __init__(self, api_client: AnalysisClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_file = None
        self.current_language = None
        self.worker = None
        self.server_available = False
        self.setup_ui()
        self.connect_signals()
        self.apply_theme()
        self.check_server_and_load_example()
    
    def setup_ui(self):
        """Setup the analysis UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status label
        self.status_label = QLabel("Checking analysis server...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Error message widget (hidden by default)
        self.error_widget = QLabel()
        self.error_widget.setWordWrap(True)
        self.error_widget.setAlignment(Qt.AlignCenter)
        self.error_widget.hide()
        layout.addWidget(self.error_widget)
        
        # Main tab widget for different languages
        self.main_tab_widget = QTabWidget()
        
        # Create language-specific tab widgets
        self.setup_python_language_tab()
        self.setup_cpp_language_tab()
        self.setup_rust_language_tab()
        self.setup_triton_language_tab()
        self.setup_cuda_language_tab()
        self.setup_hip_language_tab()
        
        layout.addWidget(self.main_tab_widget)
    
    def setup_python_language_tab(self):
        """Setup Python language tab with nested analysis tabs"""
        self.python_tab_widget = QTabWidget()
        
        # AST tab
        self.ast_text = QTextEdit()
        self.ast_text.setReadOnly(True)
        self.ast_text.setPlainText("Select a Python file to see its AST representation")
        self.python_tab_widget.addTab(self.ast_text, "🌳 AST")
        
        # Disassembly tab - custom rich bytecode display
        self.dis_text = QTextBrowser()
        self.dis_text.setPlainText("Select a Python file to see its bytecode disassembly")
        self.dis_text.setOpenExternalLinks(False)
        self.dis_text.anchorClicked.connect(self.handle_bytecode_link)
        self.python_tab_widget.addTab(self.dis_text, "⚙️ Bytecode")
        
        # Analysis tab
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlainText("Select a Python file to see bytecode analysis")
        self.python_tab_widget.addTab(self.analysis_text, "📊 Analysis")
        
        self.main_tab_widget.addTab(self.python_tab_widget, "🐍 Python")
    
    def setup_cpp_language_tab(self):
        """Setup C/C++ language tab with nested analysis tabs"""
        self.cpp_tab_widget = QTabWidget()
        
        # AST tab
        self.cpp_ast_text = QTextEdit()
        self.cpp_ast_text.setReadOnly(True)
        self.cpp_ast_text.setPlainText("Select a C/C++ file to see its AST representation")
        self.cpp_tab_widget.addTab(self.cpp_ast_text, "🌳 AST")
        
        # Assembly tab
        self.cpp_asm_text = QTextEdit()
        self.cpp_asm_text.setReadOnly(True)
        self.cpp_asm_text.setPlainText("Select a C/C++ file to see its assembly output")
        self.cpp_tab_widget.addTab(self.cpp_asm_text, "⚡ Assembly")
        
        # Analysis tab
        self.cpp_analysis_text = QTextEdit()
        self.cpp_analysis_text.setReadOnly(True)
        self.cpp_analysis_text.setPlainText("Select a C/C++ file to see static analysis")
        self.cpp_tab_widget.addTab(self.cpp_analysis_text, "📈 Analysis")
        
        self.main_tab_widget.addTab(self.cpp_tab_widget, "🔧 C/C++")
    
    def setup_rust_language_tab(self):
        """Setup Rust language tab with nested analysis tabs"""
        self.rust_tab_widget = QTabWidget()
        
        # HIR tab
        self.rust_hir_text = QTextEdit()
        self.rust_hir_text.setReadOnly(True)
        self.rust_hir_text.setPlainText("Select a Rust file to see its HIR representation")
        self.rust_tab_widget.addTab(self.rust_hir_text, "🏗️ HIR")
        
        # MIR tab
        self.rust_mir_text = QTextEdit()
        self.rust_mir_text.setReadOnly(True)
        self.rust_mir_text.setPlainText("Select a Rust file to see its MIR representation")
        self.rust_tab_widget.addTab(self.rust_mir_text, "🔩 MIR")
        
        # LLVM IR tab
        self.rust_llvm_text = QTextEdit()
        self.rust_llvm_text.setReadOnly(True)
        self.rust_llvm_text.setPlainText("Select a Rust file to see its LLVM IR")
        self.rust_tab_widget.addTab(self.rust_llvm_text, "⚙️ LLVM IR")
        
        # Analysis tab
        self.rust_analysis_text = QTextEdit()
        self.rust_analysis_text.setReadOnly(True)
        self.rust_analysis_text.setPlainText("Select a Rust file to see borrow checker analysis")
        self.rust_tab_widget.addTab(self.rust_analysis_text, "🔒 Borrow Check")
        
        self.main_tab_widget.addTab(self.rust_tab_widget, "🦀 Rust")
    
    def setup_triton_language_tab(self):
        """Setup Triton language tab with nested analysis tabs"""
        self.triton_tab_widget = QTabWidget()
        
        # Kernel AST tab
        self.triton_ast_text = QTextEdit()
        self.triton_ast_text.setReadOnly(True)
        self.triton_ast_text.setPlainText("Select a Triton file to see kernel AST")
        self.triton_tab_widget.addTab(self.triton_ast_text, "🌳 Kernel AST")
        
        # PTX tab
        self.triton_ptx_text = QTextEdit()
        self.triton_ptx_text.setReadOnly(True)
        self.triton_ptx_text.setPlainText("Select a Triton file to see generated PTX")
        self.triton_tab_widget.addTab(self.triton_ptx_text, "🎯 PTX")
        
        # Performance tab
        self.triton_perf_text = QTextEdit()
        self.triton_perf_text.setReadOnly(True)
        self.triton_perf_text.setPlainText("Select a Triton file to see performance analysis")
        self.triton_tab_widget.addTab(self.triton_perf_text, "📊 Performance")
        
        self.main_tab_widget.addTab(self.triton_tab_widget, "🚀 Triton")
    
    def setup_cuda_language_tab(self):
        """Setup CUDA language tab with nested analysis tabs"""
        self.cuda_tab_widget = QTabWidget()
        
        # Kernel AST tab
        self.cuda_ast_text = QTextEdit()
        self.cuda_ast_text.setReadOnly(True)
        self.cuda_ast_text.setPlainText("Select a CUDA file to see kernel AST")
        self.cuda_tab_widget.addTab(self.cuda_ast_text, "🌳 Kernel AST")
        
        # PTX tab
        self.cuda_ptx_text = QTextEdit()
        self.cuda_ptx_text.setReadOnly(True)
        self.cuda_ptx_text.setPlainText("Select a CUDA file to see generated PTX")
        self.cuda_tab_widget.addTab(self.cuda_ptx_text, "🎯 PTX")
        
        # SASS tab
        self.cuda_sass_text = QTextEdit()
        self.cuda_sass_text.setReadOnly(True)
        self.cuda_sass_text.setPlainText("Select a CUDA file to see SASS assembly")
        self.cuda_tab_widget.addTab(self.cuda_sass_text, "⚡ SASS")
        
        # Performance tab
        self.cuda_perf_text = QTextEdit()
        self.cuda_perf_text.setReadOnly(True)
        self.cuda_perf_text.setPlainText("Select a CUDA file to see performance analysis")
        self.cuda_tab_widget.addTab(self.cuda_perf_text, "📊 Performance")
        
        self.main_tab_widget.addTab(self.cuda_tab_widget, "🟢 CUDA")
    
    def setup_hip_language_tab(self):
        """Setup HIP language tab with nested analysis tabs"""
        self.hip_tab_widget = QTabWidget()
        
        # Kernel AST tab
        self.hip_ast_text = QTextEdit()
        self.hip_ast_text.setReadOnly(True)
        self.hip_ast_text.setPlainText("Select a HIP file to see kernel AST")
        self.hip_tab_widget.addTab(self.hip_ast_text, "🌳 Kernel AST")
        
        # GCN ISA tab
        self.hip_gcn_text = QTextEdit()
        self.hip_gcn_text.setReadOnly(True)
        self.hip_gcn_text.setPlainText("Select a HIP file to see GCN ISA")
        self.hip_tab_widget.addTab(self.hip_gcn_text, "🎯 GCN ISA")
        
        # LLVM IR tab
        self.hip_llvm_text = QTextEdit()
        self.hip_llvm_text.setReadOnly(True)
        self.hip_llvm_text.setPlainText("Select a HIP file to see LLVM IR")
        self.hip_tab_widget.addTab(self.hip_llvm_text, "⚙️ LLVM IR")
        
        # Performance tab
        self.hip_perf_text = QTextEdit()
        self.hip_perf_text.setReadOnly(True)
        self.hip_perf_text.setPlainText("Select a HIP file to see performance analysis")
        self.hip_tab_widget.addTab(self.hip_perf_text, "📊 Performance")
        
        self.main_tab_widget.addTab(self.hip_tab_widget, "🔴 HIP")
    
    def connect_signals(self):
        """Connect signals"""
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def analyze_file(self, file_path):
        """Analyze a file based on its type"""
        if not file_path:
            self.clear_analysis()
            return
        
        file_path = Path(file_path)
        self.current_file = file_path
        
        # Check which analyzers can handle this file
        compatible_analyzers = self.api_client.can_analyze(str(file_path))
        
        if not compatible_analyzers:
            self.clear_analysis()
            self.status_label.setText(f"No analyzer available for: {file_path.name}")
            return
        
        # Use the first compatible analyzer (could be made configurable)
        analyzer_type = compatible_analyzers[0]
        
        # Set appropriate tab based on analyzer type
        if analyzer_type == 'python':
            self.main_tab_widget.setCurrentWidget(self.python_tab_widget)
        elif analyzer_type == 'cpp':
            self.main_tab_widget.setCurrentWidget(self.cpp_tab_widget)
        
        self.status_label.setText(f"Analyzing {file_path.name} with {analyzer_type}...")
        
        # Start analysis in worker thread - always attempt, let the result determine server availability
        self.worker = AnalysisWorker(self.api_client, str(file_path), analyzer_type)
        self.worker.analysis_complete.connect(self.on_analysis_complete)
        self.worker.start()
    
    def detect_language(self, file_path):
        """Detect programming language from file extension"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            return 'python'
        elif suffix in ['.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx']:
            return 'cpp'
        elif suffix == '.rs':
            return 'rust'
        elif suffix == '.py' and self.is_triton_file(file_path):
            return 'triton'
        else:
            return 'unknown'
    
    def is_triton_file(self, file_path):
        """Check if a Python file contains Triton code"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'triton' in content.lower() and '@triton.jit' in content
        except:
            return False
    
    def display_cpp_analysis(self, result: AnalysisResult):
        """Display C/C++ analysis results"""
        data = result.data
        
        # Update AST tab
        self.cpp_ast_text.setPlainText(data.get('ast', 'No AST data available'))
        
        # Update assembly tab
        self.cpp_asm_text.setPlainText(data.get('assembly', 'No assembly data available'))
        
        # Update analysis tab
        self.cpp_analysis_text.setPlainText(data.get('analysis_summary', 'No analysis available'))
        
    
    def analyze_rust_file(self, file_path):
        """Analyze Rust file (placeholder)"""
        self.clear_analysis()
        self.rust_hir_text.setPlainText("Rust HIR analysis not yet implemented")
        self.rust_mir_text.setPlainText("Rust MIR analysis not yet implemented")
        self.rust_llvm_text.setPlainText("Rust LLVM IR analysis not yet implemented")
        self.rust_analysis_text.setPlainText("Rust borrow checker analysis not yet implemented")
        self.error_text.setPlainText("Rust analysis coming soon")
    
    def analyze_triton_file(self, file_path):
        """Analyze Triton file (placeholder)"""
        self.clear_analysis()
        self.triton_ast_text.setPlainText("Triton kernel AST analysis not yet implemented")
        self.triton_ptx_text.setPlainText("Triton PTX generation not yet implemented")
        self.triton_perf_text.setPlainText("Triton performance analysis not yet implemented")
        self.error_text.setPlainText("Triton analysis coming soon")
    
    def on_analysis_complete(self, result: AnalysisResult):
        """Handle analysis completion"""
        if not result:
            # Check if server is still reachable
            if not self.api_client.health_check():
                self.server_available = False
                self.show_server_unavailable_message()
            else:
                self.status_label.setText("Analysis failed - no result")
            return
        
        if not result.success:
            error_msg = '\n'.join(result.errors) if result.errors else "Unknown error"
            self.status_label.setText(f"Analysis failed: {error_msg}")
            return
        
        # Server is working again - update availability status
        if not self.server_available:
            self.server_available = True
            # Show analysis UI again
            self.error_widget.hide()
            self.main_tab_widget.show()
        
        # Display results based on analyzer type
        if result.analyzer_type == 'python':
            self.display_python_analysis(result)
        elif result.analyzer_type == 'cpp':
            self.display_cpp_analysis(result)
        
        # Update status with appropriate file name
        if self.current_file:
            self.status_label.setText(f"Analysis complete: {self.current_file.name}")
        else:
            self.status_label.setText("Analysis complete: hello_world.py")
        
        # Reset status label style in case it was showing error
        self.status_label.setStyleSheet(theme_manager.get_widget_style('label', font_size=8.0, padding=5))
    
    def display_python_analysis(self, result: AnalysisResult):
        """Display Python analysis results"""
        data = result.data
        
        # Update AST tab
        self.ast_text.setPlainText(data.get('ast', 'No AST data available'))
        
        # Update disassembly tab
        dis_result = data.get('disassembly', '')
        if dis_result:
            self.dis_text.setPlainText(dis_result)  # Simplified for now
        else:
            self.dis_text.setPlainText("No disassembly data available")
        
        # Update analysis tab
        self.analysis_text.setPlainText(data.get('analysis_summary', 'No analysis available'))
        
    
    def clear_analysis(self):
        """Clear all analysis results"""
        self.current_file = None
        self.current_language = None
        self.bytecode_analysis = None
        
        # Clear Python tabs
        self.ast_text.setPlainText("Select a Python file to see its AST representation")
        self.dis_text.setPlainText("Select a Python file to see its bytecode disassembly")
        self.analysis_text.setPlainText("Select a Python file to see bytecode analysis")
        
        # Clear C/C++ tabs
        self.cpp_ast_text.setPlainText("Select a C/C++ file to see its AST representation")
        self.cpp_asm_text.setPlainText("Select a C/C++ file to see its assembly output")
        self.cpp_analysis_text.setPlainText("Select a C/C++ file to see static analysis")
        
        # Clear Rust tabs
        self.rust_hir_text.setPlainText("Select a Rust file to see its HIR representation")
        self.rust_mir_text.setPlainText("Select a Rust file to see its MIR representation")
        self.rust_llvm_text.setPlainText("Select a Rust file to see its LLVM IR")
        self.rust_analysis_text.setPlainText("Select a Rust file to see borrow checker analysis")
        
        # Clear Triton tabs
        self.triton_ast_text.setPlainText("Select a Triton file to see kernel AST")
        self.triton_ptx_text.setPlainText("Select a Triton file to see generated PTX")
        self.triton_perf_text.setPlainText("Select a Triton file to see performance analysis")
        
        self.status_label.setText("No file selected")
    
    def create_enhanced_bytecode_display(self, bytecode_analysis):
        """Create enhanced HTML display modeled after dis.dis() with rich navigation"""
        colors = theme_manager.get_colors()
        font_family = theme_manager.current_font_family
        font_size = max(8.0, theme_manager.current_font_size * 0.8)
        
        # Color scheme for different instruction types
        type_colors = {
            'LOAD': colors['primary'],
            'STORE': colors['accent'], 
            'CALL': colors['secondary'],
            'JUMP': '#f39c12',
            'COMPARE': '#9b59b6',
            'BINARY_OP': '#e67e22',
            'BUILD': '#1abc9c',
            'RETURN': '#e74c3c',
            'LOOP': '#f1c40f',
            'OTHER': colors['text_secondary']
        }
        
        # Build the enhanced display
        sections = []
        
        # Function overview section
        if bytecode_analysis.functions:
            sections.append(self._build_function_overview(bytecode_analysis, type_colors))
        
        # Variable listings for each function
        sections.append(self._build_variable_listings(bytecode_analysis, type_colors))
        
        # Main disassembly section
        sections.append(self._build_enhanced_disassembly(bytecode_analysis, type_colors))
        
        # Combine all sections
        html = f'''
        <div style="font-family: '{font_family}', monospace; font-size: {font_size}pt; 
                    line-height: 1.4; color: {colors['text']}; background: transparent;">
            {''.join(sections)}
        </div>
        '''
        
        return html
    
    # Use sandbox implementation for bytecode display methods
    def _build_function_overview(self, analysis, type_colors):
        """Build function overview section - delegate to sandbox"""
        from sandbox import SandboxWidget
        sandbox_widget = SandboxWidget()
        return sandbox_widget._build_function_overview(analysis, type_colors)
    
    def _build_variable_listings(self, analysis, type_colors):
        """Build variable listings for each function - delegate to sandbox"""
        # Simplified version for analysis widget
        return ""  # Skip variable listings in analysis widget
    
    def _build_enhanced_disassembly(self, analysis, type_colors):
        """Build enhanced disassembly section - delegate to sandbox"""
        from sandbox import SandboxWidget
        sandbox_widget = SandboxWidget()
        return sandbox_widget._build_enhanced_disassembly(analysis, type_colors)
    
    def _format_instruction_line(self, instruction, analysis, type_colors):
        """Format instruction line - delegate to sandbox"""
        from sandbox import SandboxWidget
        sandbox_widget = SandboxWidget()
        return sandbox_widget._format_instruction_line(instruction, analysis, type_colors)
    
    def _enhance_argrepr_links(self, instruction, analysis, instr_color):
        """Enhance argrepr links - delegate to sandbox"""
        from sandbox import SandboxWidget
        sandbox_widget = SandboxWidget()
        return sandbox_widget._enhance_argrepr_links(instruction, analysis, instr_color)
    
    def _find_variable_context(self, var_name, analysis):
        """Find variable context - delegate to sandbox"""
        from sandbox import SandboxWidget
        sandbox_widget = SandboxWidget()
        return sandbox_widget._find_variable_context(var_name, analysis)
    
    def _create_enhanced_tooltip(self, instruction, analysis):
        """Create enhanced tooltip - delegate to sandbox"""
        from sandbox import SandboxWidget
        sandbox_widget = SandboxWidget()
        return sandbox_widget._create_enhanced_tooltip(instruction, analysis)
    
    def handle_bytecode_link(self, url):
        """Handle clicking on bytecode navigation links"""
        # Delegate to sandbox widget's implementation
        from sandbox import SandboxWidget
        sandbox_widget = SandboxWidget()
        sandbox_widget.bytecode_analysis = self.bytecode_analysis
        sandbox_widget.dis_text = self.dis_text
        
        # Use the sandbox implementation
        url_str = url.toString()
        
        if url_str.startswith('#offset_'):
            sandbox_widget._scroll_to_anchor(url_str)
        elif url_str.startswith('#var_'):
            if '_' in url_str[5:]:
                sandbox_widget._scroll_to_anchor(url_str)
            else:
                var_name = url_str[5:]
                sandbox_widget._highlight_variable_uses(var_name)
        elif url_str.startswith('#func_'):
            sandbox_widget._scroll_to_anchor(url_str)
        elif url_str.startswith('#call_'):
            func_name = url_str[6:]
            sandbox_widget._highlight_function_calls(func_name)
        elif url_str.startswith('#instr_'):
            sandbox_widget._scroll_to_anchor(url_str)
        elif url_str.startswith('#var_usage_'):
            var_name = url_str[11:]
            sandbox_widget._highlight_variable_uses(var_name)
        elif url_str.startswith('#disasm_'):
            sandbox_widget._scroll_to_anchor(url_str)
    
    def check_server_and_load_example(self):
        """Check server availability and load hello world example"""
        self.server_available = self.api_client.health_check()
        
        if self.server_available:
            self.status_label.setText("Analysis server connected")
            # Reset status label style in case it was showing error
            self.status_label.setStyleSheet(theme_manager.get_widget_style('label', font_size=8.0, padding=5))
            # Show analysis UI
            self.error_widget.hide()
            self.main_tab_widget.show()
            # Load hello world example
            self.analyze_hello_world_example()
        else:
            self.show_server_unavailable_message()
    
    def show_server_unavailable_message(self):
        """Show server unavailable message and hide analysis UI"""
        self.status_label.setText("⚠️ Analysis server cannot be reached")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # Hide the main analysis UI
        self.main_tab_widget.hide()
        
        # Show error message
        self.error_widget.setText(
            "The analysis server is not available.\n\n"
            "Please ensure the server is running and try again.\n"
            "Analysis features will be unavailable until the server connection is restored."
        )
        self.error_widget.setStyleSheet(f"""
            QLabel {{
                color: {theme_manager.get_colors()['text_secondary']};
                font-size: 14pt;
                padding: 40px;
                background-color: {theme_manager.get_colors()['input_bg']};
                border: 2px dashed {theme_manager.get_colors()['border']};
                border-radius: 10px;
                margin: 20px;
            }}
        """)
        self.error_widget.show()
    
    def analyze_hello_world_example(self):
        """Analyze a hello world Python example"""
        hello_world_code = '''def hello_world():
    """A simple hello world function"""
    message = "Hello, World!"
    print(message)
    return message

if __name__ == "__main__":
    result = hello_world()
    print(f"Function returned: {result}")
'''
        
        # Set to Python tab
        self.main_tab_widget.setCurrentWidget(self.python_tab_widget)
        
        # Analyze the code directly
        result = self.api_client.analyze_code(hello_world_code, 'python', 'hello_world.py')
        if result:
            self.on_analysis_complete(result)
        else:
            self.show_server_unavailable_message()
    
    def apply_theme(self):
        """Apply current theme to the widget"""
        # Apply text edit styles
        text_style = f"""
            QTextEdit {{
                background-color: {theme_manager.get_colors()['input_bg']};
                border: 1px solid {theme_manager.get_colors()['border']};
                border-radius: 5px;
                padding: 5px;
                font-family: '{theme_manager.current_font_family}', monospace;
                font-size: {max(8.0, theme_manager.current_font_size * 0.8)}pt;
                color: {theme_manager.get_colors()['text']};
            }}
        """
        
        # Apply to all text widgets
        text_widgets = [
            # Python tabs
            self.ast_text, self.dis_text, self.analysis_text,
            # C/C++ tabs
            self.cpp_ast_text, self.cpp_asm_text, self.cpp_analysis_text,
            # Rust tabs
            self.rust_hir_text, self.rust_mir_text, self.rust_llvm_text, self.rust_analysis_text,
            # Triton tabs
            self.triton_ast_text, self.triton_ptx_text, self.triton_perf_text,
            # CUDA tabs
            self.cuda_ast_text, self.cuda_ptx_text, self.cuda_sass_text, self.cuda_perf_text,
            # HIP tabs
            self.hip_ast_text, self.hip_gcn_text, self.hip_llvm_text, self.hip_perf_text
        ]
        
        for text_widget in text_widgets:
            text_widget.setStyleSheet(text_style)
        
        # Apply tab widget styles
        tab_style = f"""
            QTabWidget::pane {{
                border: 1px solid {theme_manager.get_colors()['border']};
                border-radius: 5px;
                background-color: {theme_manager.get_colors()['background']};
            }}
            QTabBar::tab {{
                background-color: {theme_manager.get_colors()['button_bg']};
                color: white;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-family: '{theme_manager.current_font_family}';
                font-size: {max(8.0, theme_manager.current_font_size * 0.7)}pt;
            }}
            QTabBar::tab:selected {{
                background-color: {theme_manager.get_colors()['primary']};
            }}
            QTabBar::tab:hover {{
                background-color: {theme_manager.get_colors()['button_hover']};
            }}
        """
        
        # Apply to all tab widgets
        self.main_tab_widget.setStyleSheet(tab_style)
        self.python_tab_widget.setStyleSheet(tab_style)
        self.cpp_tab_widget.setStyleSheet(tab_style)
        self.rust_tab_widget.setStyleSheet(tab_style)
        self.triton_tab_widget.setStyleSheet(tab_style)
        
        # Apply status label style (unless it's showing server error)
        if "cannot be reached" not in self.status_label.text():
            self.status_label.setStyleSheet(theme_manager.get_widget_style('label', font_size=8.0, padding=5))
