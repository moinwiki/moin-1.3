# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Widget base class

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: base.py,v 1.3 2003/11/09 21:01:17 thomaswaldmann Exp $
"""

class Widget:

    def __init__(self, request, **kw):
        self.request = request

    def render(self):
        raise NotImplementedError 

