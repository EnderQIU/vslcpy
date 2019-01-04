"""
yacc.py

We use non-terminators' names from the grammar definitions of VSL

Example:
 def p_expression_plus(p):
     'expression : expression PLUS term'
     #   ^            ^        ^    ^
     #  p[0]         p[1]     p[2] p[3]

     p[0] = p[1] + p[3]

"""
import ply.yacc as yacc

from config import parser_debug, parser_optimize, write_table
from lex import VSLCLexer
from ast import BinaryOperation, Number, ID, FunctionCall, IfStatement, WhileStatement, AssignStatement, \
    VariableDeclaration, Program, FunctionDefinition, Block, PrintStatement, ReturnStatement, Text


class VSLCParser(object):
    tokens = VSLCLexer.tokens  # Get the token map from the lexer.  This is required.

    # Within the precedence declaration, tokens are ordered from lowest to highest precedence
    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'UMINUS'),  # Unary minus operator
    )

    def __init__(self, parser_start='program'):
        assert isinstance(parser_start, str), 'parser_start should be a str'

        self.lexer = VSLCLexer()
        self.lexer.build()  # THIS LINE: Don't forget to build the lexer

        self.parser = yacc.yacc(module=self, start=parser_start, debug=parser_debug, optimize=parser_optimize,
                                write_tables=write_table)

    def parse(self, input=None):
        """
        shortcut for self.lexer.parse()
        :param input:
        :return:
        """
        self.input = input
        return self.parser.parse(input)

    # ======== Start of Parser Definitions ======== #

    # Parse empty production
    def p_empty(self, p):
        'empty :'
        pass

    # Expression stuff
    def p_expression_uminus(self, p):
        'expression : MINUS expression %prec UMINUS'
        p[0] = p[2].change_minus_flag()

    def p_expression_binop(self, p):
        '''expression : expression PLUS expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression
        '''
        p[0] = BinaryOperation(p[1], p[2], p[3])

    def p_expression_group(self, p):
        'expression : LPAREN expression RPAREN'
        p[0] = p[2]

    def p_expression_number(self, p):
        'expression : NUMBER'
        p[0] = Number(p[1])

    def p_expression_id(self, p):
        'expression : ID'
        p[0] = ID(p[1])

    def p_expression_function_call(self, p):
        'expression : ID LPAREN argument_list RPAREN'
        p[0] = FunctionCall(ID(p[1]), p[3])

    def p_argument_list(self, p):
        '''argument_list : empty
                         | expression_list
        '''
        p[0] = p[1]

    def p_expression_list(self, p):
        '''expression_list : expression
                           | expression_list COMMA expression
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    # Top-level program stuff
    def p_program(self, p):
        'program : function_list'
        p[0] = Program(p[1])

    def p_function_list(self, p):
        '''function_list : function_list function
                         | function
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    # function definition stuff
    def p_function(self, p):
        'function : FUNC ID LPAREN variable_list RPAREN LBRACK block RBRACK'
        p[0] = FunctionDefinition(ID(p[2]), p[4], p[7])

    def p_variable_list_variable_list(self, p):
        '''variable_list : empty
                         | ID
                         | variable_list COMMA ID
        '''
        if len(p) == 2:
            if p[1] is not None:  # Handle empty function parameter list
                p[0] = [ID(p[1])]
            else:
                p[0] = []
        else:
            p[0] = p[1] + [ID(p[3])]

    def p_block(self, p):
        'block : declaration_list statement_list'
        p[0] = Block(p[1], p[2])

    # declaration stuff
    def p_declaration_list(self, p):
        '''declaration_list : empty
                            | declaration
                            | declaration_list declaration
        '''
        if len(p) == 2:
            if p[1] is not None:
                p[0] = [p[1]]
            else:
                p[0] = []
        else:
            p[0] = p[1] + [p[2]]

    def p_declaration(self, p):
        'declaration : VAR variable_list'
        p[0] = VariableDeclaration(p[2])

    # statement stuff
    def p_statement_list(self, p):
        '''statement_list : empty
                          | statement
                          | statement_list statement
        '''
        if len(p) == 2:
            if p[1] is not None:
                p[0] = [p[1]]
            else:
                p[0] = []
        else:
            p[0] = p[1] + [p[2]]

    def p_statement(self, p):
        '''statement : assign_statement
                     | return_statement
                     | print_statement
                     | if_statement
                     | while_statement
        '''
        p[0] = p[1]

    def p_assign_statement(self, p):
        'assign_statement : ID ASSIGN expression'
        p[0] = AssignStatement(ID(p[1]), p[3])

    # return statement stuff
    def p_return_statement(self, p):
        'return_statement : RETURN expression'
        p[0] = ReturnStatement(p[2])

    # print statement stuff
    def p_print_statement(self, p):
        'print_statement : PRINT print_list'
        p[0] = PrintStatement(p[2])

    def p_print_statement_print_list(self, p):
        '''print_list : print_item
                      | print_list COMMA print_item
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]  # Will p[1] not be a list?

    def p_print_statement_print_item(self, p):
        '''print_item : expression
                      | TEXT
        '''
        if isinstance(p[1], str):
            p[0] = Text(p[1])
        else:
            p[0] = p[1]

    def p_if_statement(self, p):
        '''if_statement : IF expression THEN block FI
                        | IF expression THEN block ELSE block FI
        '''
        if len(p) == 6:
            p[0] = IfStatement(p[2], p[4])
        else:
            p[0] = IfStatement(p[2], p[4], p[6])

    def p_while_statement(self, p):
        '''while_statement : WHILE expression DO LBRACK block RBRACK DONE
        '''
        p[0] = WhileStatement(p[2], p[5])

    # Error rule for syntax errors
    def p_error(self, p):
        from utils import error_print
        if p:
            error_print("Syntax error at line {line}, column {column}".format(
                line=p.lineno,
                column=VSLCLexer.find_column(self.input, p)
            ))
        else:
            error_print('Syntax error at EOF')
