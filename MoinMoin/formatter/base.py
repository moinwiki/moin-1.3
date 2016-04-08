"""
    MoinMoin - Formatter Base Class

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: base.py,v 1.8 2001/01/03 23:07:51 jhermann Exp $
"""

# Imports


#############################################################################
### Formatter Base
#############################################################################

class FormatterBase:
    """
        Send HTML data.
    """

    def __init__(self):
        pass

    def setPage(self, page):
        self.page = page

    def startDocument(self, pagename):
        return ""

    def endDocument(self):
        return ""

    def pagelink(self, pagename, text=None):
        raise NotImplementedError

    def url(self, url, text=None, css=None, **kw):
        raise NotImplementedError

    def text(self, text):
        raise NotImplementedError

    def rule(self, size=0):
        raise NotImplementedError

    def strong(self, on):
        raise NotImplementedError

    def emphasis(self, on):
        raise NotImplementedError

    def highlight(self, on):
        raise NotImplementedError

    def number_list(self, on, type=None, start=None):
        raise NotImplementedError

    def bullet_list(self, on):
        raise NotImplementedError

    def listitem(self, on):
        raise NotImplementedError

    def code(self, on):
        raise NotImplementedError

    def preformatted(self, on):
        raise NotImplementedError

    def paragraph(self):
        raise NotImplementedError

    def linebreak(self, preformatted=1):
        raise NotImplementedError

    def heading(self, depth, title):
        raise NotImplementedError

    def table(self, on):
        raise NotImplementedError

    def anchordef(self, name):
        return ""

    def anchorlink(self, name, text):
        return text

    def underline(self, on):
        raise NotImplementedError

    def definition_list(self, on):
        raise NotImplementedError

    def definition_term(self, on, compact=0):
        raise NotImplementedError

    def definition_desc(self, on):
        raise NotImplementedError

