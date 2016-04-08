"""
    MoinMoin - "text/html" Formatter

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: text_html.py,v 1.37 2002/03/11 21:18:56 jhermann Exp $
"""

# Imports
import cgi, string, sys, time
from base import FormatterBase
from MoinMoin import wikiutil, config, user
from MoinMoin.Page import Page
from MoinMoin.cgimain import request
from MoinMoin.i18n import _


#############################################################################
### HTML Formatter
#############################################################################

class Formatter(FormatterBase):
    """
        Send HTML data.
    """

    hardspace = '&#160;'

    _allowed_table_attrs = {
        'table': ['border', 'cellspacing', 'cellpadding', 'width', 'bgcolor', ],
        'row': ['width', 'align', 'valign', 'bgcolor', ],
        '': ['width', 'align', 'valign', 'colspan', 'rowspan', 'bgcolor', ],
    }
    _table_defaults = [
        ('tableborder', '"1"'),
        ('tablecellspacing', '"0"'),
        ('tablecellpadding', '"3"'),
    ]


    def __init__(self, **kw):
        apply(FormatterBase.__init__, (self,), kw)
        self._in_li = 0
        self._in_code = 0
        self._base_depth = 0
        self._show_section_numbers = None

        if not hasattr(request, '_fmt_hd_counters'):
            request._fmt_hd_counters = []


    def pagelink(self, pagename, text=None):
        FormatterBase.pagelink(self, pagename, text)
        return Page(pagename).link_to(text)

    def url(self, url, text=None, css=None, **kw):
        url = wikiutil.mapURL(url)
        pretty = kw.get('pretty_url', 0)

        if not pretty and wikiutil.isPicture(url):
            return '<img src="%s" border="0">' % (url,)

        if text is None: text = url
        str = ''

        # add popup icon if user asked for it
        if pretty and user.current.external_target:
            str = ('%s<a target="_blank" href="%s"><img src="%s/img/moin-popup.gif"'
                ' border="0" width="15" height="9" alt="%s"></a>') % (
                str, cgi.escape(url, 1), config.url_prefix, _('[New window]'))

        # create link
        str = str + '<a'
        if css: str = '%s class="%s"' % (str, css)
        title = kw.get('title', None)
        if title: str = '%s title="%s"' % (str, title)
        str = '%s href="%s">%s</a>' % (str, cgi.escape(url, 1), text)

        return str

    def text(self, text):
        if self._in_code:
            return string.replace(cgi.escape(text), ' ', self.hardspace)
        return cgi.escape(text)

    def rule(self, size=0):
        if size:
            return '<hr size="%d">\n' % (size,)
        else:
            return '<hr>\n'

    def strong(self, on):
        return ['<b>', '</b>'][not on]

    def emphasis(self, on):
        return ['<em>', '</em>'][not on]

    def highlight(self, on):
        return ['<strong class="highlight">', '</strong>'][not on]

    def number_list(self, on, type=None, start=None):
        if not on: return '</ol>'

        result = '<ol'
        if type: result = result + ' type="%s"' % (type,)
        if start: result = result + ' start="%d"' % (start,)

        return result + '>'

    def bullet_list(self, on):
        return ['<ul>', '</ul>'][not on]

    def listitem(self, on):
        self._in_li = on != 0
        return ['<li>', '</li>'][not on]

    def sup(self, on):
        return ['<sup>', '</sup>'][not on]

    def code(self, on):
        self._in_code = on
        return ['<tt class="wiki">', '</tt>'][not on]

    def preformatted(self, on):
        return ['<pre class="code">', '</pre>'][not on]

    def paragraph(self, on):
        FormatterBase.paragraph(self, on)
        if self._in_li:
            self._in_li = self._in_li + 1
            return ['', '<p>'][on and self._in_li > 2]
        else:
            return ['<p>', ''][not on]

    def linebreak(self, preformatted=1):
        return ['\n', '<br>'][not preformatted]

    def heading(self, depth, title, **kw):
        # remember depth of first heading, and adapt current depth accordingly
        if not self._base_depth:
            self._base_depth = depth
        depth = max(depth - (self._base_depth - 1), 1)

        # check numbering, possibly changing the default
        if self._show_section_numbers is None:
            self._show_section_numbers = config.show_section_numbers
            numbering = string.lower(request.getPragma('section-numbers', ''))
            if numbering in ['0', 'off']:
                self._show_section_numbers = 0
            elif numbering in ['1', 'on']:
                self._show_section_numbers = 1

        # create section number
        number = ''
        if self._show_section_numbers:
            # count headings on all levels
            request._fmt_hd_counters = request._fmt_hd_counters[:depth]
            while len(request._fmt_hd_counters) < depth:
                request._fmt_hd_counters.append(0)
            request._fmt_hd_counters[-1] = request._fmt_hd_counters[-1] + 1
            number = string.join(map(str, request._fmt_hd_counters), ".") + " "

        return '<H%d>%s%s%s</H%d>\n' % (
            depth, kw.get('icons', ''), number, title, depth)

    def _checkTableAttr(self, attrs, prefix):
        if not attrs: return ''

        result = ''
        for key, val in attrs.items():
            if prefix and key[:len(prefix)] != prefix: continue
            key = key[len(prefix):]
            if key not in self._allowed_table_attrs[prefix]: continue
            result = '%s %s=%s' % (result, key, val)

        return result

    def table(self, on, attrs={}):
        if on:
            attrs = attrs and attrs.copy() or {}
            for key, val in self._table_defaults:
                if not attrs.has_key(key): attrs[key] = val
            on = '<table class="wiki"%s>' % self._checkTableAttr(attrs, 'table')
        return [on, '</table>'][not on]

    def table_row(self, on, attrs={}):
        if on:
            on = '<tr class="wiki"%s>' % self._checkTableAttr(attrs, 'row')
        return [on, '</tr>'][not on]

    def table_cell(self, on, attrs={}):
        if on:
            on = '<td class="wiki"%s>' % self._checkTableAttr(attrs, '')
        return [on, '</td>'][not on]

    def anchordef(self, name):
        return '<a name="%s"></a>' % name

    def anchorlink(self, name, text):
        return '<a href="#%s">%s</a>' % (name, cgi.escape(text))

    def underline(self, on):
        return ['<u>', '</u>'][not on]

    def definition_list(self, on):
        return ['<dl>', '</dl>'][not on]

    def definition_term(self, on, compact=0):
        extra = ''
        if compact:
            extra = ' compact'
        return ['<dt%s><b>' % (extra,), '</b></dt>'][not on]

    def definition_desc(self, on):
        return ['<dd>', '</dd>'][not on]

