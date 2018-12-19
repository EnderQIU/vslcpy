"""
lex.py

Tokenizer for vslc

parameters for build():
 debug=1: Enable debug features
 optimize=1: Force set -o option to 1 when specifying -o option to python
"""
import ply.lex as lex

from config import lexer_debug, lexer_optimize


class VSLCLexer(object):

    lexer = None  # Wait to be initialized

    # All lexers must provide a list `tokens` that defines all of the possible token names
    #  that can be produced by the lexer.
    tokens = [
        'NUMBER',   # [0-9]*
        'PLUS',     # +
        'MINUS',    # -
        'TIMES',    # *
        'DIVIDE',   # /
        'LPAREN',   # (
        'RPAREN',   # )
        'LBRACK',   # {
        'RBRACK',   # }
        'ASSIGN',   # :=
        'COMMA',    # ,
        'TEXT',     # ".*"
        'ID',       # [A-Za-z]([A-Za-z]|[0-9])*
    ]

    # To handle reserved words (keywords), you should write a single rule to match an identifier
    #  and do a special name lookup in a function
    reserved = {
        'FUNC': 'FUNC',
        'VAR': 'VAR',
        'PRINT': 'PRINT',
        'RETURN': 'RETURN',

        'IF': 'IF',
        'THEN': 'THEN',
        'ELSE': 'ELSE',
        'FI': 'FI',

        'WHILE': 'WHILE',
        'DO': 'DO',
        'DONE': 'DONE',
    }

    tokens += list(reserved.values())

    # Regular expression rules for simple tokens
    # Each token is specified by writing a regular expression rule compatible with Python's re module.
    # Each of these rules are defined by making declarations with a special prefix t_ to indicate that
    #  it defines a token.
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACK = r'\{'
    t_RBRACK = r'\}'
    t_ASSIGN = r':='
    t_COMMA = r','
    t_TEXT = r'\"([^\\\n]|(\\.))*?\"'

    # Build the lexer
    def build(self):
        self.lexer = lex.lex(module=self, debug=lexer_debug, optimize=lexer_optimize)

    # Test it output
    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)

    # If some kind of action needs to be performed, a token rule can be specified as a function.
    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = self.reserved.get(t.value, 'ID')  # Check for reserved words
        return t

    def t_NUMBER(self, t):
        r'\d+\.?\d*'
        t.value = float(t.value)
        return t

    def t_COMMENT(self, t):
        r'(//.*?(\n|$))'
        # still +1 lino
        t.lexer.lineno += 1

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Since column information is often only useful in the context of error handling,
    #  calculating the column position can be performed when needed as opposed to doing it for each token.
    @staticmethod
    def find_column(_input, token):
        """
        Compute column.
        :param _input: the input text string
        :param token: a token instance
        :return:
        """
        line_start = _input.rfind('\n', 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1
