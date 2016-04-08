"""
    MoinMoin - "text/xml" Formatter

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Note that this formatter needs either PyXML installed for
    Python 1.5.2, or Python 2.0 or higher.

    $Id: text_xml.py,v 1.28 2002/05/10 11:39:01 jhermann Exp $
"""

# Imports
import string
from xml.sax import saxutils

from MoinMoin.formatter.base import FormatterBase
from MoinMoin import wikiutil
from MoinMoin.Page import Page


#############################################################################
### XML Formatter
#############################################################################

class Formatter(FormatterBase):
    """
        Send XML data.
    """

    hardspace = '&#160;'

    def __init__(self, request, **kw):
        apply(FormatterBase.__init__, (self, request), kw)
        self._current_depth = 1
        self._base_depth = 0
        self.in_pre = 0

    def _escape(self, text, extra_mapping={"'": "&apos;", '"': "&quot;"}):
        return saxutils.escape(text, extra_mapping)

    def startDocument(self, pagename):
        encoding = 'ISO-8859-1'
        return '<?xml version="1.0" encoding="%s"?>\n<s1 title="%s">' % (
            encoding, self._escape(pagename))

    def endDocument(self):
        result = ""
        while self._current_depth > 1:
            result = result + "</s%d>" % self._current_depth
            self._current_depth = self._current_depth - 1
        return result + '</s1>'

    def sysmsg(self, text, **kw):
        return '<!-- %s -->' % self._escape(text).replace('--', '==')

    def rawHTML(self, markup):
        return '<![CDATA[' + string.replace(markup, ']]>', ']]>]]&gt;<![CDATA[') + ']]>'

    def pagelink(self, pagename, text=None, **kw):
        apply(FormatterBase.pagelink, (self, pagename, text), kw)
        return Page(pagename, formatter=self).link_to(text)

    def url(self, url, text=None, css=None, **kw):
        if text is None: text = url

        if wikiutil.isPicture(url):
            return '<img src="%s"/>' % (url,)
        else:
            unescaped = kw.get('unescaped', 0)
            str = '<jump'
            ##if css: str = '%s class="%s"' % (str, css)
            if not unescaped: text = self._escape(text)
            str = '%s href="%s">%s</jump>' % (str, self._escape(url), text)
            return str

    def text(self, text):
        if self.in_pre:
            return string.replace(text, ']]>', ']]>]]&gt;<![CDATA[')
        return self._escape(text)

    def rule(self, size=0):
        return "\n<br/>%s<br/>\n" % ("-"*78,) # <hr/> not supported in stylebook
        if size:
            return '<hr size="%d"/>\n' % (size,)
        else:
            return '<hr/>\n'

    def strong(self, on):
        return ['<strong>', '</strong>'][not on]

    def emphasis(self, on):
        return ['<em>', '</em>'][not on]

    def highlight(self, on):
        return ['<strong>', '</strong>'][not on]

    def number_list(self, on, type=None, start=None):
        result = ''
        if self.in_p: result = self.paragraph(0)
        return result + ['<ol>', '</ol>'][not on]

    def bullet_list(self, on):
        result = ''
        if self.in_p: result = self.paragraph(0)
        return result + ['<ul>', '</ul>'][not on]

    def listitem(self, on):
        return ['<li>', '</li>'][not on]

    def code(self, on):
        return ['<code>', '</code>'][not on]

    def sup(self, on):
        return ['<sup>', '</sup>'][not on]

    def preformatted(self, on):
        FormatterBase.preformatted(self, on)
        result = ''
        if self.in_p: result = self.paragraph(0)
        return result + ['<source><![CDATA[', ']]></source>'][not on]

    def paragraph(self, on):
        FormatterBase.paragraph(self, on)
        return ['<p>', '</p>'][not on]

    def linebreak(self, preformatted=1):
        return ['\n', '<br/>'][not preformatted]

    def heading(self, depth, title, **kw):
        # remember depth of first heading, and adapt current depth accordingly
        if not self._base_depth:
            self._base_depth = depth
        depth = max(depth + (2 - self._base_depth), 2)

        # close open sections
        result = ""
        while self._current_depth >= depth:
            result = result + "</s%d>" % self._current_depth
            self._current_depth = self._current_depth - 1
        self._current_depth = depth

        return result + '<s%d title="%s">\n' % (depth, self._escape(title))

    def table(self, on, attrs={}):
        return ['<table>', '</table>'][not on]

    def table_row(self, on, attrs={}):
        return ['<tr>', '</tr>'][not on]

    def table_cell(self, on, attrs={}):
        return ['<td>', '</td>'][not on]

    def anchordef(self, name):
        return '<anchor name="%s"/>' % name

    def anchorlink(self, name, text):
        return '<link anchor="%s">%s</link>' % (name, self._escape(text, {}))

    def underline(self, on):
        return self.strong(on) # no underline in StyleBook

    def definition_list(self, on):
        result = ''
        if self.in_p: result = self.paragraph(0)
        return result + ['<gloss>', '</gloss>'][not on]

    def definition_term(self, on, compact=0):
        return ['<label>', '</label>'][not on]

    def definition_desc(self, on):
        return ['<item>', '</item>'][not on]

    def image(self, **kw):
        valid_attrs = ['src', 'width', 'height', 'alt', 'vspace', 'hspace', 'align']
        attrs = {}
        for key, value in kw.items():
            if key in valid_attrs:
                attrs[key] = value
        return apply(FormatterBase.image, (self,), attrs) + '</img>'

