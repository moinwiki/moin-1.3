"""
    MoinMoin - Formatter Base Class

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: base.py,v 1.23 2002/05/10 11:39:01 jhermann Exp $
"""

# Imports
import sys, cgi


#############################################################################
### Formatter Base
#############################################################################

class FormatterBase:
    """ This defines the output interface used all over the rest of the code.

        Note that no other means should be used to generate _content_ output,
        while navigational elements (HTML page header/footer) and the like
        can be printed directly without violating output abstraction.
    """

    hardspace = ' '

    def __init__(self, request, **kw):
        self.request = request

        self._store_pagelinks = kw.get('store_pagelinks', 0)
        self.pagelinks = []
        self.in_p = 0
        self.in_pre = 0

    def setPage(self, page):
        self.page = page

    def sysmsg(self, text, **kw):
        """ Emit a system message (embed it into the page).

            Normally used to indicate disabled options, or invalid
            markup.
        """
        return text

    def startDocument(self, pagename):
        return ""

    def endDocument(self):
        return ""

    def rawHTML(self, markup):
        """ This allows emitting pre-formatted HTML markup, and should be
            used wisely (i.e. very seldom).

            Using this event while generating content results in unwanted
            effects, like loss of markup or insertion of CDATA sections
            when output goes to XML formats.
        """
        return markup

    def pagelink(self, pagename, text=None, **kw):
        if kw.get('generated', 0): return
        if self._store_pagelinks and pagename not in self.pagelinks:
            self.pagelinks.append(pagename)

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

    def sup(self, on):
        raise NotImplementedError

    def code(self, on):
        raise NotImplementedError

    def preformatted(self, on):
        self.in_pre = on != 0

    def paragraph(self, on):
        self.in_p = on != 0

    def linebreak(self, preformatted=1):
        raise NotImplementedError

    def heading(self, depth, title, **kw):
        raise NotImplementedError

    def table(self, on, attrs={}):
        raise NotImplementedError

    def table_row(self, on, attrs={}):
        raise NotImplementedError

    def table_cell(self, on, attrs={}):
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

    def image(self, **kw):
        """ Take HTML <IMG> tag attributes in `attr`.

            Attribute names have to be lowercase!
        """
        result = '<img'
        for attr, value in kw.items():
            result = result + ' %s="%s"' % (attr, cgi.escape(str(value)))
        return result + '>'

