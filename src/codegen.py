"""
codegen.py

LLVM IR Code Generation
"""
from llvmlite import ir

from ast import Program, Block, FunctionDefinition, AssignStatement, BinaryOperation, IfStatement, \
    VariableDeclaration, FunctionCall, ReturnStatement, WhileStatement, PrintStatement, Text
import config
from utils import ran6


class CodegenError(Exception):
    pass


class LLVMCodeGenerator(object):
    def __init__(self, mode, module_name=''):
        """Initialize the code generator.

        Because the VSL grammar defined that there's no separated statements in the global
        scope, we make a compromise in order to run the shell mode.

        In 'shell' mode, all codes in the global scope are lying in a predefined function
        named 'main', which is created when the generator init'd.

        Otherwise in the compile mode, we do not allow separated statements in the global
        scope, which is guaranteed by the syntax analysis. So there must be a function
        called 'main' as the entry of the program.
        """
        assert mode in ('shell', 'compile',)

        self.mode = mode
        self.module = ir.Module(module_name)
        if mode == 'shell':
            main_function_type = ir.FunctionType(ir.VoidType(), ())
            main_function = ir.Function(self.module, main_function_type, name=config.main_function_name)

            # The main block start before the return block. The llvmlite stores the blocks
            # in a OrderedDict.
            self.block = main_function.append_basic_block('entry')

            # Current IR builder.
            # In compile mode, it will be init'd at the start of the _codegen_FunctionDefinition().
            # In shell mode, self.builder is init'd here at __init__() of the code generator.
            # But remember to save it when call a _codegen_FunctionDefinition(), then restore it
            # at the end of the _codegen_FunctionDefinition()
            self.builder = ir.IRBuilder(self.block)

            # Generate the ret void code in advance and set the builder to the start of the entry block
            self.builder.ret_void()
            self.builder.position_at_start(self.block)

            # Manages a symbol table while the predefined 'main' function is being codegen'd.
            self.main_symbol_table = {}

            # ========  LLVM IR After __init__('shell')  ===========
            # ; ModuleID = ""
            # target triple = "unknown-unknown-unknown"
            # target datalayout = ""
            #
            # define void @"main"()
            # {
            # entry:
            # ; <= current self.builder should be here
            #   ret void
            # }
            # ======================  END  =========================

        # Manages a symbol table while a function is being codegen'd. Maps var
        # names to ir.Value which represents the var's address (alloca).
        self.function_symbol_table = {}

    def generate_code(self, node):
        assert isinstance(node, (
            Program, Block, list)), 'root node should be one of Program, Block or a list of FunctionDefinition'

        if isinstance(node, list):  # FunctionDefinition in shell mode
            for i in node:
                assert isinstance(i, FunctionDefinition)
                self._codegen(i)
        elif isinstance(node, Program):  # only the program mode will have a Program root node
            self._codegen(node)
        elif isinstance(node, Block):  # shell mode line input. Insert them into the main function
            self._codegen(node)

    def _codegen(self, node):
        """Node visitor. Dispathces upon node type.

        For AST node of class Foo, calls self._codegen_Foo. Each visitor is
        expected to return a llvmlite.ir.Value.
        """
        method = '_codegen_' + node.__class__.__name__
        return getattr(self, method)(node)

    def _codegen_Number(self, node):
        return ir.Constant(ir.DoubleType(), float(node.value))

    def _codegen_Text(self, node):
        assert isinstance(node, Text)

        escaped_text = bytes(node.value.strip('"'), encoding='utf-8').decode('unicode_escape')
        c_str = LLVMCodeGenerator.to_cstr(escaped_text)
        global_fmt = ir.GlobalVariable(self.module, c_str.type, name="fstr_" + ran6())
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_str
        return self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())

    def _codegen_ID(self, node):  # This is ID callee, not declare
        # Find the ID in the function scope first
        if node.name in self.function_symbol_table.keys():
            var_addr = self.function_symbol_table[node.name]
        else:
            # Otherwise try the global scope
            try:
                var_addr = self.main_symbol_table[node.name]
            except KeyError:
                raise CodegenError("NameError: name '{}' is not defined".format(node.name))
        return self.builder.load(var_addr, node.name)

    def _codegen_AssignStatement(self, node):
        assert isinstance(node, AssignStatement)

        # Find the ID in the function scope first. Remember to empty the function_symbol_table
        # when FunctionDefinition finished codegen
        if node.left_variable.name in self.function_symbol_table:
            var_addr = self.function_symbol_table[node.left_variable.name]
        else:
            try:
                var_addr = self.main_symbol_table[node.left_variable.name]
            except KeyError:
                raise CodegenError("NameError: name '{}' is not defined".format(node.left_variable.name))
        right_expression_value = self._codegen(node.right_expression)
        self.builder.store(right_expression_value, var_addr)

    def _codegen_BinaryOperation(self, node):
        assert isinstance(node, BinaryOperation)

        lhs = self._codegen(node.left_expression)
        rhs = self._codegen(node.right_expression)

        if node.operator == '+':
            return self.builder.fadd(lhs, rhs, 'addtmp')
        elif node.operator == '-':
            return self.builder.fsub(lhs, rhs, 'subtmp')
        elif node.operator == '*':
            return self.builder.fmul(lhs, rhs, 'multmp')
        elif node.operator == '/':
            return self.builder.fdiv(lhs, rhs, 'divtmp')
        else:
            raise CodegenError('No such operator: {}'.format(node.operator))

    def _codegen_IfStatement(self, node):
        assert isinstance(node, IfStatement)

        # Floating-point ordered compare lhs with rhs.
        test_gt_0 = self.builder.fcmp_ordered('>', self._codegen(node.test), ir.Constant(ir.DoubleType(), 0.0))

        store_builder = self.builder

        if_block = ir.Block(self.builder.block, name='if_stmt' + ran6())
        self.builder.append_basic_block(if_block)
        self.builder.position_at_start(if_block)
        with self.builder.if_else(test_gt_0) as (then, otherwise):
            with then:
                # emit instructions for when the predicate is true
                self._codegen(node.then_block)
            with otherwise:
                # emit instructions for when the predicate is false
                self._codegen(node.else_block)
        # There are no instructions following the if-else block

    def _codegen_WhileStatement(self, node):
        assert isinstance(node, WhileStatement)
        # TODO

    def _codegen_VariableDeclaration(self, node):
        assert isinstance(node, VariableDeclaration)

        for var in node.variable_list:
            name = var.name

            # Emit the initializer before adding the variable to scope. This
            # prefents the initializer from referencing the variable itself.
            init_val = ir.Constant(ir.DoubleType(), 0.0)  # init values to 0.0

            # Create an alloca for the induction var and store the init value to it.
            # As VSL grammar defined, variable declaration should be before its assignment.
            var_addr = self.builder.alloca(ir.DoubleType(), size=None, name=name)
            self.builder.store(init_val, var_addr)

            # Store the symbol name, address pair into the symbol table.
            # Decided by where the scope you are.
            if self.builder.function._name == 'main':  # TODO check whether the builder is working on the 'main' function
                self.main_symbol_table[name] = var_addr
            else:
                self.function_symbol_table[name] = var_addr

    def _codegen_FunctionCall(self, node):
        assert isinstance(node, FunctionCall)

        # Find the callee in the global scope of the module.
        # Need match the function name and also the number of parameter
        callee_func = self.module.get_global(node.name.name)
        if callee_func is None or not isinstance(callee_func, ir.Function):
            raise CodegenError('Call to unknown function', node.name)
        if node.argument_list is None:
            arglen = 0
        else:
            arglen = len(node.argument_list)
        if len(callee_func.args) != arglen:
            raise CodegenError('Call argument length', len(node.argument_list), 'mismatch', node.name)
        if node.argument_list is None:
            call_args = []
        else:
            call_args = [self._codegen(arg) for arg in node.argument_list]
        return self.builder.call(callee_func, call_args, 'calltmp')

    def _codegen_FunctionDefinition(self, node):
        assert isinstance(node, FunctionDefinition)

        # Create the function skeleton from the prototype. -----------------------
        # Check section before create the new builder and entry block
        function_name = node.name.name
        # Create a function type
        function_type = ir.FunctionType(ir.DoubleType(),
                                        [ir.DoubleType()] * len(node.parameter_list))
        # If a function with this name already exists in the module...
        if function_name in self.module.globals:
            # We don't allow redefine a function with the same name of the defined's
            raise CodegenError('Redefinition of function: {}'.format(function_name))
        else:
            # Otherwise create a new function
            func = ir.Function(self.module, function_type, function_name)
        # ------------------------------------------------------------------------

        # Reset the symbol table. Prototype generation will pre-populate it with
        # function arguments.
        self.function_symbol_table = {}
        # Store the current builder (in main function)
        stored_builder = self.builder

        # Create the entry BB in the function and set the builder to it.
        bb_entry = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(bb_entry)

        # Add all arguments to the symbol table and create their allocas
        for i, arg in enumerate(func.args):
            arg.name = node.parameter_list[i]
            alloca = self.builder.alloca(ir.DoubleType(), name=arg.name)
            self.builder.store(arg, alloca)
            self.function_symbol_table[arg.name.name] = alloca

        # We will handle ReturnStatement in the body of the FunctionDefinition
        self._codegen(node.body)
        # But we finally create a ret instruction here to return 0.0 to handle the case
        # that no ReturnStatement in the body of the FunctionDefinition
        self.builder.ret(ir.Constant(ir.DoubleType(), 0.0))

        # Reset the function symbol table for the reason of @self._codegen_AssignStatement+3
        self.function_symbol_table = {}

        # Restore the builder (in main function)
        self.builder = stored_builder
        return func

    def _codegen_Block(self, node):
        assert isinstance(node, Block)

        # Process each declaration
        for declaration in node.declaration_list:
            self._codegen(declaration)

        # Process each statement
        for statement in node.statement_list:
            self._codegen(statement)

    def _codegen_Program(self, node):
        assert isinstance(node, Program)

        for i in node.function_list:
            self._codegen(i)

    def _codegen_ReturnStatement(self, node):
        assert isinstance(node, ReturnStatement)

        return_value = self._codegen(node.expression)
        self.builder.ret(return_value)

    def _codegen_PrintStatement(self, node):
        assert isinstance(node, PrintStatement)

        voidptr_ty = ir.IntType(8).as_pointer()

        printf = self.module.globals.get('printf', None)
        if not printf:
            printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
            printf = ir.Function(self.module, printf_ty, name="printf")

        format_string = ''
        for i in node.print_list:
            if isinstance(i, Text):
                format_string += '%s'
            else:
                format_string += config.float_format

        c_format_string = LLVMCodeGenerator.to_cstr(format_string)

        # A global format
        global_fmt = ir.GlobalVariable(self.module, c_format_string.type, name="fstr_" + ran6())
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_format_string

        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)
        self.builder.call(printf, [fmt_arg] + [self._codegen(i) for i in node.print_list])

    @staticmethod
    def to_cstr(python_str):
        assert isinstance(python_str, str)

        python_str += '\0'
        return ir.Constant(ir.ArrayType(ir.IntType(8), len(python_str)), bytearray(python_str.encode("utf8")))
