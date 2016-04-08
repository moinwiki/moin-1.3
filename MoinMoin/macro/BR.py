# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - BR Macro

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This very complicated macro produces a line break.

    $Id: BR.py,v 1.2 2003/11/09 21:01:02 thomaswaldmann Exp $
"""

def execute(macro, args):
    return macro.formatter.linebreak(0)
