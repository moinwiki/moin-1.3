"""
    MoinMoin - "text/xml" Formatter

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: text_xml.py,v 1.3 2000/12/01 00:12:30 jhermann Exp $
"""

# Imports
import cgi
from base import FormatterBase
from MoinMoin import wikiutil
from MoinMoin.Page import Page


#############################################################################
### XML Formatter
#############################################################################

class Formatter(FormatterBase):
    """
        Send XML data.
    """

    def __init__(self):
        FormatterBase.__init__(self)

    def startDocument(self, pagename):
        encoding = 'ISO-8859-1'
        return '<?xml version="1.0" encoding="%s"?>\n<s1 title="%s">' % (
            encoding, cgi.escape(pagename, 1))

    def endDocument(self):
        return '</s1>'

    def pagelink(self, pagename):
        return Page(pagename).link_to()

    def url(self, url, text=None, css=None):
        if text is None: text = url

        if wikiutil.isPicture(url):
            return '<img src="%s"/>' % (url,)
        else:
            str = '<a'
            if css: str = '%s class="%s"' % (str, css)
            str = '%s href="%s">%s</a>' % (str, cgi.escape(url, 1), text)
            return str

    def text(self, text):
        return cgi.escape(text)

    def rule(self, size=0):
        if size:
            return '<hr size="%d">\n' % (size,)
        else:
            return '<hr>\n'

    def strong(self, on):
        return ['<strong>', '</strong>'][not on]

    def emphasis(self, on):
        return ['<em>', '</em>'][not on]

    def number_list(self, on, type=None, start=None):
        return ['<ol>', '</ol>'][not on]

    def bullet_list(self, on):
        return ['<ul>', '</ul>'][not on]

    def listitem(self, on):
        return ['<li>', '</li>'][not on]

    def code(self, text):
        return '<code>%s</code>' % (cgi.escape(text),)

    def preformatted(self, on):
        return ['<source>', '</source>'][not on]

    def paragraph(self):
        return '<p>'

    def linebreak(self):
        return '\n'

    def heading(self, depth, title):
        return '<s%d title="%s">\n' % (depth, cgi.escape(title, 1))

    def table(self, on):
        return ['<table>', '</table>'][not on]

