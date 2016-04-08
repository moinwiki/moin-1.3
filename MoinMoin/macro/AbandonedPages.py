# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - AbandonedPages Macro

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This is a list of pages that were not edited for a long time
    according to the edit log; if you shortened the log, the displayed
    information may not be what you expect.

    $Id: AbandonedPages.py,v 1.2 2003/11/09 21:01:01 thomaswaldmann Exp $
"""

from MoinMoin.macro import RecentChanges

def execute(macro, args):
    return RecentChanges.execute(macro, args, abandoned=1)

