"""
Nodes of AST of vsl
"""


def only_contains(_list, _type):
    """
    Return True if a list only contains _type instances or
    instances' types are the subclasses of _type
    :param _list:
    :param _type:
    :return:
    """
    for instance in _list:
        if not isinstance(instance, _type) or not issubclass(type(instance), _type):
            return False
    return True


class ASTNode(object):
    def to_json(self):
        """
        Return a json dump-able value for AST visualizing
        :return:
        """
        pass


class Statement(ASTNode):
    pass


class Program(ASTNode):
    def __init__(self, function_list):
        assert only_contains(function_list, FunctionDefinition)

        self.function_list = function_list

    def to_json(self):
        return {'program': [item.to_json() for item in self.function_list]}


class FunctionDefinition(ASTNode):
    def __init__(self, name, parameter_list, body):
        assert isinstance(name, ID)
        assert only_contains(parameter_list, ID)
        assert issubclass(type(body), Block)

        self.name = name
        self.parameter_list = parameter_list
        self.body = body

    def to_json(self):
        return {'function_definition': {
            'name': self.name.to_json(),
            'parameter_list': [item.to_json() for item in self.parameter_list],
            'body': self.body.to_json(),
        }}


class Block(ASTNode):
    def __init__(self, declaration_list, statement_list):
        assert only_contains(declaration_list, VariableDeclaration)
        assert only_contains(statement_list, Statement)

        self.declaration_list = declaration_list
        self.statement_list = statement_list

    def to_json(self):
        return {'block': {
            'declaration_list': [item.to_json() for item in self.declaration_list],
            'statement_list': [item.to_json() for item in self.statement_list],
        }}


class VariableDeclaration(ASTNode):
    def __init__(self, variable_list):
        assert only_contains(variable_list, ID)

        self.variable_list = variable_list

    def to_json(self):
        return {'variable_declaration': {
            'variable_list': [item.to_json() for item in self.variable_list]
        }}


class AssignStatement(Statement):
    def __init__(self, left_variable, right_expression):
        assert isinstance(left_variable, ID)
        assert issubclass(type(right_expression), Expression)

        self.left_variable = left_variable
        self.right_expression = right_expression

    def to_json(self):
        return {'assign_statement': {
            'left_variable': self.left_variable.to_json(),
            'right_expression': self.right_expression.to_json(),
        }}


class IfStatement(Statement):
    def __init__(self, test, then_block, else_block=None):
        assert issubclass(type(test), Expression)
        assert isinstance(then_block, Block)
        if else_block:
            assert isinstance(else_block, Block)

        self.test = test
        self.then_block = then_block
        self.else_block = else_block

    def to_json(self):
        return {'if_statement': {
            'test': self.test.to_json(),
            'then_block': self.then_block.to_json(),
            'else_block': self.else_block.to_json() if self.else_block is not None else None,
        }}


class WhileStatement(Statement):
    def __init__(self, test, block):
        assert issubclass(type(test), Expression)
        assert isinstance(block, Block)

        self.test = test
        self.block = block

    def to_json(self):
        return {'while_statement': {
            'test': self.test.to_json(),
            'block': self.block.to_json(),
        }}


class ReturnStatement(Statement):
    def __init__(self, expression):
        assert issubclass(type(expression), Expression)

        self.expression = expression

    def to_json(self):
        return {'return_statement': {
            'expression': self.expression.to_json(),
        }}


class PrintStatement(Statement):
    def __init__(self, print_list):
        assert isinstance(print_list, list)  # Though print_list should only contain expression and TEXT

        self.print_list = print_list

    def to_json(self):
        return {'print_statement': {
            'print_list': [item.to_json() for item in self.print_list],
        }}


class Expression(ASTNode):
    minus_flag = False  # Remind to check this in codegen

    def change_minus_flag(self):
        """
        Every time we meet UMINUS, call this function
        :return:
        """
        self.minus_flag = not self.minus_flag


class BinaryOperation(Expression):
    def __init__(self, left_expression, operator, right_expression):
        assert issubclass(type(left_expression), Expression)
        assert operator in ('+', '-', '*', '/',)

        self.left_expression = left_expression
        self.right_expression = right_expression
        self.operator = operator

    def to_json(self):
        return {'binary_operation': {
            'left_expression': self.left_expression.to_json(),
            'operator': self.operator,
            'right_expression': self.right_expression.to_json(),
        }}


class Number(Expression):
    def __init__(self, value):
        # p[index] lost the LexToken object, only returns the value of it
        assert isinstance(value, float)

        self.value = value

    def to_json(self):
        return {'number': self.value}


class ID(Expression):
    def __init__(self, name):
        # p[index] lost the LexToken object, only returns the value of it
        assert isinstance(name, str)

        self.name = name

    def to_json(self):
        return {'id': self.name}


class FunctionCall(Expression):
    def __init__(self, name, argument_list):
        assert isinstance(name, ID)
        assert argument_list is None or only_contains(argument_list, Expression)

        self.name = name
        self.argument_list = argument_list

    def to_json(self):
        return {'function_call': {
            'name': self.name.to_json(),
            'argument_list': [item.to_json() for item in self.argument_list],
        }}


class Text(ASTNode):
    def __init__(self, value):
        assert isinstance(value, str)

        self.value = value

    def to_json(self):
        return {'text': self.value}
