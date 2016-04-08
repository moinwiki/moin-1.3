"""
    MoinMoin - DataBrowserWidget

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: browser.py,v 1.1 2002/05/09 18:17:48 jhermann Exp $
"""

from MoinMoin.widget import base


class DataBrowserWidget(base.Widget):

    def __init__(self, request, **kw):
        base.Widget.__init__(self, request, **kw)

