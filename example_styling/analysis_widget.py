"""
Multi-language Code Analysis Widget
Provides AST parsing, bytecode disassembly, and analysis for multiple programming languages.
"""

import ast
import dis
import io
import sys
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit, QTextBrowser,
                               QLabel, QScrollArea)
from theme_manager import theme_manager
from bytecode_parser import BytecodeParser


class PythonAnalyzer(QObject):
    """Analyzes Python code using AST and disassembly"""
    
    analysis_ready = Signal(str, str, str, str)  # ast_dump, disassembly, bytecode_summary, errors
    
    def __init__(self):
        super().__init__()
        self.bytecode_parser = BytecodeParser()
    
    def analyze_file(self, file_path):
        """Analyze a Python file and emit results"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            ast_result, dis_result, bytecode_summary, errors = self.analyze_code(source_code, file_path)
            self.analysis_ready.emit(ast_result, dis_result, bytecode_summary, errors)
            
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.analysis_ready.emit("", "", "", error_msg)
    
    def analyze_code(self, source_code, filename="<string>"):
        """Analyze Python source code"""
        ast_result = ""
        dis_result = ""
        bytecode_summary = ""
        errors = ""
        
        try:
            # Parse AST
            tree = ast.parse(source_code, filename=filename)
            ast_result = self.format_ast_dump(tree)
            
            # Compile and disassemble
            try:
                compiled_code = compile(tree, filename, 'exec')
                
                # Capture disassembly output for fallback
                old_stdout = sys.stdout
                sys.stdout = dis_output = io.StringIO()
                
                dis.dis(compiled_code)
                
                sys.stdout = old_stdout
                dis_result = dis_output.getvalue()
                
                # Parse bytecode for analysis using code object
                try:
                    self.bytecode_analysis = self.bytecode_parser.analyze_code_object(compiled_code, source_code)
                    bytecode_summary = self.bytecode_parser.format_analysis_summary(self.bytecode_analysis)
                except Exception as e:
                    # Fallback to old method
                    self.bytecode_analysis = self.bytecode_parser.parse_disassembly(dis_result)
                    bytecode_summary = f"Using fallback analysis: {str(e)}\n\n" + self.bytecode_parser.format_analysis_summary(self.bytecode_analysis)
                
            except Exception as e:
                dis_result = f"Compilation error: {str(e)}"
                bytecode_summary = "Cannot analyze bytecode due to compilation error"
                
        except SyntaxError as e:
            errors = f"Syntax Error: {e.msg} (line {e.lineno})"
            ast_result = "Cannot parse due to syntax error"
            dis_result = "Cannot disassemble due to syntax error"
            bytecode_summary = "Cannot analyze bytecode due to syntax error"
            
        except Exception as e:
            errors = f"Analysis error: {str(e)}"
            
        return ast_result, dis_result, bytecode_summary, errors
    
    def format_ast_dump(self, tree):
        """Format AST dump with better readability"""
        dump = ast.dump(tree, indent=2)
        
        # Add some formatting for better readability
        lines = dump.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Count leading spaces for indentation level
            indent_level = len(line) - len(line.lstrip())
            
            # Add visual indicators for different AST node types
            if 'FunctionDef(' in line:
                line = line.replace('FunctionDef(', '🔧 FunctionDef(')
            elif 'ClassDef(' in line:
                line = line.replace('ClassDef(', '🏗️  ClassDef(')
            elif 'Import(' in line or 'ImportFrom(' in line:
                line = line.replace('Import(', '📦 Import(').replace('ImportFrom(', '📦 ImportFrom(')
            elif 'If(' in line:
                line = line.replace('If(', '🔀 If(')
            elif 'For(' in line or 'While(' in line:
                line = line.replace('For(', '🔄 For(').replace('While(', '🔄 While(')
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)


class AnalysisWidget(QWidget):
    """Multi-language code analysis widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.current_language = None
        self.analyzer = PythonAnalyzer()
        self.setup_ui()
        self.connect_signals()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the analysis UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status label
        self.status_label = QLabel("No file selected")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Main tab widget for different languages
        self.main_tab_widget = QTabWidget()
        
        # Create language-specific tab widgets
        self.setup_python_language_tab()
        self.setup_cpp_language_tab()
        self.setup_rust_language_tab()
        self.setup_triton_language_tab()
        
        # Shared errors tab at main level
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setPlainText("No errors")
        self.main_tab_widget.addTab(self.error_text, "⚠️ Errors")
        
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
    
    def connect_signals(self):
        """Connect signals"""
        self.analyzer.analysis_ready.connect(self.display_analysis)
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def analyze_file(self, file_path):
        """Analyze a file based on its type"""
        if not file_path:
            self.clear_analysis()
            return
        
        file_path = Path(file_path)
        self.current_file = file_path
        
        # Determine file type and language
        language = self.detect_language(file_path)
        self.current_language = language
        
        if language == 'python':
            self.status_label.setText(f"Analyzing Python: {file_path.name}")
            self.main_tab_widget.setCurrentWidget(self.python_tab_widget)
            self.analyzer.analyze_file(str(file_path))
        elif language == 'cpp':
            self.status_label.setText(f"Analyzing C/C++: {file_path.name}")
            self.main_tab_widget.setCurrentWidget(self.cpp_tab_widget)
            self.analyze_cpp_file(file_path)
        elif language == 'rust':
            self.status_label.setText(f"Analyzing Rust: {file_path.name}")
            self.main_tab_widget.setCurrentWidget(self.rust_tab_widget)
            self.analyze_rust_file(file_path)
        elif language == 'triton':
            self.status_label.setText(f"Analyzing Triton: {file_path.name}")
            self.main_tab_widget.setCurrentWidget(self.triton_tab_widget)
            self.analyze_triton_file(file_path)
        else:
            self.clear_analysis()
            self.status_label.setText(f"Unsupported file type: {file_path.name}")
    
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
    
    def analyze_cpp_file(self, file_path):
        """Analyze C/C++ file (placeholder)"""
        self.clear_analysis()
        self.cpp_ast_text.setPlainText("C/C++ AST analysis not yet implemented")
        self.cpp_asm_text.setPlainText("C/C++ assembly analysis not yet implemented")
        self.cpp_analysis_text.setPlainText("C/C++ static analysis not yet implemented")
        self.error_text.setPlainText("C/C++ analysis coming soon")
    
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
    
    def display_analysis(self, ast_result, dis_result, bytecode_summary, errors):
        """Display analysis results in tabs"""
        # Update AST tab
        if ast_result:
            self.ast_text.setPlainText(ast_result)
        else:
            self.ast_text.setPlainText("No AST data available")
        
        # Update disassembly tab with custom rich formatting
        if dis_result:
            try:
                # Use the analysis from analyzer which has detailed function info
                if hasattr(self.analyzer, 'bytecode_analysis'):
                    self.bytecode_analysis = self.analyzer.bytecode_analysis
                else:
                    # Fallback to parsing dis output
                    self.bytecode_analysis = self.analyzer.bytecode_parser.parse_disassembly(dis_result)
                
                formatted_html = self.create_enhanced_bytecode_display(self.bytecode_analysis)
                self.dis_text.setHtml(formatted_html)
            except Exception as e:
                # Fallback to plain text if formatting fails
                self.dis_text.setPlainText(f"Error parsing bytecode: {str(e)}\n\nRaw output:\n{dis_result}")
        else:
            self.dis_text.setPlainText("No disassembly data available")
            self.bytecode_analysis = None
        
        # Update analysis tab
        if bytecode_summary:
            self.analysis_text.setPlainText(bytecode_summary)
        else:
            self.analysis_text.setPlainText("No bytecode analysis available")
        
        # Update errors tab
        if errors:
            self.error_text.setPlainText(errors)
            # Switch to errors tab if there are errors
            self.tab_widget.setCurrentIndex(3)
        else:
            self.error_text.setPlainText("No errors detected")
        
        # Update status
        if self.current_file:
            self.status_label.setText(f"Python analysis complete: {self.current_file.name}")
    
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
        
        # Clear shared tabs
        self.error_text.setPlainText("No errors")
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
    
    def _build_function_overview(self, analysis, type_colors):
        """Build function overview section"""
        colors = theme_manager.get_colors()
        
        overview = [f'<div style="margin-bottom: 20px; padding: 10px; background-color: {colors["background"].replace("120", "40")}; border-radius: 5px;">']
        overview.append(f'<h3 style="color: {type_colors["CALL"]}; margin: 0 0 10px 0;">📋 Functions Overview</h3>')
        
        for func in analysis.functions:
            func_name = func.name if func.name != "<module>" else "Main Module"
            overview.append(f'''
            <div style="margin: 5px 0; padding: 5px; background-color: {colors["hover"]}; border-radius: 3px;">
                <a href="#func_{func.name}" style="color: {type_colors["CALL"]}; text-decoration: none; font-weight: bold;">
                    {func_name}
                </a>
                <span style="color: {colors["text_secondary"]}; margin-left: 10px;">
                    Args: {func.argcount}, Locals: {len(func.varnames)}
                </span>
            </div>
            ''')
        
        overview.append('</div>')
        return ''.join(overview)
    
    def _build_variable_listings(self, analysis, type_colors):
        """Build variable listings for each function"""
        colors = theme_manager.get_colors()
        
        listings = []
        
        for func in analysis.functions:
            func_name = func.name if func.name != "<module>" else "Main Module"
            
            listings.append(f'''
            <div style="margin-bottom: 15px; padding: 10px; background-color: {colors["background"].replace("120", "30")}; border-radius: 5px;">
                <a name="func_{func.name}"></a>
                <h4 style="color: {type_colors["CALL"]}; margin: 0 0 10px 0;">{func_name}</h4>
            ''')
            
            # Local variables only
            if func.varnames:
                listings.append(f'<div style="margin: 5px 0;"><strong style="color: {type_colors["LOAD"]};">Variables:</strong><br>')
                for i, var in enumerate(func.varnames):
                    listings.append(f'''
                    <a name="var_{var}_{func.name}"></a>
                    <a href="#var_usage_{var}" style="color: {type_colors["LOAD"]}; text-decoration: none; margin-right: 10px;" 
                       title="Find all uses of {var}">{var}</a>
                    ''')
                listings.append('</div>')
            
            listings.append('</div>')
        
        return ''.join(listings)
    
    def _build_enhanced_disassembly(self, analysis, type_colors):
        """Build enhanced disassembly section modeled after dis.dis()"""
        colors = theme_manager.get_colors()
        
        disasm = [f'''
        <div style="margin-top: 20px;">
            <h3 style="color: {colors["text"]}; margin: 0 0 15px 0;">⚙️ Disassembly</h3>
        ''']
        
        current_function = None
        
        for func in analysis.functions:
            # Function header
            func_name = func.name if func.name != "<module>" else "Main Module"
            disasm.append(f'''
            <div style="margin: 15px 0 10px 0; padding: 8px; background-color: {colors["hover"]}; border-radius: 5px;">
                <a name="disasm_{func.name}"></a>
                <strong style="color: {type_colors["CALL"]};">Disassembly of {func_name}:</strong>
            </div>
            ''')
            
            # Instructions for this function
            for instruction in func.instructions:
                line_html = self._format_instruction_line(instruction, analysis, type_colors)
                disasm.append(line_html)
        
        disasm.append('</div>')
        return ''.join(disasm)
    
    def _format_instruction_line(self, instruction, analysis, type_colors):
        """Format a single instruction line with enhanced features"""
        colors = theme_manager.get_colors()
        
        # Create anchor for this instruction
        anchor = f'<a name="instr_{instruction.offset}"></a>'
        
        # Jump target marker
        target_marker = "&gt;&gt;" if instruction.is_jump_target else "&nbsp;&nbsp;"
        if instruction.is_jump_target:
            anchor += f'<a name="offset_{instruction.offset}"></a>'
        
        # Line number
        line_info = f"({instruction.line_number:3d})" if instruction.line_number else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        
        # Instruction color
        instr_color = type_colors.get(instruction.instruction_type.name, type_colors['OTHER'])
        
        # Format instruction parts
        offset_part = f'<span style="color: {colors["text_secondary"]};">{instruction.offset:4d}</span>'
        opname_part = f'<span style="color: {instr_color}; font-weight: bold;">{instruction.opname}</span>'
        
        # Argument and representation with enhanced linking
        arg_part = ""
        if instruction.arg is not None:
            arg_part = f'<span style="color: {colors["text"]};">{instruction.arg:4d}</span>'
        
        argrepr_part = ""
        if instruction.argrepr:
            argrepr_text = self._enhance_argrepr_links(instruction, analysis, instr_color)
            argrepr_part = f'<span style="color: {colors["text"]};">({argrepr_text})</span>'
        
        # Combine parts
        line_content = f"{target_marker} {line_info} {offset_part} {opname_part:<20}"
        if arg_part:
            line_content += f" {arg_part}"
        if argrepr_part:
            line_content += f" {argrepr_part}"
        
        # Add hover tooltip
        tooltip = self._create_enhanced_tooltip(instruction, analysis)
        
        # Highlight jump targets
        line_style = ""
        if instruction.is_jump_target:
            line_style = f'background-color: {colors["hover"]}; padding: 2px; border-radius: 3px;'
        
        return f'<div style="{line_style}" title="{tooltip}">{anchor}{line_content}</div>'
    
    def _enhance_argrepr_links(self, instruction, analysis, instr_color):
        """Enhance argrepr with clickable links for variables and functions"""
        argrepr_text = instruction.argrepr
        
        # Make variable names clickable
        if instruction.instruction_type.name in ['LOAD', 'STORE'] and instruction.argval:
            var_name = instruction.argval
            # Find which function this variable belongs to
            func_context = self._find_variable_context(var_name, analysis)
            if func_context:
                argrepr_text = argrepr_text.replace(
                    var_name,
                    f'<a href="#var_{var_name}_{func_context}" style="color: {instr_color}; text-decoration: underline;" title="Go to {var_name} definition in {func_context}">{var_name}</a>'
                )
        
        # Make jump targets clickable
        elif instruction.instruction_type.name == 'JUMP':
            import re
            # Handle both "to 92" format and standalone numbers
            if 'to ' in instruction.argrepr:
                # Match "(to 92)" pattern
                target_match = re.search(r'\(to (\d+)\)', instruction.argrepr)
                if target_match:
                    target_offset = target_match.group(1)
                    if int(target_offset) in analysis.jump_targets:
                        argrepr_text = argrepr_text.replace(
                            f'to {target_offset}',
                            f'to <a href="#offset_{target_offset}" style="color: {instr_color}; text-decoration: underline;" title="Jump to offset {target_offset}">{target_offset}</a>'
                        )
            else:
                # Fallback for other jump formats
                target_match = re.search(r'(\d+)', instruction.argrepr)
                if target_match:
                    target_offset = target_match.group(1)
                    if int(target_offset) in analysis.jump_targets:
                        argrepr_text = argrepr_text.replace(
                            target_offset,
                            f'<a href="#offset_{target_offset}" style="color: {instr_color}; text-decoration: underline;" title="Jump to offset {target_offset}">{target_offset}</a>'
                        )
        
        # Make function calls clickable
        elif instruction.instruction_type.name == 'CALL' and instruction.argval:
            func_name = instruction.argval
            # Check if this function is defined in our analysis
            for func in analysis.functions:
                if func.name == func_name:
                    argrepr_text = argrepr_text.replace(
                        func_name,
                        f'<a href="#func_{func_name}" style="color: {instr_color}; text-decoration: underline;" title="Go to {func_name} definition">{func_name}</a>'
                    )
                    break
            else:
                # External function call
                argrepr_text = argrepr_text.replace(
                    func_name,
                    f'<a href="#call_{func_name}" style="color: {instr_color}; text-decoration: underline;" title="Find all calls to {func_name}">{func_name}</a>'
                )
        
        return argrepr_text
    
    def _find_variable_context(self, var_name, analysis):
        """Find which function a variable belongs to"""
        for func in analysis.functions:
            if var_name in func.varnames or var_name in func.freevars or var_name in func.cellvars:
                return func.name
        return None
    
    def _create_enhanced_tooltip(self, instruction, analysis):
        """Create enhanced tooltip with context information"""
        tooltip_parts = [
            f"Offset: {instruction.offset}",
            f"Opcode: {instruction.opname}",
            f"Type: {instruction.instruction_type.value.title()}"
        ]
        
        if instruction.line_number:
            tooltip_parts.append(f"Source Line: {instruction.line_number}")
        
        if instruction.arg is not None:
            tooltip_parts.append(f"Argument: {instruction.arg}")
        
        if instruction.argval:
            tooltip_parts.append(f"Value: {instruction.argval}")
            
            # Add context for variables
            if instruction.instruction_type.name in ['LOAD', 'STORE']:
                context = self._find_variable_context(instruction.argval, analysis)
                if context:
                    tooltip_parts.append(f"Context: {context}")
        
        if instruction.is_jump_target:
            tooltip_parts.append("🎯 Jump Target")
        
        return " | ".join(tooltip_parts)
    
    def _build_navigation_links(self, analysis, type_colors):
        """Build navigation links section"""
        colors = theme_manager.get_colors()
        links = []
        
        # Quick stats
        stats = f'''
        <div style="margin-bottom: 10px; padding: 8px; background-color: {colors['background'].replace('120', '60')}; border-radius: 5px;">
            <strong>📊 Quick Stats:</strong> 
            {len(analysis.instructions)} instructions, 
            {len(analysis.jump_targets)} jump targets, 
            {len(analysis.local_vars)} locals, 
            {len(analysis.global_vars)} globals
        </div>
        '''
        links.append(stats)
        
        # Jump targets
        if analysis.jump_targets:
            jump_links = []
            for target in sorted(analysis.jump_targets):
                jump_links.append(f'<a href="#offset_{target}" style="color: {type_colors["JUMP"]}; text-decoration: none; margin-right: 8px;" title="Jump to offset {target}">@{target}</a>')
            
            jumps_section = f'''
            <div style="margin-bottom: 8px;">
                <strong style="color: {type_colors['JUMP']};">🔀 Jump Targets:</strong> 
                {' '.join(jump_links)}
            </div>
            '''
            links.append(jumps_section)
        
        # Variables
        if analysis.local_vars or analysis.global_vars:
            var_links = []
            
            for var in sorted(analysis.local_vars):
                var_links.append(f'<a href="#var_{var}" style="color: {type_colors["LOAD"]}; text-decoration: none; margin-right: 8px;" title="Find uses of local variable {var}">🔵{var}</a>')
            
            for var in sorted(analysis.global_vars):
                var_links.append(f'<a href="#var_{var}" style="color: {type_colors["STORE"]}; text-decoration: none; margin-right: 8px;" title="Find uses of global variable {var}">🔴{var}</a>')
            
            if var_links:
                vars_section = f'''
                <div style="margin-bottom: 8px;">
                    <strong style="color: {colors['text']};">📦 Variables:</strong> 
                    {' '.join(var_links)}
                </div>
                '''
                links.append(vars_section)
        
        # Function calls
        unique_calls = list(set(analysis.function_calls))
        if unique_calls:
            call_links = []
            for call in sorted(unique_calls)[:10]:  # Limit to first 10
                call_links.append(f'<a href="#call_{call}" style="color: {type_colors["CALL"]}; text-decoration: none; margin-right: 8px;" title="Find calls to {call}">📞{call}</a>')
            
            calls_section = f'''
            <div style="margin-bottom: 8px;">
                <strong style="color: {type_colors['CALL']};">📞 Function Calls:</strong> 
                {' '.join(call_links)}
            </div>
            '''
            links.append(calls_section)
        
        return ''.join(links)
    
    def _create_instruction_tooltip(self, instruction):
        """Create tooltip text for an instruction"""
        tooltip_parts = [
            f"Offset: {instruction.offset}",
            f"Opcode: {instruction.opname}",
            f"Type: {instruction.instruction_type.value.title()}"
        ]
        
        if instruction.line_number:
            tooltip_parts.append(f"Source Line: {instruction.line_number}")
        
        if instruction.arg is not None:
            tooltip_parts.append(f"Argument: {instruction.arg}")
        
        if instruction.argval:
            tooltip_parts.append(f"Value: {instruction.argval}")
        
        if instruction.is_jump_target:
            tooltip_parts.append("🎯 Jump Target")
        
        return " | ".join(tooltip_parts)
    
    def handle_bytecode_link(self, url):
        """Handle clicking on bytecode navigation links"""
        url_str = url.toString()
        
        if url_str.startswith('#offset_'):
            # Jump to specific offset
            self._scroll_to_anchor(url_str)
        
        elif url_str.startswith('#var_'):
            # Handle variable links (could be var_name or var_name_function)
            if '_' in url_str[5:]:  # var_name_function format
                self._scroll_to_anchor(url_str)
            else:
                var_name = url_str[5:]  # Remove '#var_'
                self._highlight_variable_uses(var_name)
        
        elif url_str.startswith('#func_'):
            # Jump to function definition
            self._scroll_to_anchor(url_str)
        
        elif url_str.startswith('#call_'):
            # Highlight all calls to a function
            func_name = url_str[6:]  # Remove '#call_'
            self._highlight_function_calls(func_name)
        
        elif url_str.startswith('#instr_'):
            # Jump to specific instruction
            self._scroll_to_anchor(url_str)
        
        elif url_str.startswith('#var_usage_'):
            # Highlight all uses of a variable across functions
            var_name = url_str[11:]  # Remove '#var_usage_'
            self._highlight_variable_uses(var_name)
        
        elif url_str.startswith('#disasm_'):
            # Jump to function disassembly
            self._scroll_to_anchor(url_str)
    
    def _scroll_to_anchor(self, anchor):
        """Scroll to a specific anchor in the text"""
        cursor = self.dis_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        
        if self.dis_text.find(anchor.replace('#', '')):
            self.dis_text.ensureCursorVisible()
    
    def _highlight_variable_uses(self, var_name):
        """Highlight all uses of a variable"""
        if not self.bytecode_analysis:
            return
        
        # Find all instructions that use this variable
        matching_instructions = []
        for i, instr in enumerate(self.bytecode_analysis.instructions):
            if (instr.argval == var_name and 
                instr.instruction_type.name in ['LOAD', 'STORE']):
                matching_instructions.append(i)
        
        # Scroll to first occurrence
        if matching_instructions:
            self._scroll_to_anchor(f'#instr_{matching_instructions[0]}')
    
    def _highlight_function_calls(self, func_name):
        """Highlight all calls to a function"""
        if not self.bytecode_analysis:
            return
        
        # Find all call instructions for this function
        matching_instructions = []
        for i, instr in enumerate(self.bytecode_analysis.instructions):
            if (instr.argval == func_name and 
                instr.instruction_type.name == 'CALL'):
                matching_instructions.append(i)
        
        # Scroll to first occurrence
        if matching_instructions:
            self._scroll_to_anchor(f'#instr_{matching_instructions[0]}')
    
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
            # Shared tabs
            self.error_text
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
        
        # Apply status label style
        self.status_label.setStyleSheet(theme_manager.get_widget_style('label', font_size=8.0, padding=5))
