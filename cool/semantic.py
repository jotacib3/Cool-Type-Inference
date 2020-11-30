from .cmp import visitor, Context, SelfType, AutoType, SemanticError, ErrorType, Scope
from .ast import *

#Primera pasada al ast la cual nos permite recolectar todos los tipos definidos
#igual que en el manual de piad
#Su tarea consiste en crear un contexto, y definir en este contexto todos los tipos
#que se encuentre
class TypeCollectorVisitor:
    def __init__(self, errors=[]):
        self.context = Context()
        self.errors = errors

        # Creating special types
        self.context.add_type(SelfType())
        self.context.add_type(AutoType())

        # Creating built-in types
        self.context.create_type('Object')
        self.context.create_type('IO')
        self.context.create_type('Int')
        self.context.create_type('String')
        self.context.create_type('Bool')
    
    @visitor.on('node')
    def visit(self, node):
        pass
    
    @visitor.when(Program)
    def visit(self, node):       
        for def_class in node.declarations:
            self.visit(def_class)
    
    @visitor.when(ClassDeclaration)
    def visit(self, node):
        self.context.create_type(node.id.lex)
        
#Segunda pasada al ast la cual nos permite agregar al contexto la construccion de metodos
#y atributos
class TypeBuilderVisitor:    
    def __init__(self, context, errors=[]):
        self.context = context
        self.current_type = None
        self.errors = errors

        # Building built-in types
        self.object_type = self.context.get_type('Object')
        
        self.io_type = self.context.get_type('IO')
        self.io_type.set_parent(self.object_type)

        self.int_type = self.context.get_type('Int')
        self.int_type.set_parent(self.object_type)
        self.int_type.sealed = True

        self.string_type = self.context.get_type('String')
        self.string_type.set_parent(self.object_type)
        self.string_type.sealed = True

        self.bool_type = self.context.get_type('Bool')
        self.bool_type.set_parent(self.object_type)
        self.bool_type.sealed = True

        #OBJECT
        self.object_type.define_method('abort', [], [], self.object_type)
        self.object_type.define_method('type_name', [], [], self.string_type)
        self.object_type.define_method('copy', [], [], SelfType())
        
        #IO
        self.io_type.define_method('out_string', ['x'], [self.string_type], SelfType())
        self.io_type.define_method('out_int', ['x'], [self.int_type], SelfType())
        self.io_type.define_method('in_string', [], [], self.string_type)
        self.io_type.define_method('in_int', [], [], self.int_type)

        #STRING
        self.string_type.define_method('length', [], [], self.int_type)
        self.string_type.define_method('concat', ['s'], [self.string_type], self.string_type)
        self.string_type.define_method('substr', ['i', 'l'], [self.int_type, self.int_type], self.string_type)
    
    @visitor.on('node')
    def visit(self, node):
        pass
    
    @visitor.when(Program)
    def visit(self, node):
        for def_class in node.declarations:
            self.visit(def_class)           
    
    @visitor.when(ClassDeclaration)
    def visit(self, node):
        self.current_type = self.context.get_type(node.id.lex)        
        parent = node.parent
        if parent:
            parent_type = self.context.get_type(parent.lex)
            self.current_type.set_parent(parent_type)            
        else:
            self.current_type.set_parent(self.object_type)
        
        for feature in node.features:
            self.visit(feature)
            
    @visitor.when(AttrDeclaration)
    def visit(self, node):
        attr_type = self.context.get_type(node.type.lex)       
        self.current_type.define_attribute(node.id.lex, attr_type)        
        
    @visitor.when(FuncDeclaration)
    def visit(self, node):
        arg_names, arg_types = [], []
        for idx, typex in node.params:
            arg_type = self.context.get_type(typex.lex)               
            arg_names.append(idx.lex)
            arg_types.append(arg_type)

        ret_type = self.context.get_type(node.type.lex)
        self.current_type.define_method(node.id.lex, arg_names, arg_types, ret_type)
        
#la tercera pasada sobre el ast y nos permitira verificar la consistencia de los tipos en todos los nodos del ast
class TypeCheckerVisitor:
    def __init__(self, context, errors=[]):
        self.context = context
        self.current_type = None
        self.current_method = None
        self.errors = errors

        # search built-in types
        self.object_type = self.context.get_type('Object')
        self.io_type = self.context.get_type('IO')
        self.int_type = self.context.get_type('Int')
        self.string_type = self.context.get_type('String')
        self.bool_type = self.context.get_type('Bool')
        
    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(Program)
    def visit(self, node, scope=None):
        scope = Scope()
        for declaration in node.declarations:
            self.visit(declaration, scope.create_child())
        return scope

    @visitor.when(ClassDeclaration)
    def visit(self, node, scope):
        self.current_type = self.context.get_type(node.id.lex)

        # check ciclic heritage
        parent = self.current_type.parent
        while parent:
            if parent == self.current_type:
                self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Type "%s" froms a cyclic heritage chain' % parent.name)
                self.current_type.parent = self.object_type
                break

            parent = parent.parent
        
        for attr in self.current_type.attributes:
            scope.define_variable(attr.name, attr.type)

        for feature in node.features:
            self.visit(feature, scope.create_child())

    @visitor.when(AttrDeclaration)
    def visit(self, node, scope):
        expr = node.expression
        if expr:
            self.visit(expr, scope.create_child())
            expr_type = expr.static_type

            attr = self.current_type.get_attribute(node.id.lex)
            node_type = attr.type
            node_type = self.current_type if isinstance(node_type, SelfType) else node_type
            if not expr_type.conforms_to(node_type):
                self.errors.append('Error on Ln %d, Col %d: ' % (expr.line, expr.column) + 'Cannot convert "%s" into "%s".' % (expr_type.name, node_type.name))
        

    @visitor.when(FuncDeclaration)
    def visit(self, node, scope):
        self.current_method = self.current_type.get_method(node.id.lex)

        # check ilegal redefined func
        parent = self.current_type.parent
        if parent:
            try:
                parent_method = parent.get_method(node.id.lex)
            except SemanticError:
                pass
            else:
                if parent_method.param_types != self.current_method.param_types or parent_method.return_type != self.current_method.return_type:
                     self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Method "%s" of "%s" already defined in "%s" with a different signature.' % (self.current_method.name, self.current_type.name, parent.name))
        
        scope.define_variable('self', self.current_type)
        
        for pname, ptype in zip(self.current_method.param_names, self.current_method.param_types):
            scope.define_variable(pname, ptype)
            
        body = node.body
        self.visit(body, scope.create_child())
            
        body_type = body.static_type
        return_type = self.current_type if isinstance(self.current_method.return_type, SelfType) else self.current_method.return_type
        
        if not body_type.conforms_to(return_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (body.line, body.column) + 'Cannot convert "%s" into "%s".' % (body_type.name, return_type.name))

    @visitor.when(IfThenElse)
    def visit(self, node, scope):
        condition = node.condition
        self.visit(condition, scope.create_child())

        condition_type = condition.static_type
        if not condition_type.conforms_to(self.bool_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (condition.line, condition.column) + 'Cannot convert "%s" into "%s".' % (condition_type.name, self.bool_type.name))

        self.visit(node.if_body, scope.create_child())
        self.visit(node.else_body, scope.create_child())

        if_type = node.if_body.static_type
        else_type = node.else_body.static_type
        node.static_type = if_type.type_union(else_type)

    @visitor.when(WhileLoop)
    def visit(self, node, scope):
        condition = node.condition
        self.visit(condition, scope.create_child())

        condition_type = condition.static_type
        if not condition_type.conforms_to(self.bool_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (condition.line, condition.column) + 'Cannot convert "%s" into "%s".' % (condition_type.name, self.bool_type.name))

        self.visit(node.body, scope.create_child())

        node.static_type = self.object_type

    @visitor.when(Block)
    def visit(self, node, scope):
        for expr in node.expressions:
            self.visit(expr, scope.create_child())

        node.static_type = node.expressions[-1].static_type

    @visitor.when(LetIn)
    def visit(self, node, scope):
        for idx, typex, expr in node.let_body:
            try:
                node_type = self.context.get_type(typex.lex)
            except SemanticError as ex:
                self.errors.append('Error on Ln %d, Col %d: ' % (typex.line, typex.column) + ex.text)
                node_type = ErrorType()
            
            id_type = self.current_type if isinstance(node_type, SelfType) else node_type
            child = scope.create_child()

            if expr:
                self.visit(expr, child)
                expr_type = expr.static_type
                if not expr_type.conforms_to(id_type):
                    self.errors.append('Error on Ln %d, Col %d: ' % (expr.line, expr.column) + 'Cannot convert "%s" into "%s".' % (expr_type.name, id_type.name))

            scope.define_variable(idx.lex, id_type)

        self.visit(node.in_body, scope.create_child())

        node.static_type = node.in_body.static_type

    @visitor.when(CaseOf)
    def visit(self, node, scope):
        self.visit(node.expression, scope.create_child())

        node.static_type = None

        for idx, typex, expr in node.branches:
            try:
                node_type = self.context.get_type(typex.lex)
            except SemanticError as ex:
                self.errors.append('Error on Ln %d, Col %d: ' % (typex.line, typex.column) + ex.text)
                node_type = ErrorType()
            else:
                if isinstance(node_type, SelfType) or isinstance(node_type, AutoType):
                    self.errors.append('Error on Ln %d, Col %d: ' % (typex.line, typex.column) + f'Type "{node_type.name}" canot be used as case branch type')
                    node_type = ErrorType()

            id_type = node_type

            child_scope = scope.create_child()
            child_scope.define_variable(idx.lex, id_type)
            self.visit(expr, child_scope)
            expr_type = expr.static_type

            node.static_type = node.static_type.type_union(expr_type) if node.static_type else expr_type

    @visitor.when(Assign)
    def visit(self, node, scope):
        expression = node.expression
        self.visit(expression, scope.create_child())
        expr_type = expression.static_type
        
        if scope.is_defined(node.id.lex):
            var = scope.find_variable(node.id.lex)
            node_type = var.type       
            
            if var.name == 'self':
                self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Variable "self" is read-only.')
            elif not expr_type.conforms_to(node_type):
                self.errors.append('Error on Ln %d, Col %d: ' % (expression.line, expression.column) + 'Cannot convert "%s" into "%s".' % (expr_type.name, node_type.name))
        else:
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Variable "%s" is not defined in "%s".' % (node.id.lex, self.current_method.name))
        
        node.static_type = expr_type

    @visitor.when(Not)
    def visit(self, node, scope):
        expression = node.expression
        self.visit(expression, scope.create_child())

        expr_type = expression.static_type
        if not expr_type.conforms_to(self.bool_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (expression.line, expression.column) + 'Cannot convert "%s" into "%s".' % (expr_type.name, self.bool_type.name))

        node.static_type = self.bool_type

    @visitor.when(LessEqual)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())
        left_type = node.left.static_type

        self.visit(node.right, scope.create_child())
        right_type = node.right.static_type

        if not left_type.conforms_to(self.int_type) or not right_type.conforms_to(self.int_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Operation is not defined between "%s" and "%s".' % (right_type.name, self.int_type.name))

        node.static_type = self.bool_type

    @visitor.when(Less)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())
        left_type = node.left.static_type

        self.visit(node.right, scope.create_child())
        right_type = node.right.static_type
        
        if not left_type.conforms_to(self.int_type) or not right_type.conforms_to(self.int_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Operation is not defined between "%s" and "%s".' % (right_type.name, self.int_type.name))

        node.static_type = self.bool_type

    @visitor.when(Equal)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())
        left_type = node.left.static_type

        self.visit(node.right, scope.create_child())
        right_type = node.right.static_type

        if isinstance(left_type, AutoType) or isinstance(right_type, AutoType):
            pass 
        elif left_type.conforms_to(self.int_type) ^ right_type.conforms_to(self.int_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Operation is not defined between "%s" and "%s".' % (left_type.name, right_type.name))
        elif left_type.conforms_to(self.string_type) ^ right_type.conforms_to(self.string_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Operation is not defined between "%s" and "%s".' % (left_type.name, right_type.name))
        elif left_type.conforms_to(self.bool_type) ^ right_type.conforms_to(self.bool_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Operation is not defined between "%s" and "%s".' % (left_type.name, right_type.name))

        node.static_type = self.bool_type
    
    @visitor.when(Arithmetic)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())
        left_type = node.left.static_type
        
        self.visit(node.right, scope.create_child())
        right_type = node.right.static_type
        
        if not left_type.conforms_to(self.int_type) or not right_type.conforms_to(self.int_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Operation is not defined between "%s" and "%s".' % (left_type.name, right_type.name))
            
        node.static_type = self.int_type

    @visitor.when(IsVoid)
    def visit(self, node, scope):
        self.visit(node.expression, scope.create_child())

        node.static_type = self.bool_type

    @visitor.when(Complement)
    def visit(self, node, scope):
        expression = node.expression
        self.visit(expression, scope.create_child())

        expr_type = expression.static_type
        if not expr_type.conforms_to(self.int_type):
            self.errors.append('Error on Ln %d, Col %d: ' % (expression.line, expression.column) + 'Cannot convert "%s" into "%s".' % (expr_type.name, self.int_type.name))

        node.static_type = self.int_type

    @visitor.when(FunctionCall)
    def visit(self, node, scope):
        self.visit(node.obj, scope.create_child())
        obj_type = node.obj.static_type
        
        try:
            if node.type:
                try:
                    node_type = self.context.get_type(node.type.lex)
                except SemanticError as ex:
                    self.errors.append('Error on Ln %d, Col %d: ' % (node.type.line, node.type.column) + ex.text)
                    node_type = ErrorType()
                else:
                    if isinstance(node_type, SelfType) or isinstance(node_type, AutoType):
                        self.errors.append('Error on Ln %d, Col %d: ' % (node.type.line, node.type.column) + f'Type "{node_type}" canot be used as type of a dispatch')
                        node_type = ErrorType()

                if not obj_type.conforms_to(node_type):
                    self.errors.append('Error on Ln %d, Col %d: ' % (node.obj.line, node.obj.column) + 'Cannot convert "%s" into "%s".' % (obj_type.name, node_type.name))
                
                obj_type = node_type
            
            obj_method = obj_type.get_method(node.id.lex)
            
            node_type = obj_type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticError as ex:
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + ex.text)
            node_type = ErrorType()
            obj_method = None

        for arg in node.args:
            self.visit(arg, scope.create_child())

        if obj_method and len(node.args) == len(obj_method.param_types):
            for arg, param_type in zip(node.args, obj_method.param_types):
                arg_type = arg.static_type
                    
                if not arg_type.conforms_to(param_type):
                    self.errors.append('Error on Ln %d, Col %d: ' % (arg.line, arg.column) + 'Cannot convert "%s" into "%s".' % (arg_type.name, param_type.name))
        else:
           self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + f'Method "{node.id.lex}" canot be dispatched') 
    
        node.static_type = node_type

    @visitor.when(MemberCall)
    def visit(self, node, scope):
        obj_type = self.current_type
        
        try:
            obj_method = obj_type.get_method(node.id.lex)
                       
            node_type = obj_type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticError as ex:
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + ex.text)
            node_type = ErrorType()
            obj_method = None

        for arg in node.args:
            self.visit(arg, scope.create_child())

        if obj_method and len(node.args) == len(obj_method.param_types):
            for arg, param_type in zip(node.args, obj_method.param_types):
                arg_type = arg.static_type
                    
                if not arg_type.conforms_to(param_type):
                    self.errors.append('Error on Ln %d, Col %d: ' % (arg.line, arg.column) + 'Cannot convert "%s" into "%s".' % (arg_type.name, param_type.name))
        else:
           self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + f'Method "{node.id.lex}" canot be dispatched')
            
        node.static_type = node_type

    @visitor.when(New)
    def visit(self, node, scope):
        try:
            node_type = self.context.get_type(node.type.lex)
        except SemanticError as ex:
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + ex.text)
            node_type = ErrorType()
            
        node.static_type = node_type

    @visitor.when(Integer)
    def visit(self, node, scope):
        node.static_type = self.int_type

    @visitor.when(String)
    def visit(self, node, scope):
        node.static_type = self.string_type

    @visitor.when(Id)
    def visit(self, node, scope):
        if scope.is_defined(node.token.lex):
            var = scope.find_variable(node.token.lex)
            node_type = var.type       
        else:
            self.errors.append('Error on Ln %d, Col %d: ' % (node.line, node.column) + 'Variable "%s" is not defined in "%s".' % (node.token.lex, self.current_method.name))
            node_type = ErrorType()
        
        node.static_type = node_type
    
    @visitor.when(Bool)
    def visit(self, node, scope):
        node.static_type = self.bool_type

#la ultima pasada sobre el ast nos permitira inferir el tipo en los nodos del ast
class TypeInfererVisitor:
    def __init__(self, context, errors=[], infrencias=[]):
        self.context = context
        self.current_type = None
        self.current_method = None
        self.errors = errors
        self.infrencias = infrencias

        # search built-in types
        self.object_type = self.context.get_type('Object')
        self.io_type = self.context.get_type('IO')
        self.int_type = self.context.get_type('Int')
        self.string_type = self.context.get_type('String')
        self.bool_type = self.context.get_type('Bool')
        
    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(Program)
    def visit(self, node, scope):
        self.changed = False

        for declaration, child_scope in zip(node.declarations, scope.children):
            self.visit(declaration, child_scope)

        return self.changed

    @visitor.when(ClassDeclaration)
    def visit(self, node, scope):
        self.current_type = self.context.get_type(node.id.lex)

        for feature, child_scope in zip(node.features, scope.children):
            self.visit(feature, child_scope)

        for attr, var in zip(self.current_type.attributes, scope.locals):
            if var.infer_type():
                self.changed = True
                attr.type = var.type
                self.infrencias.append('On class "%s", attribute "%s": type "%s"' % (self.current_type.name, attr.name, var.type.name))

    @visitor.when(AttrDeclaration)
    def visit(self, node, scope):
        expression = node.expression
        if expression:
            attr = self.current_type.get_attribute(node.id.lex)

            self.visit(expression, scope.children[0], attr.type)
            expr_type = expression.static_type

            var = scope.find_variable(node.id.lex)
            var.set_upper_type(expr_type)
            if var.infer_type():
                self.changed = True
                attr.type = var.type
                self.infrencias.append('On class "%s", attribute "%s": type "%s"' % (self.current_type.name, attr.name, var.type.name))

    @visitor.when(FuncDeclaration)
    def visit(self, node, scope):
        self.current_method = self.current_type.get_method(node.id.lex)
            
        return_type = self.current_method.return_type
        self.visit(node.body, scope.children[0], self.current_type if isinstance(return_type, SelfType) else return_type)

        for i, var in enumerate(scope.locals[1:]):
            if var.infer_type():
                self.changed = True
                self.current_method.param_types[i] = var.type
                self.infrencias.append('On method "%s" of class "%s", param "%s": type "%s"' % (self.current_method.name, self.current_type.name, var.name, var.type.name))
               
        body_type = node.body.static_type
        var = self.current_method.return_info
        var.set_lower_type(body_type)
        if var.infer_type():
            self.changed = True
            self.current_method.return_type = var.type
            self.infrencias.append('Return of method "%s" in class "%s", type "%s"' % (self.current_method.name, self.current_type.name, var.type.name))

    @visitor.when(IfThenElse)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.condition, scope.children[0], self.bool_type)

        self.visit(node.if_body, scope.children[1])
        self.visit(node.else_body, scope.children[2])

        if_type = node.if_body.static_type
        else_type = node.else_body.static_type
        node.static_type = if_type.type_union(else_type)

    @visitor.when(WhileLoop)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.condition, scope.children[0], self.bool_type)

        self.visit(node.body, scope.children[1])

        node.static_type = self.object_type

    @visitor.when(Block)
    def visit(self, node, scope, expected_type=None):
        for expr, child_scope in zip(node.expressions[:-1], scope.children[:-1]):
            self.visit(expr, child_scope)
        # posible inferencia
        self.visit(node.expressions[-1], scope.children[-1], expected_type)

        node.static_type = node.expressions[-1].static_type
            
    @visitor.when(LetIn)
    def visit(self, node, scope, expected_type=None):
        for (idx, typex, expr), child_scope, (i, var) in zip(node.let_body, scope.children[:-1], enumerate(scope.locals)):
            if expr:
                self.visit(expr, child_scope, var.type if var.infered else None)
                expr_type = expr.static_type
                
                var.set_upper_type(expr_type)
                if var.infer_type():
                    self.changed = True
                    typex.name = var.type.name
                    self.infrencias.append('Error on Ln %d, Col %d: ' % (idx.line, idx.column) + 'Varible "%s", type "%s"' % (var.name, var.type.name))

        self.visit(node.in_body, scope.children[-1], expected_type)

        for i, var in enumerate(scope.locals):
            if var.infer_type():
                    self.changed = True
                    idx, typex, _ = node.let_body[i]
                    typex.name = var.type.name
                    self.infrencias.append('Error on Ln %d, Col %d: ' % (idx.line, idx.column) + 'Varible "%s", type "%s"' % (var.name, var.type.name))

        node.static_type = node.in_body.static_type

    @visitor.when(CaseOf)
    def visit(self, node, scope, expected_type=None):
        self.visit(node.expression, scope.children[0])

        node.static_type = None

        for (idx, typex, expr), child_scope in zip(node.branches, scope.children[1:]):
            self.visit(expr, child_scope)
            expr_type = expr.static_type

            node.static_type = node.static_type.type_union(expr_type) if node.static_type else expr_type

    @visitor.when(Assign)
    def visit(self, node, scope, expected_type=None):
        var = scope.find_variable(node.id.lex) if scope.is_defined(node.id.lex) else None

        self.visit(node.expression, scope.children[0], var.type if var and var.infered else expected_type)
        expr_type = node.expression.static_type

        var.set_lower_type(expr_type)
        
        node.static_type = expr_type

    @visitor.when(Not)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.expression, scope.children[0], self.bool_type)

        node.static_type = self.bool_type

    @visitor.when(LessEqual)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.left, scope.children[0], self.int_type)

        # posible inferencia
        self.visit(node.right, scope.children[1], self.int_type)

        node.static_type = self.bool_type

    @visitor.when(Less)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.left, scope.children[0], self.int_type)

        # posible inferencia
        self.visit(node.right, scope.children[1], self.int_type)

        node.static_type = self.bool_type

    @visitor.when(Equal)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.left, scope.children[0], node.right.static_type)

        # posible inferencia
        self.visit(node.right, scope.children[1], node.left.static_type)

        node.static_type = self.bool_type

    @visitor.when(Arithmetic)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.left, scope.children[0], self.int_type)

        # posible inferencia
        self.visit(node.right, scope.children[1], self.int_type)

        node.static_type = self.int_type

    @visitor.when(IsVoid)
    def visit(self, node, scope, expected_type=None):
        self.visit(node.expression, scope.children[0])

        node.static_type = self.bool_type

    @visitor.when(Complement)
    def visit(self, node, scope, expected_type=None):
        # posible inferencia
        self.visit(node.expression, scope.children[0], self.int_type)

        node.static_type = self.int_type

    @visitor.when(FunctionCall)
    def visit(self, node, scope, expected_type=None):
        node_type = None
        if node.type:
                try:
                    node_type = self.context.get_type(node.type.lex)
                except SemanticError:
                    node_type = ErrorType()
                else:
                    if isinstance(node_type, SelfType) or isinstance(node_type, AutoType):
                        node_type = ErrorType()

        self.visit(node.obj, scope.children[0], node_type)
        obj_type = node.obj.static_type
        
        try:
            obj_type = node_type if node_type else obj_type
            
            obj_method = obj_type.get_method(node.id.lex)       
            
            # coloca el expected_type al retorno
            node_type = obj_type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticError:
            node_type = ErrorType()
            obj_method = None
            
        if obj_method and len(node.args) == len(obj_method.param_types):
            for arg, var, child_scope in zip(node.args, obj_method.param_infos, scope.children[1:]):
                self.visit(arg, child_scope, var.type if var.infered else None)
                # inferir var.type por arg_type
        else:
            for arg, child_scope in zip(node.args, scope.children[1:]):
                self.visit(arg, child_scope)
        
        node.static_type = node_type

    @visitor.when(MemberCall)
    def visit(self, node, scope, expected_type=None):
        obj_type = self.current_type
        
        try:
            obj_method = obj_type.get_method(node.id.lex)
            
            # coloca el expected_type al retorno
            node_type = obj_type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticError:
            node_type = ErrorType()
            obj_method = None

        if obj_method and len(node.args) == len(obj_method.param_types):
            for arg, var, child_scope in zip(node.args, obj_method.param_infos, scope.children):
                self.visit(arg, child_scope, var.type if var.infered else None)
                # inferir var.type por arg_type
        else:
            for arg, child_scope in zip(node.args, scope.children):
                self.visit(arg, child_scope)
            
            
        node.static_type = node_type

    @visitor.when(New)
    def visit(self, node, scope, expected_type=None):
        try:
            node_type = self.context.get_type(node.type.lex)
        except SemanticError:
            node_type = ErrorType()
            
        node.static_type = node_type

    @visitor.when(Integer)
    def visit(self, node, scope, expected_type=None):
        node.static_type = self.int_type

    @visitor.when(String)
    def visit(self, node, scope, expected_type=None):
        node.static_type = self.string_type

    @visitor.when(Id)
    def visit(self, node, scope, expected_type=None):
        if scope.is_defined(node.token.lex):
            var = scope.find_variable(node.token.lex)

            if expected_type:
                var.set_upper_type(expected_type)

            node_type = var.type if var.infered else AutoType()   
        else:
            node_type = ErrorType()
        
        node.static_type = node_type
    
    @visitor.when(Bool)
    def visit(self, node, scope, expected_type=None):
        node.static_type = self.bool_type



def ChecksSemantics(node):
    errors = []
    collector = TypeCollectorVisitor(errors)
    collector.visit(node)
    context = collector.context

    builder = TypeBuilderVisitor(context, errors)
    builder.visit(node)

    checker = TypeCheckerVisitor(context, errors)
    scope = checker.visit(node)

    infrencias = []
    inferer = TypeInfererVisitor(context, errors, infrencias)
    while inferer.visit(node, scope): pass

    return context,errors,scope,infrencias


