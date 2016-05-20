# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/xml" Formatter

    @copyright: 2000, 2001, 2002 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from xml.sax import saxutils
from MoinMoin.formatter.base import FormatterBase
from MoinMoin import config
from MoinMoin.Page import Page

class Formatter(FormatterBase):
    """
        Send XML data.
    """

    hardspace = '&nbsp;'

    def __init__(self, request, **kw):
        apply(FormatterBase.__init__, (self, request), kw)
        self._current_depth = 1
        self._base_depth = 0
        self.in_pre = 0

    def _escape(self, text, extra_mapping={"'": "&apos;", '"': "&quot;"}):
        return saxutils.escape(text, extra_mapping)

    def startDocument(self, pagename):
        encoding = config.charset
        return '<?xml version="1.0" encoding="%s"?>\n<s1 title="%s">' % (
            encoding, self._escape(pagename))

    def endDocument(self):
        result = ""
        while self._current_depth > 1:
            result += "</s%d>" % self._current_depth
            self._current_depth = self._current_depth - 1
        return result + '</s1>'

    def lang(self, on, lang_name):
        return ('<div lang="">' % lang_name, '</div>')[not on]

    def sysmsg(self, on, **kw):
        return ('<sysmsg>', '</sysmsg>')[not on]

    def rawHTML(self, markup):
        return '<![CDATA[' + markup.replace(']]>', ']]>]]&gt;<![CDATA[') + ']]>'

    def pagelink(self, on, pagename='', page=None, **kw):
        apply(FormatterBase.pagelink, (self, on, pagename, page), kw)
        if page is None:
            page = Page(self.request, pagename, formatter=self)
        return page.link_to(self.request, on=on, **kw)

    def interwikilink(self, on, interwiki='', pagename='', **kw):
        if on:
            return '<interwiki wiki="%s" pagename="%s">' % (interwiki, pagename)
        else:
            return '</interwiki>'


    def url(self, on, url='', css=None, **kw):
        if css:
            str = ' class="%s"' % css
        else: str = ''
        
        return ('<jump href="%s"%s>' % (self._escape(url), str), '</jump>') [not on]

    def text(self, text):
        if self.in_pre:
            return text.replace(']]>', ']]>]]&gt;<![CDATA[')
        return self._escape(text)

    def rule(self, size=0):
        return "\n<br/>%s<br/>\n" % ("-"*78,) # <hr/> not supported in stylebook
        if size:
            return '<hr size="%d"/>\n' % (size,)
        else:
            return '<hr/>\n'

    def icon(self, type):
        return '<icon type="%s" />' % type            

    def strong(self, on):
        return ['<strong>', '</strong>'][not on]

    def emphasis(self, on):
        return ['<em>', '</em>'][not on]

    def highlight(self, on):
        return ['<strong>', '</strong>'][not on]

    def number_list(self, on, type=None, start=None):
        result = ''
        if self.in_p: result = self.paragraph(0)
        return result + ['<ol>', '</ol>\n'][not on]

    def bullet_list(self, on):
        result = ''
        if self.in_p: result = self.paragraph(0)
        return result + ['<ul>', '</ul>\n'][not on]

    def listitem(self, on, **kw):
        return ['<li>', '</li>\n'][not on]

    def code(self, on):
        return ['<code>', '</code>'][not on]

    def sup(self, on):
        return ['<sup>', '</sup>'][not on]

    def sub(self, on):
        return ['<sub>', '</sub>'][not on]

    def preformatted(self, on):
        FormatterBase.preformatted(self, on)
        result = ''
        if self.in_p: result = self.paragraph(0)
        return result + ['<source><![CDATA[', ']]></source>'][not on]

    def paragraph(self, on):
        FormatterBase.paragraph(self, on)
        return ['<p>', '</p>\n'][not on]

    def linebreak(self, preformatted=1):
        return ['\n', '<br/>\n'][not preformatted]

    def heading(self, on, depth, id = None, **kw):
        if not on:
            return '">\n'
        # remember depth of first heading, and adapt current depth accordingly
        if not self._base_depth:
            self._base_depth = depth
        depth = max(depth + (2 - self._base_depth), 2)

        # close open sections
        result = ""
        while self._current_depth >= depth:
            result = result + "</s%d>\n" % self._current_depth
            self._current_depth = self._current_depth - 1
        self._current_depth = depth

        id_text = ''
        if id:
          id_text = ' id="%s"' % id

        return result + '<s%d%s title="' % (depth, id_text)

    def table(self, on, attrs={}):
        return ['<table>', '</table>'][not on]

    def table_row(self, on, attrs={}):
        return ['<tr>', '</tr>'][not on]

    def table_cell(self, on, attrs={}):
        return ['<td>', '</td>'][not on]

    def anchordef(self, id):
        return '<anchor id="%s"/>' % id

    def anchorlink(self, on, name='', id=None):
        extra = ''
        if id:
            extra = ' id="%s"' % id
        return ('<link anchor="%s"%s>' % (name, extra) ,'</link>') [not on]

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
        valid_attrs = ['src', 'width', 'height', 'alt']
        attrs = {}
        for key, value in kw.items():
            if key in valid_attrs:
                attrs[key] = value
        return apply(FormatterBase.image, (self,), attrs) + '</img>'

    def code_area(self, on, code_id, **kwargs):
        return ('<codearea id="%s">' % code_id, '</codearea')[not on]

    def code_line(self, on):
        return ('<codeline>', '</codeline')[not on]

    def code_token(self, on, tok_type):
        return ('<codetoken type="%s">' % tok_type, '</codetoken')[not on]

    def code_area(self, on, code_id, **kwargs):
        return ('<codearea id="%s">' % code_id, '</codearea')[not on]

    def code_line(self, on):
        return ('<codeline>', '</codeline')[not on]

    def code_token(self, on, tok_type):
        return ('<codetoken type="%s">' % tok_type, '</codetoken')[not on]

