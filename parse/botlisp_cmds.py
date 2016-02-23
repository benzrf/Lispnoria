from .botlisp_shared import *

tokens += 'DOUBLE_SEMICOLON',

# this doesn't need to be a function, but functions take priority over
# non-function tokens in ply, and ";;" should not be lexed as a symbol
def t_DOUBLE_SEMICOLON(t):
    r';;'
    return t

def p_cmdlist_one(p):
    "cmdlist : sqlist"
    p[0] = [v.LispList(p[1])]

def p_cmdlist_cons(p):
    "cmdlist : sqlist DOUBLE_SEMICOLON cmdlist"
    p[0] = [v.LispList(p[1])] + p[3]

def p_cmds(p):
    "cmds : cmdlist"
    p[0] = v.LispList([progn] + p[1])

lexer = lex.lex()
parser = yacc.yacc(start='cmds', debug=False)

