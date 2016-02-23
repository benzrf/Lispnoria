class NoLex(Exception):
    @classmethod
    def create(cls, t):
        msg = "illegal character '{}'".format(t.value[0])
        return cls(msg, t.lexpos)

class NoParse(Exception):
    @classmethod
    def create(cls, t):
        if t:
            if t.type == t.value:
                msg = "unexpected token {!r}".format(t.type)
            else:
                msg = "unexpected token {} ({!r})".format(t.type, t.value)
            return cls(msg, t.lexpos)
        else:
            return cls("could not consume more input", None)

def parse(s, mod):
    return mod.parser.parse(s, lexer=mod.lexer)

