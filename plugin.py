###
# Copyright (c) 2016, benzrf
# All rights reserved.
#
#
###

import supybot.utils as utils
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


class Lispnoria(callbacks.Plugin):
    """Lisp for Limnoria"""
    pass


Class = Lispnoria


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
