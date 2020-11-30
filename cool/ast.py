# AST Classes
class Node:
    pass

class Program(Node):
    def __init__(self, declarations):
        self.declarations = declarations
        self.line = declarations[0].line
        self.column = declarations[0].column

class ClassDeclaration(Node):
    def __init__(self, idx, features, parent=None):
        self.id = idx
        self.parent = parent
        self.features = features
        self.line = idx.line
        self.column = idx.column

class AttrDeclaration(Node):
    def __init__(self, idx, typex, expression=None):
        self.id = idx
        self.type = typex
        self.expression = expression
        self.line = idx.line
        self.column = idx.column

class FuncDeclaration(Node):
    def __init__(self, idx, params, return_type, body):
        self.id = idx
        self.params = params
        self.type = return_type
        self.body = body
        self.line = idx.line
        self.column = idx.column

class Expression(Node):
    pass

class IfThenElse(Expression):
    def __init__(self, condition, if_body, else_body):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        self.line = condition.line
        self.column = condition.column

class WhileLoop(Expression):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
        self.line = condition.line
        self.column = condition.column
        
class Block(Expression):
    def __init__(self, expressions):
        self.expressions = expressions
        self.line = expressions[-1].line
        self.column = expressions[-1].column

class LetIn(Expression):
    def __init__(self, let_body, in_body):
        self.let_body = let_body
        self.in_body = in_body
        self.line = in_body.line
        self.column = in_body.column

class CaseOf(Expression):
    def __init__(self, expression, branches):
        self.expression = expression
        self.branches = branches
        self.line = expression.line
        self.column = expression.column

class Assign(Expression):
    def __init__(self, idx, expression):
        self.id = idx
        self.expression = expression
        self.line = idx.line
        self.column = idx.column

class Unary(Expression):
    def __init__(self, expression):
        self.expression = expression
        self.line = expression.line
        self.column = expression.column

class Not(Unary):
    pass

class Binary(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.line = left.line
        self.column = left.column

class LessEqual(Binary):
    pass

class Less(Binary):
    pass

class Equal(Binary):
    pass

class Arithmetic(Binary):
    pass

class Plus(Arithmetic):
    pass

class Minus(Arithmetic):
    pass

class Star(Arithmetic):
    pass

class Div(Arithmetic):
    pass

class IsVoid(Unary):
    pass

class Complement(Unary):
    pass

class FunctionCall(Expression):
    def __init__(self, obj, idx, args, typex=None):
        self.obj = obj
        self.id = idx
        self.args = args
        self.type = typex
        self.line = idx.line
        self.column = idx.column

class MemberCall(Expression):
    def __init__(self, idx, args):
        self.id = idx
        self.args = args
        self.line = idx.line
        self.column = idx.column

class New(Expression):
    def __init__(self, typex):
        self.type = typex
        self.line = typex.line
        self.column = typex.column

class Atomic(Expression):
    def __init__(self, token):
        self.token = token
        self.line = token.line
        self.column = token.column

class Integer(Atomic):
    pass

class Id(Atomic):
    pass

class String(Atomic):
    pass

class Bool(Atomic):
    pass
