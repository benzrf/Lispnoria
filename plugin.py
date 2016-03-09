###
# Copyright (c) 2016, benzrf
# All rights reserved.
#
#
###

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
from . import parthial_ext
import parthial
import yaml


class Lispnoria(callbacks.Plugin):
    """Lisp for Limnoria"""

    def __init__(self, irc, *args, **kwargs):
        super().__init__(irc, *args, **kwargs)
        bot_globals = parthial_ext.bot_globals(irc)
        filename = conf.supybot.directories.data.dirize('lisp_env.yaml')
        try:
            with open(filename, 'r') as f:
                loader = parthial.serialize.ParthialLoader(bot_globals, f)
                try:
                    self.lisp_env = loader.get_single_data()
                finally:
                    loader.dispose()
        except FileNotFoundError:
            self.lisp_env = parthial.context.Environment(bot_globals)
        world.flushers.append(self._flush)

    def _flush(self):
        filename = conf.supybot.directories.data.dirize('lisp_env.yaml')
        with open(filename, 'w') as f:
            yaml.dump(self.lisp_env, f, parthial.serialize.ParthialDumper)

    def _lispparse(self, irc, code, mod=parse.botlisp_expr):
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
            env = self.lisp_env.new_child()
            p = parthial.context.Context(env)
            p.bot_ctx = (self, irc.irc, msg)
            res = p.eval(expr)

            if not respond: return res
            if isinstance(res, parthial.vals.LispSymbol):
                res = res.val
            else:
                res = str(res)
            if res:
                irc.reply(res)
        except parthial.errs.LimitationError as e:
            irc.error("killed: {}".format(e.message()), Raise=True)
        except parthial.errs.LispError as e:
            irc.error(e.message(), Raise=True)


Class = Lispnoria


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

