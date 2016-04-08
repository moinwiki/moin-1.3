"""
    MoinMoin - Widget base class

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: base.py,v 1.1 2002/05/09 18:17:48 jhermann Exp $
"""

class Widget:

    def __init__(self, request, **kw):
        pass

    def render(self):
        pass

