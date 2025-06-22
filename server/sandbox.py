"""
Python Code Analysis Sandbox
Provides AST parsing and bytecode disassembly for Python files.
"""

import ast
import dis
import io
import sys
import inspect
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit, QTextBrowser,
                               QLabel, QScrollArea)
from theme_manager import theme_manager
from bytecode_parser import BytecodeParser


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
        try:
            tree = ast.parse(source_code, filename=filename)
            ast_result = self.format_ast_dump(tree)
            
            self.function_objects = self._extract_function_objects(source_code, filename)
            
            try:
                compiled_code = compile(tree, filename, 'exec')
                
                old_stdout = sys.stdout
                sys.stdout = dis_output = io.StringIO()
                dis.dis(compiled_code)
                sys.stdout = old_stdout
                dis_result = dis_output.getvalue()
                
                try:
                    self.bytecode_analysis = self.bytecode_parser.analyze_code_object(compiled_code, source_code, self.function_objects)
                    bytecode_summary = self.bytecode_parser.format_analysis_summary(self.bytecode_analysis)
                except Exception as e:
                    self.bytecode_analysis = self.bytecode_parser.parse_disassembly(dis_result)
                    bytecode_summary = f"Using fallback analysis: {str(e)}\n\n" + self.bytecode_parser.format_analysis_summary(self.bytecode_analysis)
                
                return ast_result, dis_result, bytecode_summary, ""
                
            except Exception as e:
                return ast_result, f"Compilation error: {str(e)}", "Cannot analyze bytecode due to compilation error", ""
                
        except SyntaxError as e:
            error_msg = f"Syntax Error: {e.msg} (line {e.lineno})"
            return "Cannot parse due to syntax error", "Cannot disassemble due to syntax error", "Cannot analyze bytecode due to syntax error", error_msg
            
        except Exception as e:
            return "", "", "", f"Analysis error: {str(e)}"
    
    def _extract_function_objects(self, source_code, filename):
        """Extract function objects by executing the code"""
        try:
            namespace = {}
            exec(compile(source_code, filename, 'exec'), namespace)
            return {name: obj for name, obj in namespace.items() if inspect.isfunction(obj)}
        except Exception:
            return {}
    
    def format_ast_dump(self, tree):
        """Format AST dump with better readability"""
        dump = ast.dump(tree, indent=2)
        
        replacements = {
            'FunctionDef(': '🔧 FunctionDef(',
            'ClassDef(': '🏗️  ClassDef(',
            'Import(': '📦 Import(',
            'ImportFrom(': '📦 ImportFrom(',
            'If(': '🔀 If(',
            'For(': '🔄 For(',
            'While(': '🔄 While('
        }
        
        for old, new in replacements.items():
            dump = dump.replace(old, new)
        
        return dump


class SandboxWidget(QWidget):
    """Sandbox panel for multi-language code analysis"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.current_language = None
        self.analyzer = PythonAnalyzer()
        self.setup_ui()
        self.connect_signals()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the sandbox UI"""
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
        
        self.status_label.setText(f"Analyzing {file_path.name} with {analyzer_type}...")
        
        # Start analysis in worker thread
        self.worker = AnalysisWorker(self.api_client, str(file_path), analyzer_type)
        self.worker.analysis_complete.connect(self.on_analysis_complete)
        self.worker.start()
    
    def detect_language(self, file_path):
        """Detect programming language from file extension"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            return 'triton' if self.is_triton_file(file_path) else 'python'
        elif suffix in ['.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx']:
            return 'cpp'
        elif suffix == '.rs':
            return 'rust'
        else:
            return 'unknown'
    
    def is_triton_file(self, file_path):
        """Check if a Python file contains Triton code"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'triton' in content.lower() and '@triton.jit' in content
        except Exception:
            return False
    
    def analyze_cpp_file(self, file_path):
        """Analyze C/C++ file (placeholder)"""
        self._set_placeholder_text("C/C++", [
            (self.cpp_ast_text, "C/C++ AST analysis not yet implemented"),
            (self.cpp_asm_text, "C/C++ assembly analysis not yet implemented"),
            (self.cpp_analysis_text, "C/C++ static analysis not yet implemented")
        ])
    
    def analyze_rust_file(self, file_path):
        """Analyze Rust file (placeholder)"""
        self._set_placeholder_text("Rust", [
            (self.rust_hir_text, "Rust HIR analysis not yet implemented"),
            (self.rust_mir_text, "Rust MIR analysis not yet implemented"),
            (self.rust_llvm_text, "Rust LLVM IR analysis not yet implemented"),
            (self.rust_analysis_text, "Rust borrow checker analysis not yet implemented")
        ])
    
    def analyze_triton_file(self, file_path):
        """Analyze Triton file (placeholder)"""
        self._set_placeholder_text("Triton", [
            (self.triton_ast_text, "Triton kernel AST analysis not yet implemented"),
            (self.triton_ptx_text, "Triton PTX generation not yet implemented"),
            (self.triton_perf_text, "Triton performance analysis not yet implemented")
        ])
    
    def _set_placeholder_text(self, language, text_widgets):
        """Helper to set placeholder text for language tabs"""
        self.clear_analysis()
        for widget, text in text_widgets:
            widget.setPlainText(text)
        self.error_text.setPlainText(f"{language} analysis coming soon")
    
    def display_analysis(self, ast_result, dis_result, bytecode_summary, errors):
        """Display analysis results in tabs"""
        self.ast_text.setPlainText(ast_result or "No AST data available")
        
        if dis_result:
            try:
                self.bytecode_analysis = getattr(self.analyzer, 'bytecode_analysis', None) or self.analyzer.bytecode_parser.parse_disassembly(dis_result)
                formatted_html = self.create_enhanced_bytecode_display(self.bytecode_analysis)
                self.dis_text.setHtml(formatted_html)
            except Exception as e:
                self.dis_text.setPlainText(f"Error parsing bytecode: {str(e)}\n\nRaw output:\n{dis_result}")
        else:
            self.dis_text.setPlainText("No disassembly data available")
            self.bytecode_analysis = None
        
        self.analysis_text.setPlainText(bytecode_summary or "No bytecode analysis available")
        self.error_text.setPlainText(errors or "No errors detected")
        
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
        font_size = max(7.5, theme_manager.current_font_size * 0.8)
        
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
            
            if func.name == "<module>":
                signature = "(module)"
            elif func.function_object is not None:
                signature = str(inspect.signature(func.function_object))
            else:
                signature = "(signature unavailable)"
            
            overview.append(f'''
            <div style="margin: 5px 0; padding: 5px; background-color: {colors["hover"]}; border-radius: 3px;">
                <a href="#func_{func.name}" style="color: {type_colors["CALL"]}; text-decoration: none; font-weight: bold;">
                    {func_name}
                </a>
                <span style="color: {colors["text_secondary"]}; font-family: monospace;">
                    {signature}
                </span>
            </div>
            ''')
        
        overview.append('</div>')
        return ''.join(overview)
    
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
        import re
        argrepr_text = instruction.argrepr
        
        if instruction.instruction_type.name in ['LOAD', 'STORE'] and instruction.argval:
            var_name = instruction.argval
            func_context = self._find_variable_context(var_name, analysis)
            if func_context:
                argrepr_text = argrepr_text.replace(
                    var_name,
                    f'<a href="#var_{var_name}_{func_context}" style="color: {instr_color}; text-decoration: underline;" title="Go to {var_name} definition in {func_context}">{var_name}</a>'
                )
        
        elif instruction.instruction_type.name == 'JUMP':
            if 'to ' in instruction.argrepr:
                target_match = re.search(r'\(to (\d+)\)', instruction.argrepr)
            else:
                target_match = re.search(r'(\d+)', instruction.argrepr)
            
            if target_match:
                target_offset = target_match.group(1)
                if int(target_offset) in analysis.jump_targets:
                    old_text = f'to {target_offset}' if 'to ' in instruction.argrepr else target_offset
                    new_text = f'<a href="#offset_{target_offset}" style="color: {instr_color}; text-decoration: underline;" title="Jump to offset {target_offset}">{target_offset}</a>'
                    if 'to ' in instruction.argrepr:
                        new_text = f'to {new_text}'
                    argrepr_text = argrepr_text.replace(old_text, new_text)
        
        elif instruction.instruction_type.name == 'CALL' and instruction.argval:
            func_name = instruction.argval
            is_internal = any(func.name == func_name for func in analysis.functions)
            href = f"#func_{func_name}" if is_internal else f"#call_{func_name}"
            title = f"Go to {func_name} definition" if is_internal else f"Find all calls to {func_name}"
            argrepr_text = argrepr_text.replace(
                func_name,
                f'<a href="{href}" style="color: {instr_color}; text-decoration: underline;" title="{title}">{func_name}</a>'
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
            if instruction.instruction_type.name in ['LOAD', 'STORE']:
                context = self._find_variable_context(instruction.argval, analysis)
                if context:
                    tooltip_parts.append(f"Context: {context}")
        
        if instruction.is_jump_target:
            tooltip_parts.append("🎯 Jump Target")
        
        return " | ".join(tooltip_parts)
    
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
    
    def handle_bytecode_link(self, url):
        """Handle clicking on bytecode navigation links"""
        url_str = url.toString()
        
        if url_str.startswith('#offset_'):
            self._scroll_to_anchor(url_str)
        elif url_str.startswith('#var_'):
            if '_' in url_str[5:]:
                self._scroll_to_anchor(url_str)
            else:
                var_name = url_str[5:]
                self._highlight_variable_uses(var_name)
        elif url_str.startswith('#func_'):
            self._scroll_to_anchor(url_str)
        elif url_str.startswith('#call_'):
            func_name = url_str[6:]
            self._highlight_function_calls(func_name)
        elif url_str.startswith('#instr_'):
            self._scroll_to_anchor(url_str)
        elif url_str.startswith('#var_usage_'):
            var_name = url_str[11:]
            self._highlight_variable_uses(var_name)
        elif url_str.startswith('#disasm_'):
            self._scroll_to_anchor(url_str)
    
    def apply_theme(self):
        """Apply current theme to the widget"""
        colors = theme_manager.get_colors()
        
        text_style = f"""
            QTextEdit {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
                padding: 5px;
                font-family: '{theme_manager.current_font_family}', monospace;
                font-size: {max(7.5, theme_manager.current_font_size * 0.8)}pt;
                color: {colors['text']};
            }}
        """
        
        text_widgets = [
            self.ast_text, self.dis_text, self.analysis_text,
            self.cpp_ast_text, self.cpp_asm_text, self.cpp_analysis_text,
            self.rust_hir_text, self.rust_mir_text, self.rust_llvm_text, self.rust_analysis_text,
            self.triton_ast_text, self.triton_ptx_text, self.triton_perf_text,
            self.error_text
        ]
        
        for widget in text_widgets:
            widget.setStyleSheet(text_style)
        
        tab_style = f"""
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                border-radius: 5px;
                background-color: {colors['background']};
            }}
            QTabBar::tab {{
                background-color: {colors['button_bg']};
                color: white;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-family: '{theme_manager.current_font_family}';
                font-size: {max(7.5, theme_manager.current_font_size * 0.7)}pt;
            }}
            QTabBar::tab:selected {{
                background-color: {colors['primary']};
            }}
            QTabBar::tab:hover {{
                background-color: {colors['button_hover']};
            }}
        """
        
        for tab_widget in [self.main_tab_widget, self.python_tab_widget, self.cpp_tab_widget, self.rust_tab_widget, self.triton_tab_widget]:
            tab_widget.setStyleSheet(tab_style)
        
        self.status_label.setStyleSheet(theme_manager.get_widget_style('label', font_size=7.5, padding=5))
