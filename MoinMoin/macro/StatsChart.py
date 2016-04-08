# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - StatsChart Macro

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro creates charts from the data in "event.log".

    $Id: StatsChart.py,v 1.4 2003/11/09 21:01:04 thomaswaldmann Exp $
"""

from MoinMoin.util import pysupport


def execute(macro, args, **kw):
    _ = macro.request.getText

    if not args:
        return _('<div class="message"><b>You need to provide a chart type!</b></div>')

    func = pysupport.importName("MoinMoin.stats." + args, "linkto")
    if not func:
        return _('<div class="message"><b>Bad chart type "%s"!</b></div>') % args

    return func(macro.formatter.page.page_name, macro.request)

