from .cmp import Grammar, LR1Parser
from .ast import *

def GetGrammar():
    # grammar
    CoolGrammar = Grammar()

    # non-terminals
    program = CoolGrammar.NonTerminal('<program>', startSymbol=True)
    class_list, def_class = CoolGrammar.NonTerminals('<class-list> <def-class>')
    feature_list, feature = CoolGrammar.NonTerminals('<feature-list> <feature>')
    param_list, param = CoolGrammar.NonTerminals('<param-list> <param>')
    expr, member_call, expr_list, let_list, case_list = CoolGrammar.NonTerminals('<expr> <member-call> <expr-list> <let-list> <case-list>')
    truth_expr, comp_expr = CoolGrammar.NonTerminals('<truth-expr> <comp-expr>')
    arith, term, factor, factor_2 = CoolGrammar.NonTerminals('<arith> <term> <factor> <factor-2>')
    atom, func_call, arg_list = CoolGrammar.NonTerminals('<atom> <func-call> <arg-list>')

    # terminals
    classx, inherits = CoolGrammar.Terminals('class inherits')
    ifx, then, elsex, fi = CoolGrammar.Terminals('if then else fi')
    whilex, loop, pool = CoolGrammar.Terminals('while loop pool')
    let, inx = CoolGrammar.Terminals('let in')
    case, of, esac = CoolGrammar.Terminals('case of esac')
    semi, colon, comma, dot, at, opar, cpar, ocur, ccur, larrow, rarrow = CoolGrammar.Terminals('; : , . @ ( ) { } <- =>')
    plus, minus, star, div, isvoid, compl = CoolGrammar.Terminals('+ - * / isvoid ~')
    notx, less, leq, equal = CoolGrammar.Terminals('not < <= =')
    new, idx, typex, integer, string, boolx = CoolGrammar.Terminals('new id type integer string bool')

    # productions
    program %= class_list, lambda h, s: Program(s[1])

    # <class-list>   ???
    class_list %= def_class + class_list, lambda h, s: [s[1]] + s[2]
    class_list %= def_class, lambda h, s: [s[1]]

    # <def-class>    ???
    def_class %= classx + typex + ocur + feature_list + ccur + semi, lambda h, s: ClassDeclaration(s[2], s[4])
    def_class %= classx + typex + inherits + typex + ocur + feature_list + ccur + semi, lambda h, s: ClassDeclaration(s[2], s[6], s[4])

    # <feature-list> ???
    feature_list %= feature + feature_list, lambda h, s: [s[1]] + s[2]
    feature_list %= CoolGrammar.Epsilon, lambda h, s: []

    # <def-attr>     ???
    feature %= idx + colon + typex + semi, lambda h, s: AttrDeclaration(s[1], s[3])
    feature %= idx + colon + typex + larrow + expr + semi, lambda h, s: AttrDeclaration(s[1], s[3], s[5])

    # <def-func>     ???
    feature %= idx + opar + param_list + cpar + colon + typex + ocur + expr + ccur + semi, lambda h, s: FuncDeclaration(s[1], s[3], s[6], s[8]) 
    feature %= idx + opar + cpar + colon + typex + ocur + expr + ccur + semi, lambda h, s: FuncDeclaration(s[1], [], s[5], s[7]) 

    # <param-list>   ???
    param_list %= param, lambda h, s: [s[1]]
    param_list %= param + comma + param_list, lambda h, s: [s[1]] + s[3]

    # <param>        ???
    param %= idx + colon + typex, lambda h, s: (s[1], s[3])

    # <expr>         ???
    expr %= ifx + expr + then + expr + elsex + expr + fi, lambda h, s: IfThenElse(s[2], s[4], s[6])
    expr %= whilex + expr + loop + expr + pool, lambda h, s: WhileLoop(s[2], s[4])
    expr %= ocur + expr_list + ccur, lambda h, s: Block(s[2])
    expr %= let + let_list + inx + expr, lambda h, s: LetIn(s[2], s[4])
    expr %= case + expr + of + case_list + esac, lambda h, s: CaseOf(s[2], s[4])
    expr %= idx + larrow + expr, lambda h, s: Assign(s[1], s[3])
    expr %= truth_expr, lambda h, s: s[1]

    # <expr-list>    ???
    expr_list %= expr + semi, lambda h, s: [s[1]]
    expr_list %= expr + semi + expr_list, lambda h, s: [s[1]] + s[3]

    # <let-list>     ???
    let_list %= idx + colon + typex, lambda h, s: [(s[1], s[3], None)]
    let_list %= idx + colon + typex + larrow + expr, lambda h, s: [(s[1], s[3], s[5])]
    let_list %= idx + colon + typex + comma + let_list, lambda h, s: [(s[1], s[3], None)] + s[5]
    let_list %= idx + colon + typex + larrow + expr + comma + let_list, lambda h, s: [(s[1], s[3], s[5])] + s[7]

    # <case-list>    ???
    case_list %= idx + colon + typex + rarrow + expr + semi, lambda h, s: [(s[1], s[3], s[5])]
    case_list %= idx + colon + typex + rarrow + expr + semi + case_list, lambda h, s: [(s[1], s[3], s[5])] + s[7]

    # <truth-expr>   ???
    truth_expr %= notx + truth_expr, lambda h, s: Not(s[2])
    truth_expr %= comp_expr, lambda h, s: s[1]

    # <comp-expr>    ???
    comp_expr %= comp_expr + leq + arith, lambda h, s: LessEqual(s[1], s[3])
    comp_expr %= comp_expr + less + arith, lambda h, s: Less(s[1], s[3])
    comp_expr %= comp_expr + equal + arith, lambda h, s: Equal(s[1], s[3])
    comp_expr %= arith, lambda h, s: s[1]

    # <arith>       ???
    arith %= arith + plus + term, lambda h, s: Plus(s[1], s[3])
    arith %= arith + minus + term, lambda h, s: Minus(s[1], s[3])
    arith %= term, lambda h, s: s[1]

    # <term>        ???
    term %= term + star + factor, lambda h, s: Star(s[1], s[3])
    term %= term + div + factor, lambda h, s: Div(s[1], s[3])
    term %= factor, lambda h, s: s[1]

    # <factor>      ???
    factor %= isvoid + factor_2, lambda h, s: IsVoid(s[2])
    factor %= factor_2, lambda h, s: s[1]

    # <factor-2>    ???
    factor_2 %= compl + atom, lambda h, s: Complement(s[2])
    factor_2 %= atom, lambda h, s: s[1]

    # <atom>        ???
    atom %= atom + func_call, lambda h, s: FunctionCall(s[1], *s[2])
    atom %= member_call, lambda h, s: s[1]
    atom %= new + typex, lambda h, s: New(s[2])
    atom %= opar + expr + cpar, lambda h, s: s[2]
    atom %= idx, lambda h, s: Id(s[1])
    atom %= integer, lambda h, s: Integer(s[1])
    atom %= string, lambda h, s: String(s[1])
    atom %= boolx, lambda h, s: Bool(s[1])

    # <func-call>   ???
    func_call %= dot + idx + opar + arg_list + cpar, lambda h, s: (s[2], s[4])
    func_call %= dot + idx + opar + cpar, lambda h, s: (s[2], [])
    func_call %= at + typex + dot + idx + opar + arg_list + cpar, lambda h, s: (s[4], s[6], s[2])
    func_call %= at + typex + dot + idx + opar + cpar, lambda h, s: (s[4], [], s[2])

    # <arg-list>    ???
    arg_list %= expr, lambda h, s: [s[1]]
    arg_list %= expr + comma + arg_list, lambda h, s: [s[1]] + s[3]

    # <member-call> ???
    member_call %= idx + opar + arg_list + cpar, lambda h, s: MemberCall(s[1], s[3])
    member_call %= idx + opar + cpar, lambda h, s: MemberCall(s[1], [])

    return CoolGrammar

CoolGrammar = GetGrammar()
# parser
CoolParser = LR1Parser(CoolGrammar)