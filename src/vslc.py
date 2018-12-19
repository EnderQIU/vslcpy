"""
vslc.py

Entry point of vslcpy
"""
import inspect
import sys

from ast import Program

from codegen import LLVMCodeGenerator
from utils import predict_start, error_print, hello, print_help
from yacc import VSLCParser
from evaluator import VSLCEvaluator


def _compile(filename):
    """
    Directly compile the source code from a file
    :param filename: filename of VSL source file
    :return:
    """
    with open(filename, 'r') as source_code_file:
        code = source_code_file.read()

        parser = VSLCParser()
        node = parser.parse(code)

        assert isinstance(node, Program)

        generator = LLVMCodeGenerator('compile', module_name=filename)
        generator.generate_code(node)

        evaluator = VSLCEvaluator()
        obj_code = evaluator.compile_to_object_code(generator.module)

        with open('a.out', 'rb+') as obj_file:
            obj_file.write(obj_code)

        print('Object code has been output to the \'a.out\' file.')


def _iscommand(command, generator):
    """
    Return False if is not a command,
    Otherwise execute the command
    :param command:
    :return:
    """
    commands = ('H', 'P', 'E', 'Q')

    if not command in commands:
        return False

    if command == 'H':
        print_help()
    elif command == 'P':
        print(generator.module)
    elif command == 'E':
        evaluator = VSLCEvaluator()
        evaluator.evaluate(generator.module)
    elif command == 'P':
        print('Good Bye')
        exit(0)
    return True


def _shell():
    """
    Enter the shell mode of VSLC
    :return:
    """
    generator = LLVMCodeGenerator('shell', module_name='<stdin>')  # init llvm before we can interact with the shell
    hello()
    code = ''  # init input data
    while True:
        try:
            line = input('>>> ')
            if line.endswith('\\'):  # enter multiple lines shell mode
                code += line[:-1] + '\n'
                line = input('... ')
                while line != '':
                    code += line.rstrip('\\') + '\n'  # strip the '\' at the end of line and add \n to track the lino
                    line = input('... ')
            elif line == '':  # empty line
                continue
            elif _iscommand(line, generator):  # continue if line is a command
                continue
            else:  # single line input
                code += line

            # parse code
            starting_symbol = predict_start(code)
            parser = VSLCParser(parser_start=starting_symbol)
            node = parser.parse(code)

            # code gen. Only function_list, block and program's code_gen() are public
            generator.generate_code(node)

        except KeyboardInterrupt:  # Ctrl-C triggered
            code = ''
            print()
            print('KeyboardInterrupt. Use Ctrl-D to exit.')
            continue  # skip this input lines
        except EOFError:  # Ctrl-D triggered
            print()
            print('Good Bye')
            exit(0)
        # SystemError should net be handled because it's a programming error
        else:
            # no exception, just flush variable 'code'
            code = ''


def main():
    """
    Main entry of vslc
    :return:
    """
    if len(sys.argv) == 1:
        _shell()
    else:
        _compile(sys.argv[1])


if __name__ == '__main__':
    main()
