import supybot.callbacks as callbacks
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
from parthial.vals import LispSymbol, LispBuiltin
from parthial.errs import LimitationError
from parthial import built_ins
import re
import threading

parseMessage = re.compile('%s: (?P<content>.*)' %
        ircutils.nickRe.pattern.lstrip('^').rstrip('$'))
class FakeIrc:
    def __init__(self, irc):
        self._irc = irc
        self._data = ''
        self._event = threading.Event()

    def _set_data(self, message):
        if isinstance(message, ircmsgs.IrcMsg):
            if message.command in ('PRIVMSG', 'NOTICE'):
                parsed = parseMessage.match(message.args[1])
                if parsed is not None:
                    message = parsed.group('content')
                else:
                    message = message.args[1]
                self._set_data(message)
            else:
                self._irc.queueMsg(message)
                return
        self._data = message
        self._event.set()

    error = _set_data
    reply = _set_data
    queueMsg = _set_data

    def __getattr__(self, name):
        return getattr(self._irc, name)

def lisp_cmd(self, ctx, args):
    for arg, val in enumerate(args):
        built_ins.check_type(self, val, LispSymbol, arg + 1)
    args = [s.val for s in args]

    pl, i, m = ctx.bot_ctx
    fakeIrc = FakeIrc(i)
    pl.Proxy(fakeIrc, m, args, nested=getattr(i, 'nested', 0) + 1)
    fakeIrc._event.wait(10)

    res = fakeIrc._data
    if len(res) > 1024:
        raise LimitationError('symbol result too large')
    return ctx.env.new(LispSymbol(res))

class CommandGlobals:
    def __init__(self, d, irc):
        self.d = d
        self.irc = irc

    def cmd_exists(self, cmd):
        cmd = callbacks.tokenize(cmd)
        cmd = list(map(callbacks.canonicalName, cmd))
        maxL, cbs = self.irc.findCallbacksForArgs(cmd)
        return maxL == cmd and len(cbs) == 1

    def __getitem__(self, k):
        try:
            return self.d[k]
        except KeyError:
            if self.cmd_exists(k):
                cmd = list(map(LispSymbol, callbacks.tokenize(k)))
                def wrapper(self, ctx, args):
                    return lisp_cmd(self, ctx, cmd + args)
                return LispBuiltin(wrapper, k)
            else:
                raise

    def __setitem__(self, *args, **kwargs):
        return self.d.__setitem__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        return self.d.__delitem__(*args, **kwargs)

    def __contains__(self, k):
        d_contains = self.d.__contains__(k)
        if d_contains:
            return d_contains
        else:
            return self.cmd_exists(k)

def bot_globals(irc):
    original = built_ins.default_globals.copy()
    bg = CommandGlobals(original, irc)
    bg['cmd'] = LispBuiltin(lisp_cmd, 'cmd')
    return bg

