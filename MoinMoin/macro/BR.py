"""
    MoinMoin - BR Macro

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This very complicated macro produces a line break.

    $Id: BR.py,v 1.1 2000/12/22 01:12:13 jhermann Exp $
"""

def execute(macro, args):
    return macro.formatter.linebreak(0)
