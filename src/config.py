"""
config.py

Global configuration of VSLC
"""

# This will produce various sorts of debugging information including all of the added rules,
# the master regular expressions used by the lexer, and tokens generating during lexing.
lexer_debug = True

# This will print the information of tracking down shift/reduce and reduce/reduce conflicts
# using an LR parsing algorithm and generate a 'parser.out' file in the current directory.
parser_debug = True

#
lexer_optimize = False

#
parser_optimize = False

# The resulting parsing table will be written to a file called parsetab.py.
# If you disable table generation, yacc() will regenerate the parsing tables each time it runs
# (which may take awhile depending on how large your grammar is).
write_table = True

# Enable optimize passed of LLVM
llvm_optimize = False

# Dump binary code after evaluate
llvmdump = True

# Main function name
main_function_name = 'main'

# Float print format
# %.nf for keeping 'n' decimal(s)
float_format = '%.1f'
