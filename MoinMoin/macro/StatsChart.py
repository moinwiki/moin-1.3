# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - StatsChart Macro

    This macro creates charts from the data in "event.log".

    @copyright: 2002-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

Dependencies = ["time24:00"]

def execute(macro, args, **kw):
    _ = macro.request.getText

    if not args:
        return macro.request.formatter.sysmsg(_('You need to provide a chart type!'))

    func = pysupport.importName("MoinMoin.stats." + args, "linkto")
    if not func:
        return macro.request.formatter.sysmsg(_('Bad chart type "%s"!') % args)

    return func(macro.formatter.page.page_name, macro.request)

