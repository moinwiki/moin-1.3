"""
    MoinMoin - Macro Implementation

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    These macros are used by the parser/wiki.py module
    to implement complex and/or dynamic page content.

    The sub-package "MoinMoin.macro" contains external
    macros, you can place your extensions there.

    $Id: wikimacro.py,v 1.33 2002/03/06 22:36:52 jhermann Exp $
"""

# Imports
import os, re, string, sys, time
from MoinMoin import action, config, editlog, macro, user, util
from MoinMoin import version, wikiutil, wikiaction
from MoinMoin.Page import Page, request
from MoinMoin.i18n import _


#############################################################################
### Globals
#############################################################################

names = ["TitleSearch", "WordIndex", "TitleIndex",
         "GoTo", "InterWiki", "SystemInfo", "PageCount", "UserPreferences",
         # Macros with arguments
         "Icon", "PageList", "Date", "DateTime", "Anchor",
]

# external macros
names.extend(macro.extension_macros)

# plugins
_plugins = os.path.join(config.plugin_dir, 'macro')
plugin_macros = []
if os.path.isdir(_plugins):
    plugin_macros = util.getPackageModules(os.path.join(_plugins, 'dummy'))
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


#############################################################################
### Macros - Handlers for [[macroname]] markup
#############################################################################

class Macro:
    """ Macro handler """

    def __init__(self, parser):
        self.parser = parser
        self.formatter = self.parser.formatter
        self.form = self.parser.form
        self.request = request

    def execute(self, macro_name, args):
        builtins = vars(self.__class__)
        if builtins.has_key('_macro_' + macro_name):
            return apply(builtins['_macro_' + macro_name], (self, args))

        # load extension macro
        if macro_name in macro.extension_macros:
            execute = util.importName("MoinMoin.macro." + macro_name, "execute")
            return apply(execute, (self, args))

        # try plugin dir
        if macro_name in plugin_macros:
            execute = util.importPlugin(_plugins, "MoinMoin.plugin.macro", macro_name, "execute")
            return apply(execute, (self, args))

        raise ImportError("Cannot load macro %s" % macro_name)

    def _macro_TitleSearch(self, args):
        return self._m_search("titlesearch")

    def _m_search(self, type):
        if self.form.has_key('value'):
            default = self.form["value"].value
        else:
            default = ''
        return self.formatter.rawHTML("""<form method="get">
        <input type="hidden" name="action" value="%s"> 
        <input name="value" size="30" value="%s"> 
        <input type="submit" value="%s">
        </form>""" % (type, default, _("Go")))

    def _macro_GoTo(self, args):
        return self.formatter.rawHTML("""<form method="get"><input name="goto" size="30">
        <input type="submit" value="%s">
        </form>""" % _("Go"))

    def _macro_WordIndex(self, args):
        index_letters = []
        s = ''
        pages = list(wikiutil.getPageList(config.text_dir))
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
        pages = list(wikiutil.getPageList(config.text_dir))
        pages.sort()
        current_letter = None
        for name in pages:
            letter = name[0]
            if wikiutil.isUnicodeName(name):
                letter = "~"
            if letter not in index_letters:
                index_letters.append(letter)
            if letter <> current_letter:
                s = s + '<a name="%s"><h3>%s</h3></a>' % (
                    wikiutil.quoteWikiname(letter), string.replace(letter, '~', 'Others'))
                current_letter = letter
            else:
                s = s + '<br>'
            s = s + Page(name).link_to() + '\n'

        # add rss link
        index = ''
        if 0 and wikixml.ok: # !!! currently switched off (not implemented)
            img = self.formatter.image(width=36, height=14, hspace=2, align="right",
                border=0, src=config.url_prefix+"/img/moin-rss.gif", alt="[RSS]")
            index = index + self.formatter.url(
                wikiutil.quoteWikiname(self.formatter.page.page_name) + "?action=rss_ti",
                img, unescaped=1)

        index = index + _make_index_key(index_letters, """<br>
<a href="?action=titleindex">%s</a>&nbsp;|
<a href="?action=titleindex&mimetype=text/xml">%s</a>
""" % (_('Plain title index'), _('XML title index')) )

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
            buf.write('<tr><td><tt><a href="%sRecentChanges">%s</a>&nbsp;&nbsp;</tt></td>' % (url, tag))
            buf.write('<td><tt><a href="%s">%s</a></tt></td>' % (url, url))
            buf.write('</tr>\n')
        buf.write('</table>')

        return self.formatter.rawHTML(buf.getvalue())


    def _macro_SystemInfo(self, args):
        from cStringIO import StringIO

        # check for 4XSLT
        try:
            import Ft
            ftversion = Ft.__version__
        except ImportError:
            ftversion = None
        except AttributeError:
            ftversion = 'N/A'

        buf = StringIO()
        row = lambda label, value, buf=buf: buf.write(
            '<tr><td valign="top" nowrap><b>%s</b></td><td>&nbsp;&nbsp;</td><td>%s</td></tr>' %
            (label, value))

        buf.write('<table border=0 cellspacing=2 cellpadding=0>')
        row(_('Python Version'), sys.version)
        row(_('MoinMoin Version'), _('Release %s [Revision %s]') % (version.release, version.revision))
        if ftversion:
            row(_('4Suite Version'), ftversion)
        row(_('Number of pages'), len(wikiutil.getPageList(config.text_dir)))
        row(_('Number of backup versions'), len(wikiutil.getBackupList(config.backup_dir, None)))
        row(_('Entries in edit log'), len(editlog.EditLog()))
        row(_('Global extension macros'), 
            string.join(macro.extension_macros, ', ') or _("<b>NONE</b>"))
        row(_('Local extension macros'), 
            string.join(plugin_macros, ', ') or _("<b>NONE</b>"))
        row(_('Global extension actions'), 
            string.join(action.extension_actions, ', ') or _("<b>NONE</b>"))
        row(_('Local extension actions'), 
            string.join(wikiaction.getPlugins()[1], ', ') or _("<b>NONE</b>"))
        buf.write('</table>')

        return self.formatter.rawHTML(buf.getvalue())


    def _macro_PageCount(self, args):
        return self.formatter.text("%d" % (len(wikiutil.getPageList(config.text_dir)),))


    def _macro_Icon(self, args):
        return self.formatter.image(border=0, hspace=2,
            src="%s/img/%s" % (config.url_prefix, args))


    def _macro_PageList(self, args):
        try:
            needle_re = re.compile(args, re.IGNORECASE)
        except re.error, e:
            return "<b>%s: %s</b>" % (
                _("ERROR in regex '%s'") % (args,), e)

        all_pages = wikiutil.getPageList(config.text_dir)
        hits = filter(needle_re.search, all_pages)
        hits.sort()

        result = self.formatter.bullet_list(1)
        for filename in hits:
            result = result + self.formatter.listitem(1)
            result = result + self.formatter.pagelink(filename)
            result = result + self.formatter.listitem(0)
        result = result + self.formatter.bullet_list(0)
        return result


    def __get_Date(self, args, format_date):
        if not args:
            tm = time.time()
        elif len(args) == 19 and args[4] == '-' and args[7] == '-' \
                and args[10] == 'T' and args[13] == ':' and args[16] == ':':
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
                    _("Bad timestamp '%s'") % (args,), e)
            tm = time.mktime(tm)
        else:
            try:
                tm = float(args)
            except ValueError, e:
                return "<b>%s: %s</b>" % (
                    _("Bad timestamp '%s'") % (args,), e)
        return format_date(tm)

    def _macro_Date(self, args):
        return self.__get_Date(args, user.current.getFormattedDate)

    def _macro_DateTime(self, args):
        return self.__get_Date(args, user.current.getFormattedDateTime)


    def _macro_UserPreferences(self, args):
        from MoinMoin import userform
        return self.formatter.rawHTML(userform.getUserForm(self.form))

    def _macro_Anchor(self, args):
        return self.formatter.anchordef(args or "anchor")

