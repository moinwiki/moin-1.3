# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/html" Formatter

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: text_html-old.py,v 1.1 2004/01/30 21:29:56 thomaswaldmann Exp $
"""

# Imports
import sys, time
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

    hardspace = '&nbsp;' # XXX was: '&#160;', but that breaks utf-8

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
            result = ' lang="%s" dir="%s"' % (lang, i18n.getDirection(lang))

        return result

    def lang(self, lang_name, text):
        """ Insert text with specific lang and direction.
        
            Enclose within span tag if lang_name is different from
            the current lang    
        """
        
        if lang_name != self.request.current_lang:
            dir = i18n.getDirection(lang_name)
            text = wikiutil.escape(text)
            return ('<span lang="%(lang_name)s" dir="%(dir)s">'
                    '%(text)s</span>') % locals()
        
        return text            
                
    def sysmsg(self, text, **kw):
        return '<div class="message"><b>%s</b></div>' % wikiutil.escape(text)

    def pagelink(self, pagename, text=None, **kw):
        """ Link to a page.

            See wikiutil.link_tag() for possible keyword parameters.
        """
        apply(FormatterBase.pagelink, (self, pagename, text), kw)
        return Page(pagename).link_to(self.request, text, **kw)

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
            img = wikiutil.make_icon('popup', self.request)           
            str = ('%s<a target="_blank" href="%s">%s</a>') % (str, wikiutil.escape(url, 1), img)

        # create link
        str = str + '<a'
        if css: str = '%s class="%s"' % (str, css)

        title = kw.get('title', None)
        if title: str = '%s title="%s"' % (str, title)
        if target: str = '%s target="%s"' % (str, target)

        str = '%s href="%s">%s</a>' % (str, wikiutil.escape(url, 1), text)

        return str

    def text(self, text):
        if self._in_code:
            return wikiutil.escape(text).replace(' ', self.hardspace)
        return wikiutil.escape(text)

    def rule(self, size=0):
        if size:
            return '<hr size="%d" />\n' % (size,)
        else:
            return '<hr />\n'

    def strong(self, on):
        return ['<b>', '</b>'][not on]

    def emphasis(self, on):
        return ['<em>', '</em>'][not on]

    def highlight(self, on):
        return ['<strong class="highlight">', '</strong>'][not on]

    def number_list(self, on, type=None, start=None):
        if not on: return '</ol>'

        result = '<ol%s' % self._langAttr()
        if type: result = result + ' type="%s"' % (type,)
        if start is not None: result = result + ' start="%d"' % (start,)

        return result + '>'

    def bullet_list(self, on):
        return ['<ul%s>' % self._langAttr(), '</ul>'][not on]

    def listitem(self, on, **kw):
        """ List item inherit its lang from the list."""
        self._in_li = on != 0
        css = ''
        css_class = kw.get('css_class', None)
        if css_class: css += ' class="%s"' % css_class
        return ['<li%s>' % (css,), '</li>'][not on]

    def sup(self, on):
        return ['<sup>', '</sup>'][not on]

    def sub(self, on):
        return ['<sub>', '</sub>'][not on]

    def code(self, on):
        self._in_code = on
        return ['<tt class="wiki">', '</tt>'][not on]

    def preformatted(self, on):
        """ Return pre inside a table
        
        On ideal world should return only <pre>, but this breaks on RTL pages.        
        """
        FormatterBase.preformatted(self, on)
        return ['<table class="code"><tr><td><pre>', '</pre></td></tr></table>'][not on]

    def paragraph(self, on):
        FormatterBase.paragraph(self, on)
        if self._in_li:
            self._in_li = self._in_li + 1
            return ['', '<p%s>' % self._langAttr()][on and self._in_li > 2]
        else:
            return ['<p%s>' % self._langAttr(), ''][not on]

    def linebreak(self, preformatted=1):
        return ['\n', '<br />'][not preformatted]

    def heading(self, depth, title, **kw):
        # remember depth of first heading, and adapt counting depth accordingly
        if not self._base_depth:
            self._base_depth = depth
        count_depth = max(depth - (self._base_depth - 1), 1)

        # check numbering, possibly changing the default
        if self._show_section_numbers is None:
            self._show_section_numbers = config.show_section_numbers
            numbering = self.request.getPragma('section-numbers', '').lower()
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
            return '<table class="wiki"%(lang)s%(tableAttr)s>' % {
                'lang': self._langAttr(),
                'tableAttr': self._checkTableAttr(attrs, 'table')
                }
        return '</table>'

    def table_row(self, on, attrs={}):
        if on:
            on = '<tr class="wiki"%s>' % self._checkTableAttr(attrs, 'row')
        return [on, '</tr>'][not on]

    def table_cell(self, on, attrs={}):
        if on:
            on = '<td class="wiki"%s>' % (self._checkTableAttr(attrs, ''),)
        return [on, '</td>'][not on]

    def anchordef(self, name):
        return '<a name="%s"></a>' % name

    def anchorlink(self, name, text):
        return '<a href="#%s">%s</a>' % (name, wikiutil.escape(text))

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

