# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Macro Implementation

    These macros are used by the parser/wiki.py module
    to implement complex and/or dynamic page content.

    The sub-package "MoinMoin.macro" contains external
    macros, you can place your extensions there.

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re, time
from MoinMoin import action, config, macro, util
from MoinMoin import wikiutil, wikiaction, i18n
from MoinMoin.Page import Page
from MoinMoin.util import pysupport

names = ["TitleSearch", "WordIndex", "TitleIndex",
         "GoTo", "InterWiki", "SystemInfo", "PageCount", "UserPreferences",
         # Macros with arguments
         "Icon", "PageList", "Date", "DateTime", "Anchor", "MailTo", "GetVal",
         "TemplateList",
]
names.extend(i18n.languages.keys())

#############################################################################
### Helpers
#############################################################################

def getNames(cfg):
    if hasattr(cfg, 'macro_names'):
        return cfg.macro_names
    else:
        lnames = names[:]
        lnames.extend(wikiutil.getPlugins('macro', cfg))
        return lnames

def _make_index_key(index_letters, additional_html=""):
    index_letters.sort()
    links = map(lambda ch:
                    '<a href="#%s">%s</a>' %
                    (wikiutil.quoteWikinameURL(ch), ch.replace('~', 'Others')),
                index_letters)
    return "<p>%s%s</p>" % (' | '.join(links), additional_html)


#############################################################################
### Macros - Handlers for [[macroname]] markup
#############################################################################

class Macro:
    """ Macro handler 
    
    There are three kinds of macros: 
     * Builtin Macros - implemented in this file and named _macro_[name]
     * Language Pseudo Macros - any lang the wiki knows can be use as
       macro and is implemented here by _m_lang() 
     * External macros - implemented in either MoinMoin.macro package, or
       in the specific wiki instance in the plugin/macro directory
    """

    Dependencies = {
        "TitleSearch" : ["namespace"],
        "Goto"        : [],
        "WordIndex"   : ["namespace"],
        "TitleIndex"  : ["namespace"],
        "InterWiki"   : ["pages"],  # if interwikimap is editable
        "SystemInfo"  : ["pages"],
        "PageCount"   : ["namespace"],
        "Icon"        : ["user"], # users have different themes and user prefs
        "PageList"    : ["namespace"],
        "Date"        : ["time"],
        "DateTime"    : ["time"],
        "UserPreferences" :["time"],
        "Anchor"      : [],
        "Mailto"      : ["user"],
        "GetVal"      : ["pages"],
        "TemplateList": ["namespace"],
        }

    # we need the lang macros to execute when html is generated,
    # to have correct dir and lang html attributes
    for lang in i18n.languages.keys():
        Dependencies[lang] = []
    

    def __init__(self, parser):
        self.parser = parser
        self.form = self.parser.form
        self.request = self.parser.request
        self.formatter = self.request.formatter
        self._ = self.request.getText
        self.cfg = self.request.cfg

    def execute(self, macro_name, args):
        macro = wikiutil.importPlugin(self.request.cfg, 'macro', macro_name)
        if macro:
            return macro(self, args)

        builtins = vars(self.__class__)
        # builtin macro
        if builtins.has_key('_macro_' + macro_name):
            return builtins['_macro_' + macro_name](self, args)

        # language pseudo macro
        if i18n.languages.has_key(macro_name):
            return self._m_lang(macro_name, args)

        raise ImportError("Cannot load macro %s" % macro_name)

    def _m_lang(self, lang_name, text):
        """ Set the current language for page content.
        
            Language macro are used in two ways:
             * [lang] - set the current language until next lang macro
             * [lang(text)] - insert text with specific lang inside page
        """
        if text:
            return (self.formatter.lang(1, lang_name) +
                    self.formatter.text(text) +
                    self.formatter.lang(0, lang_name))
        
        self.request.current_lang = lang_name
        return ''
  
    def get_dependencies(self, macro_name):
        if self.Dependencies.has_key(macro_name):
            return self.Dependencies[macro_name]
        result = wikiutil.importPlugin(self.request.cfg, 'macro', macro_name,
                                       'Dependencies')
        if result != None:
            return result
        else:
            return ["time"]

    def _macro_TitleSearch(self, args):
        return self._m_search("titlesearch")

    def _m_search(self, type):
        """ Make a search box

        Make both Title Search and Full Search boxes, according to type.

        @param type: search box type: 'titlesearch' or 'fullsearch'
        @rtype: unicode
        @return: search box html fragment
        """
        _ = self._
        if self.form.has_key('value'):
            default = wikiutil.escape(self.form["value"][0], quote=1)
        else:
            default = ''

        # Title search settings
        boxes = ''
        button = _("Search Titles")

        # Special code for fullsearch
        if type == "fullsearch":
            boxes = [
                u'<br>',
                u'<input type="checkbox" name="context" value="160" checked="checked">',
                _('Display context of search results'),
                u'<br>',
                u'<input type="checkbox" name="case" value="1">',
                _('Case-sensitive searching'),
                ]
            boxes = u'\n'.join(boxes)
            button = _("Search Text")
            
        # Format
        type = (type == "titlesearch")
        html = [
            u'<form method="get" action="">',
            u'<div>',
            u'<input type="hidden" name="action" value="fullsearch">',
            u'<input type="hidden" name="titlesearch" value="%i">' % type,
            u'<input type="text" name="value" size="30" value="%s">' % default,
            u'<input type="submit" value="%s">' % button,
            boxes,
            u'</div>',
            u'</form>',    
            ]
        html = u'\n'.join(html)
        return self.formatter.rawHTML(html)
    
    def _macro_GoTo(self, args):
        """ Make a goto box

        @param args: macro arguments
        @rtype: unicode
        @return: goto box html fragment
        """
        _ = self._
        html = [
            u'<form method="get" action="">',
            u'<div>',
            u'<input type="text" name="goto" size="30">',
            u'<input type="submit" value="%s">' % _("Go To Page"),
            u'</div>',
            u'</form>',
            ]
        html = u'\n'.join(html)
        return self.formatter.rawHTML(html)

    def _macro_WordIndex(self, args):
        s = ''
        # Get page list readable by current user
        pages = self.request.rootpage.getPageList()
        map = {}
        word_re = re.compile(u'[%s][%s]+' % (config.chars_upper, config.chars_lower), re.UNICODE)
        for name in pages:
            for word in word_re.findall(name):
                try:
                    if not map[word].count(name):
                        map[word].append(name)
                except KeyError:
                    map[word] = [name]

        all_words = map.keys()
        all_words.sort()
        index_letters = []
        last_letter = None
        html = []
        for word in all_words:
            letter = word[0]
            if letter != last_letter:
                #html.append(self.formatter.anchordef()) # XXX no text param available!
                html.append(u'<a name="%s">\n<h3>%s</h3>\n' % (wikiutil.quoteWikinameURL(letter), letter))
                last_letter = letter
            if letter not in index_letters:
                index_letters.append(letter)

            html.append(self.formatter.strong(1))
            html.append(word)
            html.append(self.formatter.strong(0))
            html.append(self.formatter.bullet_list(1))
            links = map[word]
            links.sort()
            last_page = None
            for name in links:
                if name == last_page: continue
                html.append(self.formatter.listitem(1))
                html.append(Page(self.request, name).link_to(self.request))
                html.append(self.formatter.listitem(0))
            html.append(self.formatter.bullet_list(0))
        return u'%s%s' % (_make_index_key(index_letters), u''.join(html))


    def _macro_TitleIndex(self, args):
        _ = self._
        html = []
        index_letters = []
        allpages = int(self.form.get('allpages', [0])[0]) != 0
        # Get page list readable by current user
        # Filter by isSystemPage if needed
        if allpages:
            # TODO: make this fast by caching full page list
            pages = self.request.rootpage.getPageList()
        else:
            def filter(name):
                return not wikiutil.isSystemPage(self.request, name)
            pages = self.request.rootpage.getPageList(filter=filter)

        # Sort ignoring case
        tmp = [(name.upper(), name) for name in pages]
        tmp.sort()
        pages = [item[1] for item in tmp]
                
        current_letter = None
        for name in pages:
            letter = name[0].upper()
            letter = wikiutil.getUnicodeIndexGroup(name)
            if letter not in index_letters:
                index_letters.append(letter)
            if letter != current_letter:
                html.append(u'<a name="%s"><h3>%s</h3></a>' % (
                    wikiutil.quoteWikinameURL(letter), letter.replace('~', 'Others')))
                current_letter = letter
            else:
                html.append(u'<br>')
            html.append(u'%s\n' % Page(self.request, name).link_to(self.request, attachment_indicator=1))

        # add rss link
        index = ''
        if 0: # if wikixml.ok: # XXX currently switched off (not implemented)
            from MoinMoin import wikixml
            index = (index + self.formatter.url(1, 
                wikiutil.quoteWikinameURL(self.formatter.page.page_name) + "?action=rss_ti", unescaped=1) +
                     self.formatter.icon("rss") +
                     self.formatter.url(0))

        qpagename = wikiutil.quoteWikinameURL(self.formatter.page.page_name)
        index = index + _make_index_key(index_letters, u"""<br>
<a href="%s?allpages=%d">%s</a>&nbsp;|
<a href="%s?action=titleindex">%s</a>&nbsp;|
<a href="%s?action=titleindex&amp;mimetype=text/xml">%s</a>
""" % (qpagename, not allpages, (_('Include system pages'), _('Exclude system pages'))[allpages],
       qpagename, _('Plain title index'),
       qpagename, _('XML title index')) )

        return u'%s%s' % (index, u''.join(html)) 


    def _macro_InterWiki(self, args):
        from StringIO import StringIO

        # load interwiki list
        dummy = wikiutil.resolve_wiki(self.request, '')

        buf = StringIO()
        buf.write('<dl>')
        list = self.cfg._interwiki_list.items() # this is where we cached it
        list.sort()
        for tag, url in list:
            buf.write('<dt><tt><a href="%s">%s</a></tt></dt>' % (
                wikiutil.join_wiki(url, 'RecentChanges'), tag))
            if url.find('$PAGE') == -1:
                buf.write('<dd><tt><a href="%s">%s</a></tt></dd>' % (url, url))
            else:
                buf.write('<dd><tt>%s</tt></dd>' % url)
        buf.write('</dl>')

        return self.formatter.rawHTML(buf.getvalue())


    def _macro_SystemInfo(self, args):
        import operator, sys
        from StringIO import StringIO
        from MoinMoin import parser, processor, version
        from MoinMoin.logfile import editlog, eventlog
        _ = self._
        # check for 4XSLT
        try:
            import Ft
            ftversion = Ft.__version__
        except ImportError:
            ftversion = None
        except AttributeError:
            ftversion = 'N/A'

        # Get the full pagelist in the wiki
        pagelist = self.request.rootpage.getPageList(user='')
        totalsize = reduce(operator.add, [Page(self.request, name).size()
                                          for name in pagelist])

        buf = StringIO()
        row = lambda label, value, buf=buf: buf.write(
            u'<dt>%s</dt><dd>%s</dd>' %
            (label, value))

        buf.write(u'<dl>')
        row(_('Python Version'), sys.version)
        row(_('MoinMoin Version'), _('Release %s [Revision %s]') % (version.release, version.revision))
        if ftversion:
            row(_('4Suite Version'), ftversion)
        row(_('Number of pages'), str(len(pagelist)))
        systemPages = [page for page in pagelist
                       if wikiutil.isSystemPage(self.request, page)]
        row(_('Number of system pages'), str(len(systemPages)))
        row(_('Accumulated page sizes'), str(totalsize))

        edlog = editlog.EditLog(self.request)
        row(_('Entries in edit log'),
            _("%(logcount)s (%(logsize)s bytes)") %
            {'logcount': edlog.lines(), 'logsize': edlog.size()})

        # !!! This puts a heavy load on the server when the log is large,
        # and it can appear on normal pages ==> so disable it for now.
        eventlogger = eventlog.EventLog(self.request)
        nonestr = _("NONE")
        row('Event log',
            "%s bytes" % eventlogger.size())
        row(_('Global extension macros'), 
            ', '.join(macro.extension_macros) or nonestr)
        row(_('Local extension macros'), 
            ', '.join(wikiutil.wikiPlugins('macro', self.cfg)) or nonestr)
        ext_actions = []
        for a in action.extension_actions:
            if not a in self.request.cfg.excluded_actions:
                ext_actions.append(a)
        row(_('Global extension actions'), 
            ', '.join(ext_actions) or nonestr)
        row(_('Local extension actions'), 
            ', '.join(wikiaction.getPlugins(self.request)[1]) or nonestr)
        row(_('Installed parsers'), 
            ', '.join(parser.modules) or nonestr)
        row(_('Installed processors (DEPRECATED -- use Parsers instead)'), 
            ', '.join(processor.processors) or nonestr)
        state = (_('Disabled'), _('Enabled'))
        row(_('Lupy search'), state[self.request.cfg.lupy_search])
        buf.write(u'</dl')

        return self.formatter.rawHTML(buf.getvalue())

    def _macro_PageCount(self, args):
        """ Return number of pages readable by current user
        
        Return either an exact count (slow!) or fast count including
        deleted pages.
        """
        # Check input
        options = {None: 0, '': 0, 'exists': 1}
        try:
            exists = options[args]
        except KeyError:
            # Wrong argument, return inline error message
            arg = self.formatter.text(args)
            return '<span class="error">Wrong argument: %s</span>' % arg
        
        count = self.request.rootpage.getPageCount(exists=exists)
        return self.formatter.text("%d" % count)

    def _macro_Icon(self, args):
        icon = args.lower()
        return self.formatter.icon(icon)

    def _macro_PageList(self, needle):
        from MoinMoin import search
        _ = self._
        literal=0
        case=0

        # If called with empty or no argument, default to regex search for .+,
        # the full page list.
        if not needle:
            needle = 'regex:.+'

        # With whitespace argument, return same error message as FullSearch
        elif needle.isspace():
            err = _('Please use a more selective search term instead of '
                    '{{{"%s"}}}') %  needle
            return '<span class="error">%s</span>' % err
            
        # Return a title search for needle, sorted by name.
        query = search.QueryParser(literal=literal, titlesearch=1,
                                   case=case).parse_query(needle)
        results = search.searchPages(self.request, query)
        results.sortByPagename()
        return results.pageList(self.request, self.formatter)
        
    def _macro_TemplateList(self, args):
        _ = self._
        try:
            needle_re = re.compile(args or '', re.IGNORECASE)
        except re.error, e:
            return "<strong>%s: %s</strong>" % (
                _("ERROR in regex '%s'") % (args,), e)

        # Get page list readable by current user, filtered by needle
        hits = self.request.rootpage.getPageList(filter=needle_re.search)
        hits.sort()
        
        result = []
        result.append(self.formatter.bullet_list(1))
        for pagename in hits:
            result.append(self.formatter.listitem(1))
            result.append(self.formatter.pagelink(1, pagename, generated=1))
            result.append(self.formatter.text(pagename))
            result.append(self.formatter.pagelink(0, pagename))
            result.append(self.formatter.listitem(0))
        result.append(self.formatter.bullet_list(0))
        return ''.join(result)


    def __get_Date(self, args, format_date):
        _ = self._
        if not args:
            tm = time.time() # always UTC
        elif len(args) >= 19 and args[4] == '-' and args[7] == '-' \
                and args[10] == 'T' and args[13] == ':' and args[16] == ':':
            # we ignore any time zone offsets here, assume UTC,
            # and accept (and ignore) any trailing stuff
            try:
                year, month, day = int(args[0:4]), int(args[5:7]), int(args[8:10]) 
                hour, minute, second = int(args[11:13]), int(args[14:16]), int(args[17:19]) 
                tz = args[19:] # +HHMM, -HHMM or Z or nothing (then we assume Z)
                tzoffset = 0 # we assume UTC no matter if there is a Z
                if tz:
                    sign = tz[0]
                    if sign in '+-':
                        tzh, tzm = int(tz[1:3]), int(tz[3:])
                        tzoffset = (tzh*60+tzm)*60
                        if sign == '-':
                            tzoffset = -tzoffset
                tm = (year, month, day, hour, minute, second, 0, 0, 0)
            except ValueError, e:
                return "<strong>%s: %s</strong>" % (
                    _("Bad timestamp '%s'") % (args,), e)
            # as mktime wants a localtime argument (but we only have UTC),
            # we adjust by our local timezone's offset
            try:
                tm = time.mktime(tm) - time.timezone - tzoffset
            except (OverflowError, ValueError), err:
                tm = 0 # incorrect, but we avoid an ugly backtrace
        else:
            # try raw seconds since epoch in UTC
            try:
                tm = float(args)
            except ValueError, e:
                return "<strong>%s: %s</strong>" % (
                    _("Bad timestamp '%s'") % (args,), e)
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
            icon = util.web.getLinkIcon(self.request, self.formatter, "mailto")
            result = (self.formatter.url(1, 'mailto:' + email, 'external', pretty_url=1, unescaped=1) +
                      icon +
                      self.formatter.text(text or email) +
                      self.formatter.url(0))
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


    def _macro_GetVal(self, args):
        page,key = args.split(',')
        d = self.request.dicts.dict(page)
        result = d.get(key,'')
        return self.formatter.text(result)

