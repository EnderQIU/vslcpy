import platform
import random
import string

from llvmlite._version import get_versions as llvmlite_version


def predict_start(code):
    """
    predict start symbol by the input code
    :param code: 
    :return: 
    """
    assert isinstance(code, str)

    if code.startswith('FUNC'):
        return 'function_list'
    else:
        return 'block'


def error_print(output, **kwargs):
    """
    print in red text color
    :param output:
    :param kwargs:
    :return:
    """
    assert isinstance(output, str)

    print('\033[91m{}\033[0m'.format(output), **kwargs)


def hello():
    print('VSLC v0.0.1 shell mode')
    print('[llvmlite {version} (Python {python_version})] on {system}'.format(
        version=llvmlite_version()['version'],
        system=platform.system(),
        python_version=platform.python_version(),
    ))
    print("Type '\\' at the end of line for multi-line input.")
    print("Type 'H' for more help.")


def print_help():
    """
    Print help message
    :return:
    """
    print("""Usage:
    (H)elp for this message
    (P)rint LLVM IR code of the module
    (E)xecute current LLVM IR code
    (Q)uit shell
    
    """)


def ran6():
    """
    Generate a random 6 chars
    :return:
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
