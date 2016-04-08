"""
    MoinMoin - MoinMoin Wiki Markup Parser

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wiki.py,v 1.15 2000/12/05 19:34:43 jhermann Exp $
"""

# Imports
import cgi, re, string, sys
from MoinMoin import config, wikimacro, wikiutil
from MoinMoin.Page import Page


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

    ol_rule = r"^\s+[0-9aAiI]\.(?:#\d+)?\s"

    formatting_rules = r"""(?:(?P<emph_ibb>'''''(?=[^']+'''))
(?P<emph>'{2,3})
(?P<tt>\{\{\{.*?\}\}\})
(?P<pre>(\{\{\{ ?|\}\}\}))
(?P<rule>-{4,})
(?P<comment>^\#\#.*$)
(?P<macro>\[\[(%(macronames)s)(?:\(.*?\))?\]\]))
(?P<li>^\s+\*)
(?P<ol>%(ol_rule)s)
(?P<tableZ>\|\| $)
(?P<table>(?:\|\|)+(?=.))
(?P<heading>^\s*(?P<hmarker>=+)\s.*\s(?P=hmarker) $)
(?P<interwiki>[A-Z][a-zA-Z]+\:[^\s'\"\:\<]([^\s%(punct)s]|([%(punct)s][^\s%(punct)s]))+)
(?P<word>(?:[%(u)s][%(l)s]+){2,})
(?P<url_bracket>\[(%(url)s)\:[^\s\]]+(\s[^\]]+)?\])
(?P<url>(%(url)s)\:([^\s\<%(punct)s]|([%(punct)s][^\s\<%(punct)s]))+)
(?P<email>[-\w._+]+\@[\w.-]+)
(?P<smiley>\s(%(smiley)s)\s)
(?P<smileyA>^(%(smiley)s)\s)
(?P<ent>[<>&])"""  % {
        'url': 'http|https|ftp|nntp|news|mailto|telnet|wiki',
        'punct': re.escape('''"'}]|:,.)?!'''),
        'macronames': string.join(wikimacro.names, '|'),
        'ol_rule': ol_rule,
        'u': config.upperletters,
        'l': config.lowerletters,
        'smiley': string.join(map(re.escape, wikiutil.smileys.keys()), '|')}

    def __init__(self, raw):
        self.raw = raw

        self.macro = None

        self.is_em = 0
        self.is_b = 0
        self.lineno = 0
        self.in_pre = 0
        self.in_table = 0

        # holds the nesting level (in chars) of open lists
        self.list_indents = []
        self.list_types = []

    def interwiki(self, url_and_text):
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

        wikitag, wikiurl, wikitail = wikiutil.resolve_wiki(url)

        # check for image URL, and possibly return IMG tag
        if wikiutil.isPicture(wikitail):
            return '<img src="%s%s" border="0">' % (wikiurl, wikitail)

        # return InterWiki hyperlink
        return '<a href="%s"><img src="%s/img/moin-inter.gif" width="16" height="16" hspace="2" border="%d" alt="[%s]"></a><a href="%s%s">%s</a>' % (
            wikiurl, config.url_prefix, wikitag == "BadWikiTag", wikitag, wikiurl, wikitail, text)

    def _emph_repl(self, word):
        """Handle emphasis, i.e. '' and '''."""
        if len(word) == 3:
            self.is_b = not self.is_b
            return self.formatter.strong(self.is_b)
        else:
            self.is_em = not self.is_em
            return self.formatter.emphasis(self.is_em)

    def _emph_ibb_repl(self, word):
        """Handle mixed emphasis, i.e. ''''' followed by '''."""
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        return self.formatter.emphasis(self.is_em) + self.formatter.strong(self.is_b)


    def _rule_repl(self, word):
        """Handle sequences of dashes."""
        result = self._undent()
        if len(word) <= 4:
            result = result + self.formatter.rule()
        else:
            result = result + self.formatter.rule(min(len(word), 10) - 2)
        return result

    def _word_repl(self, word):
        """Handle WikiNames."""
        return self.formatter.pagelink(word)


    def _interwiki_repl(self, word):
        """Handle InterWiki links."""
        #!!! handle this correctly
        return self.interwiki(["wiki:" + word])


    def _url_repl(self, word):
        """Handle literal URLs including inline images."""
        if word[:5] == "wiki:": return self.interwiki([word])
        return self.formatter.url(word)


    def _wikiname_bracket_repl(self, word):
        """Handle special-char wikinames."""
        wikiname = word[2:-2]
        return self.formatter.pagelink(wikiname)


    def _url_bracket_repl(self, word):
        """Handle bracketed URLs."""
        words = string.split(word[1:-1], None, 1)
        if len(words) == 1: words = words * 2
        scheme = string.split(words[0], ":", 1)[0]

        if scheme == "wiki": return self.interwiki(words)

        icon = ("www", 11, 11)
        if scheme == "mailto": icon = ("email", 14, 10)
        if scheme == "news": icon = ("news", 10, 11)
        if scheme == "telnet": icon = ("telnet", 10, 11)
        if scheme == "ftp": icon = ("ftp", 11, 11)
        #!!! use a map?
        # http|https|ftp|nntp|news|mailto|wiki

        text = '<img src="%s/img/moin-%s.gif" width="%d" height="%d" border="0" hspace="4" alt="[%s]">%s' % (
            config.url_prefix, icon[0], icon[1], icon[2], string.upper(icon[0]), words[1])
        return self.formatter.url(words[0], text, 'external')


    def _email_repl(self, word):
        """Handle email addresses (without a leading mailto:)."""
        return self.formatter.url("mailto:" + word, word)


    def _ent_repl(self, word):
        """Handle SGML entities."""
        return self.formatter.text(word)
        #return {'&': '&amp;',
        #        '<': '&lt;',
        #        '>': '&gt;'}[word]
    

    def _li_repl(self, match):
        """Handle bullet lists."""
        return self.formatter.listitem(1)


    def _ol_repl(self, match):
        """Handle numbered lists."""
        return self.formatter.listitem(1)


    def _tt_repl(self, word):
        """Handle inline code."""
        return self.formatter.code(word[3:-3])


    def _tableZ_repl(self, word):
        """Handle table row end."""
        if self.in_table:
            return '</td>\n</tr>'
        else:
            return word

    def _table_repl(self, word):
        """Handle table cell separator."""
        if self.in_table:
            str = ''

            # start the table row?
            if self.table_rowstart:
                self.table_rowstart = 0
                str = str + '<tr class="wiki">\n'

            # check for adjacent cell markers
            colspan = ''
            if len(word) > 2:
                colspan = ' align="center" colspan="%d"' % (len(word)/2,)

            # return the complete cell markup           
            return '%s</td>\n<td class="wiki"%s>' % (str, colspan)
        else:
            return word


    def _heading_repl(self, word):
        """Handle section headings."""
        h = string.strip(word)
        level = 1
        while h[level:level+1] == '=': level = level+1
        depth = min(5,level)
        return self.formatter.anchordef("line%d" % self.lineno) + \
            self.formatter.heading(depth, h[level:-level])


    def _pre_repl(self, word):
        """Handle code displays."""
        word = string.strip(word)
        if word == '{{{' and not self.in_pre:
            self.in_pre = 1
            return self.formatter.preformatted(self.in_pre)
        elif word == '}}}' and self.in_pre:
            self.in_pre = 0
            return self.formatter.preformatted(self.in_pre)

        return word

    def _smiley_repl(self, word):
        """Handle smileys."""
        return wikiutil.getSmiley(string.strip(word))

    _smileyA_repl = _smiley_repl


    def _comment_repl(self, word):
        return ''


    def _macro_repl(self, word):
        """Handle macros ([[macroname]])."""
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
        close = ''
        open = ''

        # Close lists while char-wise indent is greater than the current one
        while self._indent_level() > new_level:
            if self.list_types[-1] == 'ol':
                close = close + self.formatter.number_list(0)
            else:
                close = close + self.formatter.bullet_list(0)

            del(self.list_indents[-1])
            del(self.list_types[-1])

        # Open new list, if necessary
        if self._indent_level() < new_level:
            self.list_indents.append(new_level)
            self.list_types.append(list_type)
            if list_type == 'ol':
                open = open + self.formatter.number_list(1, numtype, numstart)
            else:
                open = open + self.formatter.bullet_list(1)

        # If list level changes, close an open table
        if self.in_table and (open or close):
            close = self.formatter.table(0) + close
            self.in_table = 0

        return close + open


    def _undent(self):
        """Close all open lists."""
        result = ''
        for type in self.list_types:
            if type == 'ol':
                result = result + self.formatter.number_list(0)
            else:
                result = result + self.formatter.bullet_list(0)
        self.list_indents = []
        self.list_types = []
        return result


    def replace(self, match):
        #hit = filter(lambda g: g[1], match.groupdict().items())
        for type, hit in match.groupdict().items():
            if hit is not None:
                if self.in_pre and type not in ['pre', 'ent']:
                    return self.formatter.text(hit)
                else:
                    return apply(getattr(self, '_' + type + '_repl'), (hit,))
        else:
            import pprint
            raise ("Can't handle match " + `match`
                + "\n" + pprint.pformat(match.groupdict())
                + "\n" + pprint.pformat(match.groups()) )

        return ""
        

    def format(self, formatter, form):
        """ For each line, scan through looking for magic
            strings, outputting verbatim any intervening text.
        """
        self.formatter = formatter
        self.form = form

        # prepare regex patterns
        rules = string.replace(self.__class__.formatting_rules, '\n', '|')
        if config.allow_extended_names:
            rules = rules + r'|(?P<wikiname_bracket>\[".*?"\])'
        scan_re = re.compile(rules)
        number_re = re.compile(self.__class__.ol_rule)
        indent_re = re.compile("^\s*")
        eol_re = re.compile(r'\r?\n')

        # get text and replaces TABs
        rawtext = string.expandtabs(self.raw)

        # go through the lines
        self.lineno = 0
        self.lines = eol_re.split(rawtext)
        for line in self.lines:
            self.lineno = self.lineno + 1
            self.table_rowstart = 1

            if not self.in_pre:
                # paragraph break on empty lines
                if not string.strip(line):
                    if self.in_table:
                        sys.stdout.write(self.formatter.table(0))
                        self.in_table = 0
                    sys.stdout.write(self.formatter.paragraph())
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

                        if numstart and numstart[0] == "#":
                            numstart = int(numstart[1:])
                        else:
                            numstart = None

                        indtype = "ol"

                # output proper indentation tags
                print self._indent_to(indlen, indtype, numtype, numstart)

                # start or end table mode
                if not self.in_table and line[indlen:indlen+2] == "||" and line[-2:] == "||":
                    sys.stdout.write(self.formatter.table(1))
                    self.in_table = self.lineno
                elif self.in_table and not(line[indlen:indlen+2] == "||" and line[-2:] == "||"):
                    sys.stdout.write(self.formatter.table(0))
                    self.in_table = 0

            # convert line from wiki markup to HTML and print it            
            sys.stdout.write(re.sub(scan_re, self.replace, line + " ")) #string.rstrip(line)))

            if self.in_pre:
                sys.stdout.write(self.formatter.linebreak())

        # close code displays, tables and open lists
        if self.in_pre: sys.stdout.write(self.formatter.preformatted(0))
        if self.in_table: sys.stdout.write(self.formatter.table(0))
        sys.stdout.write(self._undent())

