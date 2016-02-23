from .botlisp_shared import *

lexer = lex.lex()
parser = yacc.yacc(start='expr', debug=False)

