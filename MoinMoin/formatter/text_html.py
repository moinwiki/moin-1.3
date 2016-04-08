# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/html" Formatter

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: text_html.py,v 1.57 2003/11/09 21:00:56 thomaswaldmann Exp $
"""

# Imports
import cgi, string, sys, time
from MoinMoin.formatter.base import FormatterBase
from MoinMoin import wikiutil, config, user, i18n
from MoinMoin.Page import Page


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


    def __init__(self, request, **kw):
        apply(FormatterBase.__init__, (self, request), kw)
        self._in_li = 0
        self._in_code = 0
        self._base_depth = 0
        self._show_section_numbers = None

        if not hasattr(request, '_fmt_hd_counters'):
            request._fmt_hd_counters = []

    def _langAttr(self):
        result = ''
        lang = self.request.current_lang
        if lang != config.default_lang:
            result += ' lang="%s" dir="%s"' % (
                lang, i18n.getDirection(self.request, lang))

        return result

    def sysmsg(self, text, **kw):
        return '<div class="message"><b>%s</b></div>' % cgi.escape(text)

    def pagelink(self, pagename, text=None, **kw):
        """ Link to a page.

            See wikiutil.link_tag() for possible keyword parameters.
        """
        apply(FormatterBase.pagelink, (self, pagename, text), kw)
        return Page(pagename).link_to(text, **kw)

    def url(self, url, text=None, css=None, **kw):
        """
            Keyword params:
                title - title attribute
                target - target attribute
                ... some more (!!! TODO) 
        """
        url = wikiutil.mapURL(url)
        pretty = kw.get('pretty_url', 0)
        target = kw.get('target', None)

        if not pretty and wikiutil.isPicture(url):
            return '<img src="%s" border="0">' % (url,)

        if text is None: text = url
        str = ''

        # add popup icon if user asked for it or a target is set
        if pretty and (self.request.user.external_target or target is not None):
            str = ('%s<a target="_blank" href="%s"><img src="%s/img/moin-popup.gif"'
                ' border="0" width="15" height="9" alt="%s" title="%s"></a>') % (
                str, cgi.escape(url, 1), config.url_prefix, self._('[New window]'), self._('[New window]'))

        # create link
        str = str + '<a'
        if css: str = '%s class="%s"' % (str, css)

        title = kw.get('title', None)
        if title: str = '%s title="%s"' % (str, title)
        if target: str = '%s target="%s"' % (str, target)

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
        if start is not None: result = result + ' start="%d"' % (start,)

        return result + '>'

    def bullet_list(self, on):
        return ['<ul>', '</ul>'][not on]

    def listitem(self, on, **kw):
        self._in_li = on != 0
        css = ''
        css_class = kw.get('css_class', None)
        if css_class: css += ' class="%s"' % css_class
        return ['<li%s%s>' % (css, self._langAttr()), '</li>'][not on]

    def sup(self, on):
        return ['<sup>', '</sup>'][not on]

    def sub(self, on):
        return ['<sub>', '</sub>'][not on]

    def code(self, on):
        self._in_code = on
        return ['<tt class="wiki">', '</tt>'][not on]

    def preformatted(self, on):
        FormatterBase.preformatted(self, on)
        return ['<pre class="code">', '</pre>'][not on]

    def paragraph(self, on):
        FormatterBase.paragraph(self, on)
        if self._in_li:
            self._in_li = self._in_li + 1
            return ['', '<p%s>' % self._langAttr()][on and self._in_li > 2]
        else:
            return ['<p%s>' % self._langAttr(), ''][not on]

    def linebreak(self, preformatted=1):
        return ['\n', '<br>'][not preformatted]

    def heading(self, depth, title, **kw):
        # remember depth of first heading, and adapt counting depth accordingly
        if not self._base_depth:
            self._base_depth = depth
        count_depth = max(depth - (self._base_depth - 1), 1)

        # check numbering, possibly changing the default
        if self._show_section_numbers is None:
            self._show_section_numbers = config.show_section_numbers
            numbering = string.lower(self.request.getPragma('section-numbers', ''))
            if numbering in ['0', 'off']:
                self._show_section_numbers = 0
            elif numbering in ['1', 'on']:
                self._show_section_numbers = 1
            elif numbering in ['2', '3', '4', '5', '6']:
                # explicit base level for section number display
                self._show_section_numbers = int(numbering)

        # create section number
        number = ''
        if self._show_section_numbers:
            # count headings on all levels
            self.request._fmt_hd_counters = self.request._fmt_hd_counters[:count_depth]
            while len(self.request._fmt_hd_counters) < count_depth:
                self.request._fmt_hd_counters.append(0)
            self.request._fmt_hd_counters[-1] = self.request._fmt_hd_counters[-1] + 1
            number = '.'.join(map(str, self.request._fmt_hd_counters[self._show_section_numbers-1:]))
            # CNC:2003-05-30
            if number: number += ". "

        if kw.has_key('on'):
            if kw['on']:
                return '<H%d>' % depth
            else:
                return '</H%d>' % depth
        else:
            return '<H%d%s>%s%s%s</H%d>\n' % (
                depth, self._langAttr(), kw.get('icons', ''), number, title, depth)

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
            on = '<td class="wiki"%s%s>' % (
                self._langAttr(),
                self._checkTableAttr(attrs, ''))
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
        return ['<dt%s%s><b>' % (extra, self._langAttr()), '</b></dt>'][not on]

    def definition_desc(self, on):
        return ['<dd%s>' % self._langAttr(), '</dd>'][not on]

