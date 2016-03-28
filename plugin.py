import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Lispnoria')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

from . import parse
from .parse import botlisp_expr, botlisp_cmds, sexpr
from . import parthial_ext
from parthial import serialize, context, vals, errs
import yaml


class Lispnoria(callbacks.Plugin):
    """Lisp for Limnoria"""

    threaded = True

    def __init__(self, irc, *args, **kwargs):
        super().__init__(irc, *args, **kwargs)
        bot_globals = parthial_ext.bot_globals(irc)
        filename = conf.supybot.directories.data.dirize('lisp_env.yaml')
        try:
            with open(filename, 'r') as f:
                loader = serialize.ParthialLoader(bot_globals, f)
                try:
                    self._lisp_env = loader.get_single_data()
                finally:
                    loader.dispose()
        except FileNotFoundError:
            self._lisp_env = context.Environment(bot_globals)
        world.flushers.append(self._flush)

    def new_env(self, irc):
        env = self._lisp_env.new_child()
        env.globals = parthial_ext.bot_globals(irc)
        return env

    def _flush(self):
        filename = conf.supybot.directories.data.dirize('lisp_env.yaml')
        with open(filename, 'w') as f:
            yaml.dump(self._lisp_env, f, serialize.ParthialDumper)

    def _lispparse(self, irc, code, mod=botlisp_expr):
        try:
            return parse.parse(code, mod)
        except parse.NoLex as e:
            msg, char = e.args
            irc.error("lex error at char {}: {}".format(char, msg), Raise=True)
        except parse.NoParse as e:
            msg, char = e.args
            if char:
                irc.error("parse error at char {}: {}".format(char, msg),
                    Raise=True)
            else:
                irc.error("parse error: {}".format(msg), Raise=True)

    def _lispinterpret(self, irc, msg, expr, respond=False):
        try:
            env = self.new_env(irc)
            env.rec_new(expr)
            p = context.Context(env)
            p.bot_ctx = (self, irc.irc, msg)
            res = p.eval(expr)

            if not respond: return res
            if isinstance(res, vals.LispSymbol):
                res = res.val
            else:
                res = str(res)
            if res:
                irc.reply(res)
        except errs.LimitationError as e:
            irc.error("killed: {}".format(e.message()), Raise=True)
        except errs.LispError as e:
            irc.error(e.message(), Raise=True)


    def lispinterpret(self, irc, msg, args, code):
        """<code>

        Evaluate a botlisp expression."""
        expr = self._lispparse(irc, code)
        self._lispinterpret(irc, msg, expr, respond=True)
    lispinterpret = wrap(lispinterpret, ['text'])

    def lispinterpretcmd(self, irc, msg, args, code):
        """<code>

        Run a botlisp command."""
        expr = self._lispparse(irc, code, mod=botlisp_cmds)
        self._lispinterpret(irc, msg, expr, respond=True)
    lispinterpretcmd = wrap(lispinterpretcmd, ['text'])

    def lispinterpretsexpr(self, irc, msg, args, code):
        """<code>

        Evaluate a sexpr."""
        expr = self._lispparse(irc, code, mod=sexpr)
        self._lispinterpret(irc, msg, expr, respond=True)
    lispinterpretsexpr = wrap(lispinterpretsexpr, ['text'])

    def _lispassign(self, irc, msg, args, k, code, mod=botlisp_expr):
        expr = self._lispparse(irc, code, mod=mod)
        res = self._lispinterpret(irc, msg, expr)
        try:
            if isinstance(res, vals.LispFunc):
                res.name = k
            self._lisp_env.add_rec_new(k, res)
            irc.replySuccess()
        except errs.LimitationError as e:
            irc.error("killed: {}".format(e.message()))

    def lispassign(self, *args):
        """<var> <code>

        Set a variable in the Lisp environment to the result of
        evaluating a botlisp expression."""
        self._lispassign(*args)
    lispassign = wrap(lispassign, ['anything', 'text'])

    def lispassignsexpr(self, *args):
        """<var> <code>

        Set a variable in the Lisp environment to the result of
        evaluating a sexpr."""
        self._lispassign(*args, mod=sexpr)
    lispassignsexpr = wrap(lispassignsexpr, ['anything', 'text'])

    def lispclear(self, irc, msg, args, k):
        """<var>

        Delete a variable from the Lisp environment."""
        if k in self._lisp_env:
            del self._lisp_env[k]
            irc.replySuccess()
        else:
            irc.error("no such definition")
    lispclear = wrap(lispclear, ['anything'])


    def doPrivmsg(self, irc, msg):
        text = msg.args[1]
        _types = [('expr', botlisp_expr),
                  ('command', botlisp_cmds),
                  ('sexpr', sexpr)]
        for var, mod in _types:
            for ep in self.registryValue(var + 'Prefixes'):
                if text.startswith(ep):
                    code = text[len(ep):]
                    try:
                        expr = self._lispparse(irc, code, mod=mod)
                        self._lispinterpret(irc, msg, expr, respond=True)
                    except callbacks.Error as e:
                        irc.error(e.args[0])
                    return

    def invalidCommand(self, irc, msg, tokens):
        cmd = tokens[0]
        env = self.new_env(irc)
        if cmd in env:
            f = env[cmd]
            if callable(f):
                qs = vals.LispSymbol('quote')
                args = [vals.LispList([qs, vals.LispSymbol(t)])
                    for t in tokens[1:]]
                expr = vals.LispList([vals.LispSymbol(cmd)] + args)
                self._lispinterpret(irc, msg, expr, respond=True)


Class = Lispnoria


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

