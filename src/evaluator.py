from ctypes import CFUNCTYPE, c_double

import llvmlite.binding as llvm
from llvmlite import ir

import config


class VSLCEvaluator(object):
    """Evaluator for VSLC IR code

    """
    def __init__(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        self.target = llvm.Target.from_default_triple()

    def evaluate(self, module):
        assert isinstance(module, ir.Module)

        # Convert LLVM IR into in-memory representation
        llvmmod = llvm.parse_assembly(str(module))

        if config.llvmdump:
            print('======== Unoptimized LLVM IR ========')
            print(str(module))

        if config.llvm_optimize:
            pmb = llvm.create_pass_manager_builder()
            pmb.opt_level = 2
            pm = llvm.create_module_pass_manager()
            pmb.populate(pm)
            pm.run(llvmmod)

            if config.llvmdump:
                print('======== Optimized LLVM IR ========')
                print(str(llvmmod))

        # Create a MCJIT execution engine to JIT-compile the module. Note that
        # ee takes ownership of target_machine, so it has to be recreated anew
        # each time we call create_mcjit_compiler.
        target_machine = self.target.create_target_machine()
        with llvm.create_mcjit_compiler(llvmmod, target_machine) as ee:
            ee.finalize_object()

            if config.llvmdump:
                print('======== Machine code ========')
                print(target_machine.emit_assembly(llvmmod))

            fptr = CFUNCTYPE(c_double)(ee.get_function_address('main'))
            result = fptr()
            return result

    def compile_to_object_code(self, module):
        """Compile previously evaluated code into an object file.

        """
        target_machine = self.target.create_target_machine(codemodel='small')

        # Convert LLVM IR into in-memory representation
        llvmmod = llvm.parse_assembly(str(module))
        return target_machine.emit_object(llvmmod)
