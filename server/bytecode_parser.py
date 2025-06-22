"""
Bytecode Parser and Representation
Parses Python bytecode disassembly into structured data for analysis and visualization.
"""

import re
import dis
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Any
from enum import Enum


class InstructionType(Enum):
    """Categories of bytecode instructions"""
    LOAD = "load"
    STORE = "store"
    CALL = "call"
    JUMP = "jump"
    COMPARE = "compare"
    BINARY_OP = "binary_op"
    BUILD = "build"
    RETURN = "return"
    LOOP = "loop"
    OTHER = "other"


@dataclass
class BytecodeInstruction:
    """Represents a single bytecode instruction"""
    offset: int
    opname: str
    arg: Optional[int]
    argval: Optional[str]
    argrepr: str
    line_number: Optional[int]
    is_jump_target: bool
    instruction_type: InstructionType
    
    def __str__(self):
        target_marker = ">>" if self.is_jump_target else "  "
        line_info = f"({self.line_number:3d})" if self.line_number else "     "
        
        if self.arg is not None:
            return f"{target_marker} {self.offset:4d} {self.opname:<20} {self.arg:4d} {self.argrepr}"
        else:
            return f"{target_marker} {self.offset:4d} {self.opname:<20}"


@dataclass
class FunctionInfo:
    """Information about a function in the bytecode"""
    name: str
    code_object: Any
    function_object: Optional[Any]  # The actual callable function object
    start_offset: int
    varnames: List[str]  # Local variables
    names: List[str]     # Global names
    freevars: List[str]  # Free variables (nonlocals)
    cellvars: List[str]  # Cell variables
    constants: List[Any] # Constants
    argcount: int
    kwonlyargcount: int
    instructions: List[BytecodeInstruction]

@dataclass
class BytecodeAnalysis:
    """Analysis results for bytecode"""
    instructions: List[BytecodeInstruction]
    jump_targets: Set[int]
    local_vars: Set[str]
    global_vars: Set[str]
    constants: Set[str]
    function_calls: List[str]
    functions: List[FunctionInfo]  # All functions found in the code
    main_function: Optional[FunctionInfo]  # The main module function
    


class BytecodeParser:
    """Parses dis.dis() output into structured data"""
    
    METADATA_EXTRACTORS = {
        ('LOAD_FAST', 'STORE_FAST'): 'local_vars',
        ('LOAD_GLOBAL', 'STORE_GLOBAL'): 'global_vars',
        ('LOAD_CONST',): 'constants'
    }
    
    INSTRUCTION_TYPES = {
        InstructionType.LOAD: {
            'LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 
            'LOAD_DEREF', 'LOAD_CLOSURE'
        },
        InstructionType.STORE: {
            'STORE_NAME', 'STORE_GLOBAL', 'STORE_FAST', 'STORE_DEREF',
            'STORE_SUBSCR', 'STORE_ATTR'
        },
        InstructionType.CALL: {
            'CALL_FUNCTION', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
            'CALL_METHOD', 'CALL'
        },
        InstructionType.JUMP: {
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT',
            'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 
            'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
            'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP', 'FOR_ITER', 'SETUP_LOOP',
            'BREAK_LOOP', 'CONTINUE_LOOP', 'SETUP_EXCEPT', 'SETUP_FINALLY', 'SETUP_WITH',
            'SETUP_ASYNC_WITH', 'BEFORE_ASYNC_WITH', 'END_ASYNC_FOR'
        },
        InstructionType.COMPARE: {
            'COMPARE_OP', 'IS_OP', 'CONTAINS_OP'
        },
        InstructionType.BINARY_OP: {
            'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
            'BINARY_MODULO', 'BINARY_POWER', 'BINARY_AND', 'BINARY_OR', 'BINARY_XOR'
        },
        InstructionType.BUILD: {
            'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP',
            'BUILD_SLICE', 'UNPACK_SEQUENCE'
        },
        InstructionType.RETURN: {
            'RETURN_VALUE', 'YIELD_VALUE'
        },
        InstructionType.LOOP: {
            'GET_ITER', 'FOR_ITER'
        }
    }
    
    def __init__(self):
        self.instruction_map = self._build_instruction_map()
    
    def _build_instruction_map(self) -> Dict[str, InstructionType]:
        """Build mapping from instruction name to type"""
        mapping = {}
        for instr_type, instructions in self.INSTRUCTION_TYPES.items():
            for instr in instructions:
                mapping[instr] = instr_type
        return mapping
    
    def parse_disassembly(self, dis_output: str) -> BytecodeAnalysis:
        """Parse dis.dis() output into structured bytecode representation"""
        lines = dis_output.strip().split('\n')
        jump_targets = self._extract_jump_targets(lines)
        
        analysis = self._create_base_analysis()
        analysis.jump_targets = jump_targets
        
        for line in lines:
            instruction = self._parse_instruction_line(line, jump_targets)
            if instruction:
                analysis.instructions.append(instruction)
                self._extract_metadata(instruction, analysis.local_vars, analysis.global_vars, 
                                     analysis.constants, analysis.function_calls)
        
        return analysis
    
    def analyze_code_object(self, code_obj, source_code: str = "", function_objects: Dict[str, Any] = None) -> BytecodeAnalysis:
        """Analyze a code object directly to get detailed function information"""
        if function_objects is None:
            function_objects = {}
        
        functions = []
        main_function = self._analyze_single_function(code_obj, "<module>", 0, function_objects.get("<module>"))
        functions.append(main_function)
        
        self._find_nested_functions(code_obj, functions, len(main_function.instructions), function_objects)
        
        return self._build_analysis_from_functions(functions, main_function)
    
    def _analyze_single_function(self, code_obj, name: str, offset_base: int, function_object: Any) -> FunctionInfo:
        """Analyze a single function's code object"""
        instructions = []
        
        # Get bytecode instructions using dis module
        bytecode_iter = dis.Bytecode(code_obj)
        
        for instr in bytecode_iter:
            # Convert dis.Instruction to our BytecodeInstruction
            instruction_type = self.instruction_map.get(instr.opname, InstructionType.OTHER)
            
            bytecode_instr = BytecodeInstruction(
                offset=instr.offset + offset_base,
                opname=instr.opname,
                arg=instr.arg,
                argval=instr.argval,
                argrepr=instr.argrepr,
                line_number=instr.starts_line,
                is_jump_target=instr.is_jump_target,
                instruction_type=instruction_type
            )
            instructions.append(bytecode_instr)
        
        return FunctionInfo(
            name=name,
            code_object=code_obj,
            function_object=function_object,
            start_offset=offset_base,
            varnames=list(code_obj.co_varnames),
            names=list(code_obj.co_names),
            freevars=list(code_obj.co_freevars),
            cellvars=list(code_obj.co_cellvars),
            constants=list(code_obj.co_consts),
            argcount=code_obj.co_argcount,
            kwonlyargcount=getattr(code_obj, 'co_kwonlyargcount', 0),
            instructions=instructions
        )
    
    def _find_nested_functions(self, code_obj, functions: List[FunctionInfo], offset_base: int, function_objects: Dict[str, Any]):
        """Recursively find nested functions in constants"""
        for const in code_obj.co_consts:
            if hasattr(const, 'co_code'):
                func_name = const.co_name
                func_obj = function_objects.get(func_name)
                nested_func = self._analyze_single_function(const, func_name, offset_base, func_obj)
                functions.append(nested_func)
                
                self._find_nested_functions(const, functions, offset_base + len(nested_func.instructions) * 2, function_objects)
                offset_base += len(nested_func.instructions) * 2
    
    def _parse_instruction_line(self, line: str, jump_targets: Set[int]) -> Optional[BytecodeInstruction]:
        """Parse a single line of disassembly output"""
        line = line.strip()
        if not line or line.startswith('Disassembly'):
            return None
        
        is_jump_target = line.startswith('>>')
        if is_jump_target:
            line = line[2:].strip()
        
        parts = line.split()
        if len(parts) < 2:
            return None
        
        try:
            offset = int(parts[0])
            opname = parts[1]
            arg = int(parts[2]) if len(parts) > 2 else None
        except (ValueError, IndexError):
            return None
        
        argrepr = ' '.join(parts[3:]) if len(parts) > 3 else ""
        
        # Extract line number and argval inline
        line_number = None
        if '(' in line and ')' in line:
            match = re.search(r'\((\d+)\)', line)
            if match:
                line_number = int(match.group(1))
        
        argval = None
        if '(' in argrepr and ')' in argrepr:
            match = re.search(r'\(([^)]+)\)', argrepr)
            if match:
                argval = match.group(1)
        
        return BytecodeInstruction(
            offset=offset,
            opname=opname,
            arg=arg,
            argval=argval,
            argrepr=argrepr,
            line_number=line_number,
            is_jump_target=is_jump_target,
            instruction_type=self.instruction_map.get(opname, InstructionType.OTHER)
        )
    
    def _extract_metadata(self, instruction: BytecodeInstruction, 
                         local_vars: Set[str], global_vars: Set[str], 
                         constants: Set[str], function_calls: List[str]):
        """Extract variable names, constants, and function calls from instruction"""
        if not instruction.argval:
            return
        
        # Use lookup table for metadata extraction
        for opcodes, var_type in self.METADATA_EXTRACTORS.items():
            if instruction.opname in opcodes:
                if var_type == 'local_vars':
                    local_vars.add(instruction.argval)
                elif var_type == 'global_vars':
                    global_vars.add(instruction.argval)
                elif var_type == 'constants':
                    constants.add(instruction.argval)
                return
        
        if instruction.instruction_type == InstructionType.CALL:
            function_calls.append(instruction.argval)
    
    def format_analysis_summary(self, analysis: BytecodeAnalysis) -> str:
        """Format a summary of the bytecode analysis"""
        summary = []
        summary.append(f"📊 Bytecode Analysis Summary")
        summary.append(f"{'='*40}")
        summary.append(f"Total Instructions: {len(analysis.instructions)}")
        summary.append(f"Jump Targets: {len(analysis.jump_targets)}")
        summary.append("")
        
        summary.append(f"🔄 Instruction Breakdown:")
        type_counts = {}
        for instr in analysis.instructions:
            type_counts[instr.instruction_type] = type_counts.get(instr.instruction_type, 0) + 1
        
        for instr_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            summary.append(f"  {instr_type.value.title()}: {count}")
        
        summary.append("")
        summary.append(f"📦 Variables & Constants:")
        summary.append(f"  Local Variables: {', '.join(sorted(analysis.local_vars)) if analysis.local_vars else 'None'}")
        summary.append(f"  Global Variables: {', '.join(sorted(analysis.global_vars)) if analysis.global_vars else 'None'}")
        summary.append(f"  Constants: {len(analysis.constants)} items")
        
        if analysis.function_calls:
            summary.append("")
            summary.append(f"📞 Function Calls:")
            for call in analysis.function_calls[:10]:  # Show first 10
                summary.append(f"  {call}")
            if len(analysis.function_calls) > 10:
                summary.append(f"  ... and {len(analysis.function_calls) - 10} more")
        
        # Add jump analysis
        jumps = [i for i in analysis.instructions if i.instruction_type == InstructionType.JUMP]
        if jumps:
            summary.append("")
            summary.append(f"🔀 Jump Analysis:")
            summary.append(f"  Total Jumps: {len(jumps)}")
            
            # Group jumps by type
            jump_types = {}
            for jump in jumps:
                jump_types[jump.opname] = jump_types.get(jump.opname, 0) + 1
            
            for jump_type, count in sorted(jump_types.items()):
                summary.append(f"    {jump_type}: {count}")
        
        # Add complexity metrics
        summary.append("")
        summary.append(f"📈 Complexity Metrics:")
        summary.append(f"  Cyclomatic Complexity: {self._calculate_cyclomatic_complexity(analysis)}")
        summary.append(f"  Load/Store Ratio: {self._calculate_load_store_ratio(analysis)}")
        
        return '\n'.join(summary)
    
    def _create_base_analysis(self) -> BytecodeAnalysis:
        """Create a base BytecodeAnalysis with empty collections"""
        return BytecodeAnalysis(
            instructions=[],
            jump_targets=set(),
            local_vars=set(),
            global_vars=set(),
            constants=set(),
            function_calls=[],
            functions=[],
            main_function=None
        )
    
    def _calculate_cyclomatic_complexity(self, analysis: BytecodeAnalysis) -> int:
        """Calculate approximate cyclomatic complexity from bytecode"""
        decision_points = len([instr for instr in analysis.instructions 
                             if instr.opname in ['POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE', 
                                               'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP']])
        return decision_points + 1
    
    def _extract_jump_targets(self, lines: List[str]) -> Set[int]:
        """Extract jump targets from disassembly lines"""
        jump_targets = set()
        for line in lines:
            if '>>' in line:
                match = re.search(r'>>\s*(\d+)', line)
                if match:
                    jump_targets.add(int(match.group(1)))
        return jump_targets
    
    def _build_analysis_from_functions(self, functions: List[FunctionInfo], main_function: FunctionInfo) -> BytecodeAnalysis:
        """Build BytecodeAnalysis from function list"""
        all_instructions = []
        jump_targets = set()
        local_vars = set()
        global_vars = set()
        constants = set()
        function_calls = []
        
        for func in functions:
            all_instructions.extend(func.instructions)
            local_vars.update(func.varnames)
            global_vars.update(func.names)
            constants.update(str(c) for c in func.constants if c is not None)
            
            for instr in func.instructions:
                if instr.instruction_type == InstructionType.CALL and instr.argval:
                    function_calls.append(instr.argval)
                if instr.is_jump_target:
                    jump_targets.add(instr.offset)
        
        return BytecodeAnalysis(
            instructions=all_instructions,
            jump_targets=jump_targets,
            local_vars=local_vars,
            global_vars=global_vars,
            constants=constants,
            function_calls=function_calls,
            functions=functions,
            main_function=main_function
        )
    
    def _calculate_load_store_ratio(self, analysis: BytecodeAnalysis) -> str:
        """Calculate ratio of load to store operations"""
        loads = len([i for i in analysis.instructions if i.instruction_type == InstructionType.LOAD])
        stores = len([i for i in analysis.instructions if i.instruction_type == InstructionType.STORE])
        
        if stores == 0:
            return f"{loads}:0 (all loads)" if loads > 0 else "0:0"
        
        ratio = loads / stores
        return f"{loads}:{stores} ({ratio:.2f}:1)"
