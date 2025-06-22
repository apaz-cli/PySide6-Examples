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
    start_offset: int
    end_offset: int
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
    
    @property
    def loads(self) -> List[BytecodeInstruction]:
        """Get all load instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.LOAD]
    
    @property
    def stores(self) -> List[BytecodeInstruction]:
        """Get all store instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.STORE]
    
    @property
    def calls(self) -> List[BytecodeInstruction]:
        """Get all call instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.CALL]
    
    @property
    def jumps(self) -> List[BytecodeInstruction]:
        """Get all jump instructions"""
        return [instr for instr in self.instructions if instr.instruction_type == InstructionType.JUMP]


class BytecodeParser:
    """Parses dis.dis() output into structured data"""
    
    # Core instruction patterns (stable across Python versions)
    LOAD_INSTRUCTIONS = {
        'LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 
        'LOAD_DEREF', 'LOAD_CLOSURE'
    }
    
    STORE_INSTRUCTIONS = {
        'STORE_NAME', 'STORE_GLOBAL', 'STORE_FAST', 'STORE_DEREF',
        'STORE_SUBSCR', 'STORE_ATTR'
    }
    
    CALL_INSTRUCTIONS = {
        'CALL_FUNCTION', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
        'CALL_METHOD', 'CALL'  # CALL is newer Python versions
    }
    
    JUMP_INSTRUCTIONS = {
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT',
        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 
        'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP', 'FOR_ITER', 'SETUP_LOOP',
        'BREAK_LOOP', 'CONTINUE_LOOP', 'SETUP_EXCEPT', 'SETUP_FINALLY', 'SETUP_WITH',
        'SETUP_ASYNC_WITH', 'BEFORE_ASYNC_WITH', 'END_ASYNC_FOR'
    }
    
    COMPARE_INSTRUCTIONS = {
        'COMPARE_OP', 'IS_OP', 'CONTAINS_OP'
    }
    
    BINARY_INSTRUCTIONS = {
        'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
        'BINARY_MODULO', 'BINARY_POWER', 'BINARY_AND', 'BINARY_OR', 'BINARY_XOR'
    }
    
    BUILD_INSTRUCTIONS = {
        'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP',
        'BUILD_SLICE', 'UNPACK_SEQUENCE'
    }
    
    RETURN_INSTRUCTIONS = {
        'RETURN_VALUE', 'YIELD_VALUE'
    }
    
    LOOP_INSTRUCTIONS = {
        'GET_ITER', 'FOR_ITER'
    }
    
    def __init__(self):
        self.instruction_map = self._build_instruction_map()
    
    def _build_instruction_map(self) -> Dict[str, InstructionType]:
        """Build mapping from instruction name to type"""
        mapping = {}
        
        for instr in self.LOAD_INSTRUCTIONS:
            mapping[instr] = InstructionType.LOAD
        for instr in self.STORE_INSTRUCTIONS:
            mapping[instr] = InstructionType.STORE
        for instr in self.CALL_INSTRUCTIONS:
            mapping[instr] = InstructionType.CALL
        for instr in self.JUMP_INSTRUCTIONS:
            mapping[instr] = InstructionType.JUMP
        for instr in self.COMPARE_INSTRUCTIONS:
            mapping[instr] = InstructionType.COMPARE
        for instr in self.BINARY_INSTRUCTIONS:
            mapping[instr] = InstructionType.BINARY_OP
        for instr in self.BUILD_INSTRUCTIONS:
            mapping[instr] = InstructionType.BUILD
        for instr in self.RETURN_INSTRUCTIONS:
            mapping[instr] = InstructionType.RETURN
        for instr in self.LOOP_INSTRUCTIONS:
            mapping[instr] = InstructionType.LOOP
            
        return mapping
    
    def parse_disassembly(self, dis_output: str) -> BytecodeAnalysis:
        """Parse dis.dis() output into structured bytecode representation"""
        lines = dis_output.strip().split('\n')
        instructions = []
        jump_targets = set()
        local_vars = set()
        global_vars = set()
        constants = set()
        function_calls = []
        
        # First pass: identify jump targets
        for line in lines:
            if '>>' in line:
                match = re.search(r'>>\s*(\d+)', line)
                if match:
                    jump_targets.add(int(match.group(1)))
        
        # Second pass: parse instructions
        for line in lines:
            instruction = self._parse_instruction_line(line, jump_targets)
            if instruction:
                instructions.append(instruction)
                
                # Extract variable and constant information
                self._extract_metadata(instruction, local_vars, global_vars, constants, function_calls)
        
        return BytecodeAnalysis(
            instructions=instructions,
            jump_targets=jump_targets,
            local_vars=local_vars,
            global_vars=global_vars,
            constants=constants,
            function_calls=function_calls,
            functions=[],  # Will be populated by analyze_code_object
            main_function=None
        )
    
    def analyze_code_object(self, code_obj, source_code: str = "") -> BytecodeAnalysis:
        """Analyze a code object directly to get detailed function information"""
        functions = []
        all_instructions = []
        jump_targets = set()
        local_vars = set()
        global_vars = set()
        constants = set()
        function_calls = []
        
        # Analyze main code object
        main_function = self._analyze_single_function(code_obj, "<module>", 0)
        functions.append(main_function)
        
        # Find nested functions by looking for LOAD_CONST instructions with code objects
        self._find_nested_functions(code_obj, functions, len(main_function.instructions))
        
        # Collect all instructions and metadata
        for func in functions:
            all_instructions.extend(func.instructions)
            local_vars.update(func.varnames)
            global_vars.update(func.names)
            constants.update(str(c) for c in func.constants if c is not None)
            
            # Extract function calls from instructions
            for instr in func.instructions:
                if instr.instruction_type == InstructionType.CALL and instr.argval:
                    function_calls.append(instr.argval)
        
        # Collect jump targets
        for instr in all_instructions:
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
    
    def _analyze_single_function(self, code_obj, name: str, offset_base: int) -> FunctionInfo:
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
            start_offset=offset_base,
            end_offset=offset_base + len(instructions) * 2,  # Approximate
            varnames=list(code_obj.co_varnames),
            names=list(code_obj.co_names),
            freevars=list(code_obj.co_freevars),
            cellvars=list(code_obj.co_cellvars),
            constants=list(code_obj.co_consts),
            argcount=code_obj.co_argcount,
            kwonlyargcount=getattr(code_obj, 'co_kwonlyargcount', 0),
            instructions=instructions
        )
    
    def _find_nested_functions(self, code_obj, functions: List[FunctionInfo], offset_base: int):
        """Recursively find nested functions in constants"""
        for const in code_obj.co_consts:
            if hasattr(const, 'co_code'):  # It's a code object
                func_name = const.co_name
                nested_func = self._analyze_single_function(const, func_name, offset_base)
                functions.append(nested_func)
                
                # Recursively find functions within this function
                self._find_nested_functions(const, functions, offset_base + len(nested_func.instructions) * 2)
                offset_base += len(nested_func.instructions) * 2
    
    def _parse_instruction_line(self, line: str, jump_targets: Set[int]) -> Optional[BytecodeInstruction]:
        """Parse a single line of disassembly output"""
        line = line.strip()
        if not line or line.startswith('Disassembly'):
            return None
        
        # Handle jump target marker
        is_jump_target = line.startswith('>>')
        if is_jump_target:
            line = line[2:].strip()
        
        # Parse instruction components
        # Format: offset opname [arg] [argval] [(argrepr)]
        parts = line.split()
        if len(parts) < 2:
            return None
        
        try:
            offset = int(parts[0])
            opname = parts[1]
        except (ValueError, IndexError):
            return None
        
        # Extract line number if present (in parentheses at start)
        line_number = None
        line_match = re.search(r'\((\d+)\)', line)
        if line_match:
            line_number = int(line_match.group(1))
        
        # Extract argument and argument representation
        arg = None
        argval = None
        argrepr = ""
        
        if len(parts) > 2:
            try:
                arg = int(parts[2])
            except ValueError:
                pass
        
        # Extract argument representation (everything after the opname and arg)
        if len(parts) > 3:
            argrepr = ' '.join(parts[3:])
            # Clean up parentheses and extract argval
            if '(' in argrepr and ')' in argrepr:
                argval_match = re.search(r'\(([^)]+)\)', argrepr)
                if argval_match:
                    argval = argval_match.group(1)
        
        # Determine instruction type
        instruction_type = self.instruction_map.get(opname, InstructionType.OTHER)
        
        return BytecodeInstruction(
            offset=offset,
            opname=opname,
            arg=arg,
            argval=argval,
            argrepr=argrepr,
            line_number=line_number,
            is_jump_target=is_jump_target,
            instruction_type=instruction_type
        )
    
    def _extract_metadata(self, instruction: BytecodeInstruction, 
                         local_vars: Set[str], global_vars: Set[str], 
                         constants: Set[str], function_calls: List[str]):
        """Extract variable names, constants, and function calls from instruction"""
        
        if instruction.opname in ['LOAD_FAST', 'STORE_FAST'] and instruction.argval:
            local_vars.add(instruction.argval)
        
        elif instruction.opname in ['LOAD_GLOBAL', 'STORE_GLOBAL'] and instruction.argval:
            global_vars.add(instruction.argval)
        
        elif instruction.opname == 'LOAD_CONST' and instruction.argval:
            constants.add(instruction.argval)
        
        elif instruction.instruction_type == InstructionType.CALL and instruction.argval:
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
        if analysis.jumps:
            summary.append("")
            summary.append(f"🔀 Jump Analysis:")
            summary.append(f"  Total Jumps: {len(analysis.jumps)}")
            
            # Group jumps by type
            jump_types = {}
            for jump in analysis.jumps:
                jump_types[jump.opname] = jump_types.get(jump.opname, 0) + 1
            
            for jump_type, count in sorted(jump_types.items()):
                summary.append(f"    {jump_type}: {count}")
        
        # Add complexity metrics
        summary.append("")
        summary.append(f"📈 Complexity Metrics:")
        summary.append(f"  Cyclomatic Complexity: {self._calculate_cyclomatic_complexity(analysis)}")
        summary.append(f"  Load/Store Ratio: {self._calculate_load_store_ratio(analysis)}")
        
        return '\n'.join(summary)
    
    def _calculate_cyclomatic_complexity(self, analysis: BytecodeAnalysis) -> int:
        """Calculate approximate cyclomatic complexity from bytecode"""
        # Count decision points (jumps + 1)
        decision_points = len([instr for instr in analysis.instructions 
                             if instr.opname in ['POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE', 
                                               'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP']])
        return decision_points + 1
    
    def _calculate_load_store_ratio(self, analysis: BytecodeAnalysis) -> str:
        """Calculate ratio of load to store operations"""
        loads = len(analysis.loads)
        stores = len(analysis.stores)
        
        if stores == 0:
            return f"{loads}:0 (all loads)" if loads > 0 else "0:0"
        
        ratio = loads / stores
        return f"{loads}:{stores} ({ratio:.2f}:1)"
