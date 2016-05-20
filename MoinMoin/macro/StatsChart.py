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
    formatter = macro.request.formatter

    if not args:
        return (formatter.sysmsg(1) +
                formatter.text(_('You need to provide a chart type!')) +
                formatter.sysmsg(0))

    func = pysupport.importName("MoinMoin.stats." + args, "linkto")
    if not func:
        return (formatter.sysmsg(1) +
                formatter.text(_('Bad chart type "%s"!') % args) +
                formatter.sysmsg(0))

    return func(macro.formatter.page.page_name, macro.request)

