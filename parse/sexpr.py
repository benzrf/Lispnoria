from . import NoLex, NoParse

tokens = 'QUOTE QUOTED_SYMBOL BARE_SYMBOL'.split()

literals = r'()'

t_QUOTE = r'\''

def t_QUOTED_SYMBOL(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t
t_BARE_SYMBOL = r'[\w^*/+-\.!?]+'

t_ignore = " \t\n"

def t_error(t):
    raise NoLex.create(t)

import ply.lex as lex
lexer = lex.lex()

from parthial import vals as v

quote = v.LispSymbol('quote')

def p_expr_sym(p):
    """expr : QUOTED_SYMBOL
            | BARE_SYMBOL"""
    p[0] = v.LispSymbol(p[1])

def p_expr_quote(p):
    "expr : QUOTE expr"
    p[0] = v.LispList([quote, p[2]])

def p_expr_list(p):
    "expr : '(' list ')'"
    p[0] = v.LispList(p[2])

def p_list_empty(p):
    "list :"
    p[0] = []

def p_list_cons(p):
    "list : expr list"
    p[0] = [p[1]] + p[2]

def p_error(t):
    raise NoParse.create(t)

import ply.yacc as yacc
parser = yacc.yacc(start='expr', debug=False)

