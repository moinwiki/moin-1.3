"""
    MoinMoin - MoinMoin Wiki Markup Parser

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wiki.py,v 1.88 2002/05/09 21:09:37 jhermann Exp $
"""

# Imports
import cgi, os, re, string, sys
from MoinMoin import config, user, wikimacro, wikiutil, util
from MoinMoin.Page import Page
from MoinMoin.i18n import _


#############################################################################
### MoinMoin Wiki Markup Parser
#############################################################################

class Parser:
    """
        Object that turns Wiki markup into HTML.

        All formatting commands can be parsed one line at a time, though
        some state is carried over between lines.

        Methods named like _*_repl() are responsible to handle the named regex
        patterns defined in print_html().
    """

    # some common strings
    attachment_schemas = ["attachment", "inline", "drawing"]
    punct_pattern = re.escape('''"'}]|:,.)?!''')
    url_pattern = ('http|https|ftp|nntp|news|mailto|telnet|wiki|file|' +
            string.join(attachment_schemas, '|') + 
            (config.url_schemas and '|' + string.join(config.url_schemas, '|') or ''))

    # some common rules
    word_rule = r'(?:%(subpages)s(?:[%(u)s][%(l)s]+){2,})+' % {
        'u': config.upperletters,
        'l': config.lowerletters,
        'subpages': config.allow_subpages and '/?' or '',
    }
    url_rule = r'%(url_guard)s(%(url)s)\:([^\s\<%(punct)s]|([%(punct)s][^\s\<%(punct)s]))+' % {
        'url_guard': ('(^|(?<!\w))', '')[sys.version < "2"],
        'url': url_pattern,
        'punct': punct_pattern,
    }

    ol_rule = r"^\s+(?:[0-9]+|[aAiI])\.(?:#\d+)?\s"
    dl_rule = r"^\s+.*?::\s"

    # the big, fat, ugly one ;)
    formatting_rules = r"""(?:(?P<emph_ibb>'''''(?=[^']+'''))
(?P<emph_ibi>'''''(?=[^']+''))
(?P<emph_ib_or_bi>'{5}(?=[^']))
(?P<emph>'{2,3})
(?P<sup>\^.*?\^)
(?P<tt>\{\{\{.*?\}\}\})
(?P<processor>(\{\{\{#!.*))
(?P<pre>(\{\{\{ ?|\}\}\}))
(?P<rule>-{4,})
(?P<comment>^\#\#.*$)
(?P<macro>\[\[(%(macronames)s)(?:\(.*?\))?\]\]))
(?P<li>^\s+\*)
(?P<ol>%(ol_rule)s)
(?P<dl>%(dl_rule)s)
(?P<tableZ>\|\| $)
(?P<table>(?:\|\|)+(?:<[^>]*?>)?(?=.))
(?P<heading>^\s*(?P<hmarker>=+)\s.*\s(?P=hmarker) $)
(?P<interwiki>[A-Z][a-zA-Z]+\:[^\s'\"\:\<]([^\s%(punct)s]|([%(punct)s][^\s%(punct)s]))+)
(?P<word>%(word_rule)s)
(?P<url_bracket>\[((%(url)s)\:|#)[^\s\]]+(\s[^\]]+)?\])
(?P<url>%(url_rule)s)
(?P<email>[-\w._+]+\@[\w-]+\.[\w.-]+)
(?P<smiley>\s(%(smiley)s)\s)
(?P<smileyA>^(%(smiley)s)\s)
(?P<ent>[<>&])"""  % {
        'url': url_pattern,
        'punct': punct_pattern,
        'macronames': string.join(wikimacro.names, '|'),
        'ol_rule': ol_rule,
        'dl_rule': dl_rule,
        'url_rule': url_rule,
        'word_rule': word_rule,
        'smiley': string.join(map(re.escape, wikiutil.smileys.keys()), '|')}

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request

        self.macro = None

        self.is_em = 0
        self.is_b = 0
        self.lineno = 0
        self.in_li = 0
        self.in_dd = 0
        self.in_pre = 0
        self.in_table = 0

        # holds the nesting level (in chars) of open lists
        self.list_indents = []
        self.list_types = []


    def _check_p(self):
        if not (self.formatter.in_p or self.in_pre):
            sys.stdout.write(self.formatter.paragraph(1))


    def _close_item(self, result):
        if self.formatter.in_p:
            result.append(self.formatter.paragraph(0))
        if self.in_li:
            self.in_li = 0
            result.append(self.formatter.listitem(0))
        if self.in_dd:
            self.in_dd = 0
            result.append(self.formatter.definition_desc(0))


    def interwiki(self, url_and_text, **kw):
        self._check_p()

        if len(url_and_text) == 1:
            url = url_and_text[0]
            text = None
        else:
            url, text = url_and_text

        url = url[5:] # remove "wiki:"
        if text is None:
            tag, tail = wikiutil.split_wiki(url)
            if tag:
                text = tail
            else:
                text = url
                url = ""
        elif config.allow_subpages and url[0] == '/':
            # fancy link to subpage [wiki:/SubPage text]
            return self._word_repl(url, text)
        elif Page(url).exists():
            # fancy link to local page [wiki:LocalPage text]
            return self._word_repl(url, text)

        import urllib
        wikitag, wikiurl, wikitail = wikiutil.resolve_wiki(url)
        wikiurl = wikiutil.mapURL(wikiurl)
        href = wikiutil.join_wiki(wikiurl, wikitail)

        # check for image URL, and possibly return IMG tag
        if not kw.get('pretty_url', 0) and wikiutil.isPicture(wikitail):
            return self.formatter.image(border=0, src=href)

        # link to self?
        if wikitag is None:
            return self._word_repl(wikitail)
              
        # return InterWiki hyperlink
        prefix = config.url_prefix
        badwiki = wikitag == "BadWikiTag"
        text = self.highlight_text(text) # also cgi.escapes if necessary

        icon = ''
        if self.request.user.show_fancy_links:
            icon = self.formatter.image(width=16, height=16, hspace=2,
                border=badwiki,
                src=prefix+"/img/moin-inter.gif",
                alt="[%s]" % wikitag)
        return self.formatter.url(href, icon + text,
            title=wikitag, unescaped=1, pretty_url=kw.get('pretty_url', 0))


    def attachment(self, url_and_text, **kw):
        """ This gets called on attachment URLs.
        """
        self._check_p()

        if len(url_and_text) == 1:
            url = url_and_text[0]
            text = None
        else:
            url, text = url_and_text

        inline = url[0] == 'i'
        drawing = url[0] == 'd'
        url = string.split(url, ":", 1)[1]
        text = text or url

        pagename = self.formatter.page.page_name
        parts = string.split(url, '/')
        if len(parts) > 1:
            # get attachment from other page
            pagename = string.join(parts[:-1], '/')
            url = parts[-1]

        import urllib
        from MoinMoin.action import AttachFile
        fname = wikiutil.taintfilename(url)
        if drawing:
            drawing = fname
            fname = fname + ".gif"
            url = url + ".gif"
        fpath = os.path.join(AttachFile.getAttachDir(pagename), fname)

        # check whether attachment exists, possibly point to upload form
        if not os.path.exists(fpath):
            if drawing:
                linktext = _('Create new drawing "%(filename)s"')
            else:
                linktext = _('Upload new attachment "%(filename)s"')
            return wikiutil.link_tag(
                '%s?action=AttachFile&rename=%s%s' % (
                    wikiutil.quoteWikiname(pagename),
                    urllib.quote_plus(fname),
                    drawing and ('&drawing=%s' % urllib.quote(drawing)) or ''),
                linktext % {'filename': fname})

        # check for image URL, and possibly return IMG tag
        # (images are always inlined, just like for other URLs)
        if not kw.get('pretty_url', 0) and wikiutil.isPicture(url):
            return self.formatter.image(border=0, alt=url,
                src=AttachFile.getAttachUrl(pagename, url, addts=1))

        # try to inline the attachment (we only accept a list
        # of known extensions)
        base, ext = os.path.splitext(url)
        if inline and ext in ['.py']:
            if ext == '.py':
                import cStringIO
                from MoinMoin.parser import python

                buff = cStringIO.StringIO()
                colorizer = python.Parser(open(fpath, 'r').read(), self.request, out = buff)
                colorizer.format(self.formatter, self.form)
                return self.formatter.preformatted(1) + \
                    self.formatter.rawHTML(buff.getvalue()) + \
                    self.formatter.preformatted(0)

        return self.formatter.url(
            AttachFile.getAttachUrl(pagename, url),
            text, pretty_url=kw.get('pretty_url', 0))


    def _emph_repl(self, word):
        """Handle emphasis, i.e. '' and '''."""
        self._check_p()
        ##print "#", self.is_b, self.is_em, "#"
        if len(word) == 3:
            self.is_b = not self.is_b
            if self.is_em and self.is_b: self.is_b = 2
            return self.formatter.strong(self.is_b)
        else:
            self.is_em = not self.is_em
            if self.is_em and self.is_b: self.is_em = 2
            return self.formatter.emphasis(self.is_em)

    def _emph_ibb_repl(self, word):
        """Handle mixed emphasis, i.e. ''''' followed by '''."""
        self._check_p()
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b: self.is_b = 2
        return self.formatter.emphasis(self.is_em) + self.formatter.strong(self.is_b)

    def _emph_ibi_repl(self, word):
        """Handle mixed emphasis, i.e. ''''' followed by ''."""
        self._check_p()
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b: self.is_em = 2
        return self.formatter.strong(self.is_b) + self.formatter.emphasis(self.is_em)

    def _emph_ib_or_bi_repl(self, word):
        """Handle mixed emphasis, exactly five '''''."""
        self._check_p()
        ##print "*", self.is_b, self.is_em, "*"
        b_before_em = self.is_b > self.is_em > 0
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if b_before_em:
            return self.formatter.strong(self.is_b) + self.formatter.emphasis(self.is_em)
        else:
            return self.formatter.emphasis(self.is_em) + self.formatter.strong(self.is_b)


    def _sup_repl(self, word):
        """Handle superscript."""
        self._check_p()
        return self.formatter.sup(1) + \
            self.highlight_text(word[1:-1]) + \
            self.formatter.sup(0)


    def _rule_repl(self, word):
        """Handle sequences of dashes."""
        result = self._undent()
        if len(word) <= 4:
            result = result + self.formatter.rule()
        else:
            result = result + self.formatter.rule(min(len(word), 10) - 2)
        return result


    def _word_repl(self, word, text=None):
        """Handle WikiNames."""
        self._check_p()
        if not text: text = word
        if config.allow_subpages and word[0] == '/':
            word = self.formatter.page.page_name + word
        text = self.highlight_text(text)
        if word == text:
            return self.formatter.pagelink(word)
        else:
            return self.formatter.pagelink(word, text)

    def _notword_repl(self, word):
        """Handle !NotWikiNames."""
        self._check_p()
        return self.highlight_text(word[1:])


    def _interwiki_repl(self, word):
        """Handle InterWiki links."""
        self._check_p()
        return self.interwiki(["wiki:" + word])


    def _url_repl(self, word):
        """Handle literal URLs including inline images."""
        self._check_p()
        scheme = string.split(word, ":", 1)[0]

        if scheme == "wiki": return self.interwiki([word])
        if scheme in self.attachment_schemas:
            return self.attachment([word])

        return self.formatter.url(word, text=self.highlight_text(word))


    def _wikiname_bracket_repl(self, word):
        """Handle special-char wikinames."""
        return self._word_repl(word[2:-2])


    def _url_bracket_repl(self, word):
        """Handle bracketed URLs."""
        self._check_p()
        words = string.split(word[1:-1], None, 1)
        if len(words) == 1: words = words * 2

        if words[0][0] == '#':
            # anchor link
            return self.formatter.url(words[0], self.highlight_text(words[1]))

        scheme = string.split(words[0], ":", 1)[0]
        if scheme == "wiki": return self.interwiki(words, pretty_url=1)
        if scheme in self.attachment_schemas:
            return self.attachment(words, pretty_url=1)

        icon = ("www", 11, 11)
        if scheme == "mailto": icon = ("email", 14, 10)
        if scheme == "news": icon = ("news", 10, 11)
        if scheme == "telnet": icon = ("telnet", 10, 11)
        if scheme == "ftp": icon = ("ftp", 11, 11)
        if scheme == "file": icon = ("ftp", 11, 11)
        #!!! use a map?
        # http|https|ftp|nntp|news|mailto|wiki|file

        text = ''
        if self.request.user.show_fancy_links:
            text = text + self.formatter.image(
                src="%s/img/moin-%s.gif" % (config.url_prefix, icon[0]),
                width=icon[1], height=icon[2], border=0, hspace=4,
                alt="[%s]" % string.upper(icon[0])
                )
        text = text + self.highlight_text(words[1])
        return self.formatter.url(words[0], text, 'external', pretty_url=1, unescaped=1)


    def _email_repl(self, word):
        """Handle email addresses (without a leading mailto:)."""
        self._check_p()
        return self.formatter.url("mailto:" + word, self.highlight_text(word))


    def _ent_repl(self, word):
        """Handle SGML entities."""
        self._check_p()
        return self.formatter.text(word)
        #return {'&': '&amp;',
        #        '<': '&lt;',
        #        '>': '&gt;'}[word]


    def _ent_numeric_repl(self, word):
        """Handle numeric SGML entities."""
        self._check_p()
        return self.formatter.rawHTML(word)


    def _li_repl(self, match):
        """Handle bullet lists."""
        result = []
        self._close_item(result)
        self.in_li = 1
        result.append(self.formatter.listitem(1))
        result.append(self.formatter.paragraph(1))
        return string.join(result, '')


    def _ol_repl(self, match):
        """Handle numbered lists."""
        return self._li_repl(match)


    def _dl_repl(self, match):
        """Handle definition lists."""
        result = []
        self._close_item(result)
        self.in_dd = 1
        result.extend([
            self.formatter.definition_term(1),
            match[:-3],
            self.formatter.definition_term(0),
            self.formatter.definition_desc(1)
        ])
        return string.join(result, '')


    def _tt_repl(self, word):
        """Handle inline code."""
        self._check_p()
        return self.formatter.code(1) + \
            self.highlight_text(word[3:-3]) + \
            self.formatter.code(0)


    def _tt_bt_repl(self, word):
        """Handle backticked inline code."""
        if len(word) == 2: return ""
        self._check_p()
        return self.formatter.code(1) + \
            self.highlight_text(word[1:-1]) + \
            self.formatter.code(0)


    def _getTableAttrs(self, attrdef):
        # skip "|" and initial "<"
        while attrdef and attrdef[0] == "|":
            attrdef = attrdef[1:]
        if not attrdef or attrdef[0] != "<":
            return {}, ''
        attrdef = attrdef[1:]

        # extension for special table markup
        def table_extension(key, parser, attrs):
            msg = ''
            if key[0] in string.digits:
                token = parser.get_token()
                if token != '%':
                    wanted = '%'
                    msg = _('Expected "%(wanted)s" after "%(key)s", got "%(token)s"') % locals()
                else:
                    try:
                        dummy = int(key)
                    except ValueError:
                        msg = _('Expected an integer "%(key)s" before "%(token)s"') % locals()
                    else:
                        attrs['width'] = '"%s"' % key
            elif key == '-':
                arg = parser.get_token()
                try:
                    dummy = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % locals()
                else:
                    attrs['colspan'] = '"%s"' % arg
            elif key == '|':
                arg = parser.get_token()
                try:
                    dummy = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % locals()
                else:
                    attrs['rowspan'] = '"%s"' % arg
            elif key == '(':
                attrs['align'] = '"left"'
            elif key == ':':
                attrs['align'] = '"center"'
            elif key == ')':
                attrs['align'] = '"right"'
            elif key == '^':
                attrs['valign'] = '"top"'
            elif key == 'v':
                attrs['valign'] = '"bottom"'
            elif key == '#':
                arg = parser.get_token()
                try:
                    if len(arg) != 6: raise ValueError
                    dummy = string.atoi(arg, 16)
                except ValueError:
                    msg = _('Expected a color value "%(arg)s" after "%(key)s"' % locals())
                else:
                    attrs['bgcolor'] = '"%s"' % arg
            else:
                msg = None
            return msg

        # scan attributes
        attr, msg = wikiutil.parseAttributes(attrdef, '>', table_extension)
        if msg: msg = '<strong class="highlight">%s</strong>' % msg
        return attr, msg

    def _tableZ_repl(self, word):
        """Handle table row end."""
        if self.in_table:
            return self.formatter.table_cell(0) + self.formatter.table_row(0)
        else:
            return word


    def _table_repl(self, word):
        """Handle table cell separator."""
        if self.in_table:
            # check for attributes
            attrs, attrerr = self._getTableAttrs(word)

            # start the table row?
            if self.table_rowstart:
                self.table_rowstart = 0
                leader = self.formatter.table_row(1, attrs)
            else:
                leader = self.formatter.table_cell(0)

            # check for adjacent cell markers
            if string.count(word, "|") > 2:
                if not attrs.has_key('align'):
                    attrs['align'] = '"center"'
                if not attrs.has_key('colspan'):
                    attrs['colspan'] = '"%d"' % (string.count(word, "|")/2)

            # return the complete cell markup           
            return leader + self.formatter.table_cell(1, attrs) + attrerr
        else:
            return word


    def _heading_repl(self, word):
        """Handle section headings."""
        import sha

        icons = ''
        if self.request.user.show_topbottom:
            bottom = self.formatter.image(width=14, height=10, hspace=2, vspace=6, align="right",
                border=0, src=config.url_prefix+"/img/moin-bottom.gif", alt="[BOTTOM]")
            icons = icons + self.formatter.url("#bottom", bottom, unescaped=1)
            top = self.formatter.image(width=14, height=10, hspace=2, vspace=6, align="right",
                border=0, src=config.url_prefix+"/img/moin-top.gif", alt="[TOP]")
            icons = icons + self.formatter.url("#top", top, unescaped=1)

        h = string.strip(word)
        level = 1
        while h[level:level+1] == '=': level = level+1
        depth = min(5,level)
        headline = string.strip(h[level:-level])
        return \
            self.formatter.anchordef("head-"+sha.new(headline).hexdigest()) + \
            self.formatter.heading(depth, self.highlight_text(headline, flow=0), icons=icons)


    def _processor_repl(self, word):
        """Handle processed code displays."""
        if word[:3] == '{{{': word = word[3:]

        from MoinMoin.processor import processors
        self.processor = None
        processor_name = string.split(word[2:])[0]
        if processor_name in processors:
            self.processor = util.importName("MoinMoin.processor." +
                processor_name, "process")

        if self.processor:
            self.in_pre = 2
            self.colorize_lines = [word]
            return ''
        else:
            self._check_p()
            self.in_pre = 1
            return self.formatter.preformatted(self.in_pre) + \
                self.formatter.text(word)


    def _pre_repl(self, word):
        """Handle code displays."""
        word = string.strip(word)
        if word == '{{{' and not self.in_pre:
            self._check_p()
            self.in_pre = 1
            return self.formatter.preformatted(self.in_pre)
        elif word == '}}}' and self.in_pre:
            self.in_pre = 0
            return self.formatter.preformatted(self.in_pre)

        return word


    def _smiley_repl(self, word):
        """Handle smileys."""
        self._check_p()
        return wikiutil.getSmiley(word, self.formatter)

    _smileyA_repl = _smiley_repl


    def _comment_repl(self, word):
        return ''


    def _macro_repl(self, word):
        """Handle macros ([[macroname]])."""
        self._check_p()
        macro_name = word[2:-2]

        # check for arguments
        args = None
        if string.count(macro_name, "("):
            macro_name, args = string.split(macro_name, '(', 1)
            args = args[:-1]

        # create macro instance
        if self.macro is None:
            self.macro = wikimacro.Macro(self)

        # call the macro
        return self.macro.execute(macro_name, args)


    def _indent_level(self):
        """Return current char-wise indent level."""
        return len(self.list_indents) and self.list_indents[-1]


    def _indent_to(self, new_level, list_type, numtype, numstart):
        """Close and open lists."""
        close = []
        open = ''

        # Close open paragraphs and list items
        if self._indent_level() != new_level:
            self._close_item(close)

        # Close lists while char-wise indent is greater than the current one
        while self._indent_level() > new_level:
            if self.list_types[-1] == 'ol':
                close.append(self.formatter.number_list(0))
            elif self.list_types[-1] == 'dl':
                close.append(self.formatter.definition_list(0))
            else:
                close.append(self.formatter.bullet_list(0))

            del(self.list_indents[-1])
            del(self.list_types[-1])

        # Open new list, if necessary
        if self._indent_level() < new_level:
            self.list_indents.append(new_level)
            self.list_types.append(list_type)
            if list_type == 'ol':
                open = open + self.formatter.number_list(1, numtype, numstart)
            elif list_type == 'dl':
                open = open + self.formatter.definition_list(1)
            else:
                open = open + self.formatter.bullet_list(1)

        # If list level changes, close an open table
        if self.in_table and (open or close):
            close[0:0] = [self.formatter.table(0)]
            self.in_table = 0

        return string.join(close, '') + open


    def _undent(self):
        """Close all open lists."""
        result = []
        self._close_item(result)
        for type in self.list_types:
            if type == 'ol':
                result.append(self.formatter.number_list(0))
            elif type == 'dl':
                result.append(self.formatter.definition_list(0))
            else:
                result.append(self.formatter.bullet_list(0))
        self.list_indents = []
        self.list_types = []
        return string.join(result, '')


    def highlight_text(self, text, **kw):
        if kw.get('flow', 1): self._check_p()
        if not self.hilite_re: return self.formatter.text(text)

        result = []
        lastpos = 0
        match = self.hilite_re.search(text)
        while match and lastpos < len(text):
            # add the match we found
            result.append(self.formatter.text(text[lastpos:match.start()]))
            result.append(self.formatter.highlight(1))
            result.append(self.formatter.text(match.group(0)))
            result.append(self.formatter.highlight(0))

            # search for the next one
            lastpos = match.end() + (match.end() == lastpos)
            match = self.hilite_re.search(text, lastpos)

        result.append(self.formatter.text(text[lastpos:]))
        return string.join(result, '')

    def highlight_scan(self, scan_re, line):
        result = []
        lastpos = 0
        match = scan_re.search(line)
        while match and lastpos < len(line):
            # add the match we found
            result.append(self.highlight_text(line[lastpos:match.start()]))
            result.append(self.replace(match))

            # search for the next one
            lastpos = match.end() + (match.end() == lastpos)
            match = scan_re.search(line, lastpos)

        result.append(self.highlight_text(line[lastpos:]))
        return string.join(result, '')


    def replace(self, match):
        #hit = filter(lambda g: g[1], match.groupdict().items())
        for type, hit in match.groupdict().items():
            if hit is not None and type != "hmarker":
                ##print "###", cgi.escape(`type`), cgi.escape(`hit`), "###"
                if self.in_pre and type not in ['pre', 'ent']:
                    return self.highlight_text(hit)
                else:
                    return apply(getattr(self, '_' + type + '_repl'), (hit,))
        else:
            import pprint
            raise Exception("Can't handle match " + `match`
                + "\n" + pprint.pformat(match.groupdict())
                + "\n" + pprint.pformat(match.groups()) )

        return ""


    def format(self, formatter, form):
        """ For each line, scan through looking for magic
            strings, outputting verbatim any intervening text.
        """
        self.formatter = formatter
        self.form = form
        self.hilite_re = self.formatter.page.hilite_re

        # prepare regex patterns
        rules = string.replace(self.formatting_rules, '\n', '|')
        if config.allow_extended_names:
            rules = rules + r'|(?P<wikiname_bracket>\[".*?"\])'
        if config.bang_meta:
            rules = r'(?P<notword>!%(word_rule)s)|%(rules)s' % {
                'word_rule': self.word_rule,
                'rules': rules,
            }
        if config.backtick_meta:
            rules = rules + r'|(?P<tt_bt>`.*?`)'
        if config.allow_numeric_entities:
            rules = r'(?P<ent_numeric>&#\d{1,5};)|' + rules

        scan_re = re.compile(rules)
        number_re = re.compile(self.ol_rule)
        term_re = re.compile(self.dl_rule)
        indent_re = re.compile("^\s*")
        eol_re = re.compile(r'\r?\n')

        # get text and replace TABs
        rawtext = string.expandtabs(self.raw)

        # go through the lines
        self.lineno = 0
        self.lines = eol_re.split(rawtext)
        for line in self.lines:
            self.lineno = self.lineno + 1
            self.table_rowstart = 1

            if self.in_pre:
                if self.in_pre == 2:
                    # processing mode
                    endpos = string.find(line, "}}}")
                    if endpos == -1:
                        self.colorize_lines.append(line)
                        continue

                    self.processor(self.request, self.formatter, self.colorize_lines)
                    del self.colorize_lines
                    self.in_pre = 0

                    # send rest of line through regex machinery
                    line = line[endpos+3:]                    
                elif string.strip(line)[:2] == "#!" and string.find(line, 'python') > 0:
                    from MoinMoin.processor.Colorize import process
                    self.processor = process
                    self.in_pre = 2
                    self.colorize_lines = [line]
                    continue
            else:
                # paragraph break on empty lines
                if not string.strip(line):
                    if self.formatter.in_p:
                        sys.stdout.write(self.formatter.paragraph(0))
                    if self.in_table:
                        sys.stdout.write(self.formatter.table(0))
                        self.in_table = 0
                    continue

                # check indent level
                indent = indent_re.match(line)
                indlen = len(indent.group(0))
                indtype = "ul"
                numtype = None
                numstart = None
                if indlen:
                    match = number_re.match(line)
                    if match:
                        numtype, numstart = string.split(string.strip(match.group(0)), '.')
                        numtype = numtype[0]

                        if numstart and numstart[0] == "#":
                            numstart = int(numstart[1:])
                        else:
                            numstart = None

                        indtype = "ol"
                    else:
                        match = term_re.match(line)
                        if match:
                            indtype = "dl"

                # output proper indentation tags
                print self._indent_to(indlen, indtype, numtype, numstart)

                # start or end table mode
                if not self.in_table and line[indlen:indlen+2] == "||" and line[-2:] == "||":
                    attrs, attrerr = self._getTableAttrs(line[indlen+2:])
                    sys.stdout.write(self.formatter.table(1, attrs) + attrerr)
                    self.in_table = self.lineno
                elif self.in_table and not(line[indlen:indlen+2] == "||" and line[-2:] == "||"):
                    sys.stdout.write(self.formatter.table(0))
                    self.in_table = 0

            # convert line from wiki markup to HTML and print it
            if self.hilite_re:
                sys.stdout.write(self.highlight_scan(scan_re, line + " "))
            else:
                line, count = re.subn(scan_re, self.replace, line + " ")
                ##if not count: self._check_p()
                self._check_p()
                sys.stdout.write(line)

            if self.in_pre:
                sys.stdout.write(self.formatter.linebreak())
            #if self.in_li:
            #    self.in_li = 0
            #    sys.stdout.write(self.formatter.listitem(0))

        # close code displays, paragraphs, tables and open lists
        if self.in_pre: sys.stdout.write(self.formatter.preformatted(0))
        if self.formatter.in_p: sys.stdout.write(self.formatter.paragraph(0))
        if self.in_table: sys.stdout.write(self.formatter.table(0))
        sys.stdout.write(self._undent())

