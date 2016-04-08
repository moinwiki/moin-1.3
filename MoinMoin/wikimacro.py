# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Macro Implementation

    Copyright (c) 2000, 2001, 2002 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    These macros are used by the parser/wiki.py module
    to implement complex and/or dynamic page content.

    The sub-package "MoinMoin.macro" contains external
    macros, you can place your extensions there.

    $Id: wikimacro.py,v 1.69 2003/11/09 21:00:52 thomaswaldmann Exp $
"""

# Imports
import os, re, string, sys, time
from MoinMoin import action, config, editlog, macro, user, util
from MoinMoin import version, wikiutil, wikiaction, i18n
from MoinMoin.Page import Page
from MoinMoin.util import pysupport


#############################################################################
### Globals
#############################################################################

names = ["TitleSearch", "WordIndex", "TitleIndex",
         "GoTo", "InterWiki", "SystemInfo", "PageCount", "UserPreferences",
         # Macros with arguments
         "Icon", "PageList", "Date", "DateTime", "Anchor", "MailTo"
]

# external macros
names.extend(macro.extension_macros)

# languages
names.extend(i18n.languages.keys())

# plugins
_plugins = os.path.join(config.plugin_dir, 'macro')
plugin_macros = []
if os.path.isdir(_plugins):
    plugin_macros = pysupport.getPackageModules(os.path.join(_plugins, 'dummy'))
    names.extend(plugin_macros)


#############################################################################
### Helpers
#############################################################################

def _make_index_key(index_letters, additional_html=""):
    index_letters.sort()
    s = '<p><center>'
    links = map(lambda ch:
                    '<a href="#%s">%s</a>' %
                    (wikiutil.quoteWikiname(ch), string.replace(ch, '~', 'Others')),
                index_letters)
    s = s + string.join(links, ' | ')
    s = s + additional_html + '</center><p>'
    return s


def execute_external_macro(macro_name, function, args):
    """ Call `function` with `args` in an external macro `macro_name`.
    """
    # load extension macro
    if macro_name in macro.extension_macros:
        execute = pysupport.importName("MoinMoin.macro." + macro_name, function)
        return execute(*args)

    # try plugin dir
    # !!! plugin dir should prolly take precedence, but changing this should
    # be done uniformly to all extensions (actions, etc.)
    if macro_name in plugin_macros:
        execute = pysupport.importPlugin(_plugins, "MoinMoin.plugin.macro", macro_name, function)
        return execute(*args)

    raise ImportError("Cannot load macro %s" % macro_name)


#############################################################################
### Macros - Handlers for [[macroname]] markup
#############################################################################

class Macro:
    """ Macro handler """

    def __init__(self, parser):
        self.parser = parser
        self.formatter = self.parser.formatter
        self.form = self.parser.form
        self.request = self.parser.request
        self._ = self.request.getText

        # make formatter available in request, so macros
        # can rely on that
        self.request.formatter = self.formatter

    def execute(self, macro_name, args):
        builtins = vars(self.__class__)
        if builtins.has_key('_macro_' + macro_name):
            return builtins['_macro_' + macro_name](self, args)

        # language macro
        if i18n.languages.has_key(macro_name):
            self.request.current_lang = macro_name
            return ''

        return execute_external_macro(macro_name, "execute", (self, args))

    def _macro_TitleSearch(self, args):
        return self._m_search("titlesearch")

    def _m_search(self, type):
        import cgi

        if self.form.has_key('value'):
            default = self.form["value"].value
        else:
            default = ''
        boxes = ''
        if type == "fullsearch":
            boxes = (
                  '<br><input type="checkbox" name="context" value="40" checked>'
                + self._('Display context of search results')
                + '<br><input type="checkbox" name="case" value="1">'
                + self._('Case-sensitive searching')
            )
        return self.formatter.rawHTML((
            '<form method="GET">'
            '<input type="hidden" name="action" value="%s">'
            '<input name="value" size="30" value="%s">&nbsp;'
            '<input type="submit" value="%s">'
            '%s</form>') % (type, cgi.escape(default, quote=1), self._("Go"), boxes))

    def _macro_GoTo(self, args):
        return self.formatter.rawHTML("""<form method="get"><input name="goto" size="30">
        <input type="submit" value="%s">
        </form>""" % self._("Go"))

    def _macro_WordIndex(self, args):
        index_letters = []
        s = ''
        pages = list(wikiutil.getPageList(config.text_dir))
        pages = filter(self.request.user.may.read, pages)
        map = {}
        word_re = re.compile('[%s][%s]+' % (config.upperletters, config.lowerletters))
        for name in pages:
            for word in word_re.findall(name):
                try:
                    if not map[word].count(name):
                        map[word].append(name)
                except KeyError:
                    map[word] = [name]

        all_words = map.keys()
        all_words.sort()
        last_letter = None
        for word in all_words:
            if wikiutil.isUnicodeName(word): continue

            letter = word[0]
            if letter <> last_letter:
                s = s + '<a name="%s"><h3>%s</h3></a>' % (wikiutil.quoteWikiname(letter), letter)
                last_letter = letter
            if letter not in index_letters:
                index_letters.append(letter)

            s = s + '<b>%s</b><ul>' % word
            links = map[word]
            links.sort()
            last_page = None
            for name in links:
                if name == last_page: continue
                s = s + '<li>' + Page(name).link_to()
            s = s + '</ul>\n'
        return _make_index_key(index_letters) + s


    def _macro_TitleIndex(self, args):
        from MoinMoin import wikixml

        s = ''
        index_letters = []
        allpages = int(self.form.getvalue('allpages', 0)) != 0
        pages = list(wikiutil.getPageList(config.text_dir))
        pages = filter(self.request.user.may.read, pages)
        if not allpages:
            pages = [p for p in pages if not wikiutil.isSystemPage(p)]
        pages.sort()
        current_letter = None
        for name in pages:
            letter = name[0]
            if wikiutil.isUnicodeName(letter):
                try:
                    letter = wikiutil.getUnicodeIndexGroup(unicode(name, config.charset))
                    if letter: letter = letter.encode(config.charset)
                except UnicodeError:
                    letter = None
                if not letter: letter = "~"
            if letter not in index_letters:
                index_letters.append(letter)
            if letter <> current_letter:
                s = s + '<a name="%s"><h3>%s</h3></a>' % (
                    wikiutil.quoteWikiname(letter), string.replace(letter, '~', 'Others'))
                current_letter = letter
            else:
                s = s + '<br>'
            s = s + Page(name).link_to(attachment_indicator=1) + '\n'

        # add rss link
        index = ''
        if 0 and wikixml.ok: # !!! currently switched off (not implemented)
            img = self.formatter.image(width=36, height=14, hspace=2, align="right",
                border=0, src=config.url_prefix+"/img/moin-rss.gif", alt="[RSS]")
            index = index + self.formatter.url(
                wikiutil.quoteWikiname(self.formatter.page.page_name) + "?action=rss_ti",
                img, unescaped=1)

        qpagename = wikiutil.quoteWikiname(self.formatter.page.page_name)
        index = index + _make_index_key(index_letters, """<br>
<a href="%s?allpages=%d">%s</a>&nbsp;|
<a href="%s?action=titleindex">%s</a>&nbsp;|
<a href="%s?action=titleindex&mimetype=text/xml">%s</a>
""" % (qpagename, not allpages, (self._('Include system pages'), self._('Exclude system pages'))[allpages],
       qpagename, self._('Plain title index'),
       qpagename, self._('XML title index')) )

        return index + s


    def _macro_InterWiki(self, args):
        from cStringIO import StringIO

        # load interwiki list
        dummy = wikiutil.resolve_wiki('')

        buf = StringIO()
        buf.write('<table border=0 cellspacing=2 cellpadding=0>')
        list = wikiutil._interwiki_list.items()
        list.sort()
        for tag, url in list:
            buf.write('<tr><td><tt><a href="%s">%s</a>&nbsp;&nbsp;</tt></td>' % (
                wikiutil.join_wiki(url, 'RecentChanges'), tag))
            if string.find(url, '$PAGE') == -1:
                buf.write('<td><tt><a href="%s">%s</a></tt></td>' % (url, url))
            else:
                buf.write('<td><tt>%s</tt></td>' % url)
            buf.write('</tr>\n')
        buf.write('</table>')

        return self.formatter.rawHTML(buf.getvalue())


    def _macro_SystemInfo(self, args):
        import operator
        from cStringIO import StringIO
        from MoinMoin import processor

        # check for 4XSLT
        try:
            import Ft
            ftversion = Ft.__version__
        except ImportError:
            ftversion = None
        except AttributeError:
            ftversion = 'N/A'

        pagelist = wikiutil.getPageList(config.text_dir)
        totalsize = reduce(operator.add, [Page(name).size() for name in pagelist])

        buf = StringIO()
        row = lambda label, value, buf=buf: buf.write(
            '<tr><td valign="top" nowrap><b>%s</b></td><td>&nbsp;&nbsp;</td><td>%s</td></tr>' %
            (label, value))

        buf.write('<table border=0 cellspacing=2 cellpadding=0>')
        row(self._('Python Version'), sys.version)
        row(self._('MoinMoin Version'), self._('Release %s [Revision %s]') % (version.release, version.revision))
        if ftversion:
            row(self._('4Suite Version'), ftversion)
        row(self._('Number of pages'), len(pagelist))
        row(self._('Number of system pages'), len(filter(wikiutil.isSystemPage, pagelist)))
        row(self._('Number of backup versions'), len(wikiutil.getBackupList(config.backup_dir, None)))
        row(self._('Accumulated page sizes'), totalsize)

        edlog = editlog.EditLog(self.request)
        row(self._('Entries in edit log'), self._("%(logcount)s (%(logsize)s bytes)") %
            {'logcount': len(edlog), 'logsize': edlog.size()})

        # !!! This puts a heavy load on the server when the log is large,
        # and it can appear on normal pages ==> so disable it for now.
        if 0:
            eventlogger = self.request.getEventLogger()
            row(self._('Entries in event log'), self._("%(logcount)s (%(logsize)s bytes)") %
                {'logcount': len(eventlogger.read()), 'logsize': eventlogger.size()})

        row(self._('Global extension macros'), 
            string.join(macro.extension_macros, ', ') or self._("<b>NONE</b>"))
        row(self._('Local extension macros'), 
            string.join(plugin_macros, ', ') or self._("<b>NONE</b>"))
        row(self._('Global extension actions'), 
            string.join(action.extension_actions, ', ') or self._("<b>NONE</b>"))
        row(self._('Local extension actions'), 
            string.join(wikiaction.getPlugins()[1], ', ') or self._("<b>NONE</b>"))
        row(self._('Installed processors'), 
            string.join(processor.processors, ', ') or self._("<b>NONE</b>"))
        buf.write('</table>')

        return self.formatter.rawHTML(buf.getvalue())


    def _macro_PageCount(self, args):
        return self.formatter.text("%d" % (len(wikiutil.getPageList(config.text_dir)),))


    def _macro_Icon(self, args):
        return self.formatter.image(border=0, hspace=2,
            src="%s/img/%s" % (config.url_prefix, args))


    def _macro_PageList(self, args):
        try:
            needle_re = re.compile(args or '', re.IGNORECASE)
        except re.error, e:
            return "<b>%s: %s</b>" % (
                self._("ERROR in regex '%s'") % (args,), e)

        all_pages = wikiutil.getPageList(config.text_dir)
        hits = filter(needle_re.search, all_pages)
        hits.sort()
        hits = filter(self.request.user.may.read, hits)

        result = self.formatter.bullet_list(1)
        for filename in hits:
            result = result + self.formatter.listitem(1)
            result = result + self.formatter.pagelink(filename, generated=1)
            result = result + self.formatter.listitem(0)
        result = result + self.formatter.bullet_list(0)
        return result


    def __get_Date(self, args, format_date):
        if not args:
            tm = time.time() # always UTC
        elif len(args) >= 19 and args[4] == '-' and args[7] == '-' \
                and args[10] == 'T' and args[13] == ':' and args[16] == ':':
            # we ignore any time zone offsets here, assume UTC,
            # and accept (and ignore) any trailing stuff
            try:
                tm = (
                    int(args[0:4]),
                    int(args[5:7]),
                    int(args[8:10]),
                    int(args[11:13]),
                    int(args[14:16]),
                    int(args[17:19]),
                    0, 0, 0
                )
            except ValueError, e:
                return "<b>%s: %s</b>" % (
                    self._("Bad timestamp '%s'") % (args,), e)
     	    # as mktime wants a localtime argument (but we only have UTC),
            # we adjust by our local timezone's offset
     	    tm = time.mktime(tm) - time.timezone
        else:
            # try raw seconds since epoch in UTC
            try:
                tm = float(args)
            except ValueError, e:
                return "<b>%s: %s</b>" % (
                    self._("Bad timestamp '%s'") % (args,), e)
        return format_date(tm)

    def _macro_Date(self, args):
        return self.__get_Date(args, self.request.user.getFormattedDate)

    def _macro_DateTime(self, args):
        return self.__get_Date(args, self.request.user.getFormattedDateTime)


    def _macro_UserPreferences(self, args):
        from MoinMoin import userform
        return self.formatter.rawHTML(userform.getUserForm(self.request))

    def _macro_Anchor(self, args):
        return self.formatter.anchordef(args or "anchor")

    def _macro_MailTo(self, args):
        from MoinMoin.util.mail import decodeSpamSafeEmail

        args = args or ''
        if args.find(',') == -1:
            email = args
            text = ''
        else:
            email, text = args.split(',', 1)

        email, text = email.strip(), text.strip()

        if self.request.user.valid:
            # decode address and generate mailto: link
            email = decodeSpamSafeEmail(email)
            text = util.web.getLinkIcon(self.request, self.formatter, "mailto") + \
                self.formatter.text(text or email)
            result = self.formatter.url('mailto:' + email, text, 'external', pretty_url=1, unescaped=1)
        else:
            # unknown user, maybe even a spambot, so
            # just return text as given in macro args
            email = self.formatter.code(1) + \
                self.formatter.text("<%s>" % email) + \
                self.formatter.code(0)
            if text:
                result = self.formatter.text(text) + " " + email
            else:
                result = email

        return result

