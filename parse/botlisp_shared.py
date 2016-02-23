from . import NoLex, NoParse
from ply.lex import TOKEN

tokens =\
    'QUOTED_SYMBOL BARE_SYMBOL '\
    'QUOTED_VARIABLE BARE_VARIABLE'.split()

literals = r'`[]{}'

def t_QUOTED_SYMBOL(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t
t_BARE_SYMBOL = r'[^ \[\]\{\}`$"]' r'.*?(?=[ \[\]\{\}]|;;|$)'

def t_QUOTED_VARIABLE(t):
    r'\$"[^"]*"'
    t.value = t.value[2:-1]
    return t
@TOKEN(r'\$' + t_BARE_SYMBOL)
def t_BARE_VARIABLE(t):
    t.value = t.value[1:]
    return t

t_ignore = " \t\n"

def t_error(t):
    raise NoLex.create(t)

from parthial import vals as v

quote = v.LispSymbol('quote')
progn = v.LispSymbol('progn')

def p_expr(p):
    """expr : nonsymexpr
            | nsym"""
    p[0] = p[1]

def p_sqleadexpr(p):
    """sqleadexpr : nonsymexpr
                  | sqleadsym"""
    p[0] = p[1]

def p_nonsymexpr_quote(p):
    "nonsymexpr : '`' expr"
    p[0] = v.LispList([quote, p[2]])

def p_nsym(p):
    """nsym : BARE_SYMBOL
            | QUOTED_SYMBOL"""
    p[0] = v.LispList([quote, v.LispSymbol(p[1])])

def p_sqleadsym(p):
    """sqleadsym : BARE_SYMBOL
                 | QUOTED_SYMBOL"""
    p[0] = v.LispSymbol(p[1])

def p_nonsymexpr_var(p):
    """nonsymexpr : BARE_VARIABLE
                  | QUOTED_VARIABLE"""
    p[0] = v.LispSymbol(p[1])

def p_nonsymexpr_list(p):
    """nonsymexpr : '[' sqlist ']'
               | '{' curlylist '}'"""
    p[0] = v.LispList(p[2])

def p_sqlist_empty(p):
    "sqlist :"
    p[0] = []

def p_sqlist_cons(p):
    "sqlist : sqleadexpr curlylist"
    p[0] = [p[1]] + p[2]

def p_curlylist_empty(p):
    "curlylist :"
    p[0] = []

def p_curlylist_cons(p):
    "curlylist : expr curlylist"
    p[0] = [p[1]] + p[2]

def p_error(t):
    raise NoParse.create(t)

import ply.lex as lex
import ply.yacc as yacc

