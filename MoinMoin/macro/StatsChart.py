"""
    MoinMoin - StatsChart Macro

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro creates charts from the data in "event.log".

    $Id: StatsChart.py,v 1.1 2002/02/02 03:14:26 jhermann Exp $
"""

# Imports
from MoinMoin import util
from MoinMoin.i18n import _


def execute(macro, args, **kw):
    if not args:
        return _('<div class="message"><b>You need to provide a chart type!</b></div>')

    func = util.importName("MoinMoin.stats." + args, "linkto")
    if not func:
        return _('<div class="message"><b>Bad chart type "%s"!</b></div>') % args

    return apply(func, (macro.formatter.page.page_name,))

