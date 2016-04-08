"""
    MoinMoin - Macro Implementation

    These macros are used by the parser/wiki.py module
    to implement complex and/or dynamic page content.

    The sub-package "MoinMoin.macro" contains external
    macros, you can place your extensions there.

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: wikimacro.py,v 1.3 2000/12/06 10:48:50 jhermann Exp $
"""

# Imports
import re, string, sys, time
from MoinMoin import config, util, version, wikiutil, macro
from MoinMoin.Page import Page


#############################################################################
### Globals
#############################################################################

names = ["TitleSearch", "FullSearch", "WordIndex", "TitleIndex",
         "GoTo", "InterWiki", "SystemInfo", "PageCount", "UserPreferences",
         # Macros with arguments
         "Icon", "PageList"]

# external macros
names.extend(macro.extension_macros)


#############################################################################
### Helpers
#############################################################################

def _make_index_key(index_letters):
    index_letters.sort()
    s = '<p><center>'
    links = map(lambda ch:
                    '<a href="#%s">%s</a>' %
                    (wikiutil.quoteWikiname(ch), string.replace(ch, '~', 'Others')),
                index_letters)
    s = s + string.join(links, ' | ')
    s = s + '</center><p>'
    return s


#############################################################################
### Macros - Handlers for [[macroname]] markup
#############################################################################

class Macro:
    def __init__(self, parser):
        self.parser = parser
        self.formatter = self.parser.formatter
        self.form = self.parser.form

    def execute(self, macro_name, args):
        builtins = vars(self.__class__)
        if builtins.has_key('_macro_' + macro_name):
            return apply(builtins['_macro_' + macro_name], (self, args))

        # load extension macro
        execute = util.importName("MoinMoin.macro." + macro_name, "execute")
        return apply(execute, (self, args))
    
    def _macro_TitleSearch(self, args):
        return self._m_search("titlesearch")
    
    def _macro_FullSearch(self, args):
        return self._m_search("fullsearch")
    
    def _m_search(self, type):
        if self.form.has_key('value'):
            default = self.form["value"].value
        else:
            default = ''
        return """<form method="get">
        <input type="hidden" name="action" value="%s"> 
        <input name="value" size="30" value="%s"> 
        <input type="submit" value="Go">
        </form>""" % (type, default)
    
    def _macro_GoTo(self, args):
        return """<form method="get"><input name="goto" size="30">
        <input type="submit" value="Go">
        </form>"""
    
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
        index_letters = []
        s = ''
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
        return _make_index_key(index_letters) + s
    
    
    def _macro_InterWiki(self, args):
        from cStringIO import StringIO
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
    
        return buf.getvalue()
    
    
    def _macro_SystemInfo(self, args):
        from cStringIO import StringIO
    
        row = '<tr><td><b>%s</b></td><td>&nbsp;&nbsp;</td><td>%s</td></tr>'
        buf = StringIO()
        buf.write('<table border=0 cellspacing=2 cellpadding=0>')
        buf.write(row % ('Python Version', sys.version))
        buf.write(row % ('MoinMoin Version', 'Release %s [Revision %s]' % (version.release, version.revision)))
        buf.write(row % ('Number of pages', len(wikiutil.getPageList(config.text_dir))))
        buf.write('</table>')
    
        return buf.getvalue()
    
    
    def _macro_PageCount(self, args):
        return self.formatter.text("%d" % (len(wikiutil.getPageList(config.text_dir)),))
    
    
    def _macro_Icon(self, args):
        return '<img src="%s/img/%s" border="0" hspace="2">' % (config.url_prefix, args)
    
    
    def _macro_PageList(self, args):
        needle_re = re.compile(args, re.IGNORECASE)
        all_pages = wikiutil.getPageList(config.text_dir)
        hits = filter(needle_re.search, all_pages)
    
        result = self.formatter.bullet_list(1)
        for filename in hits:
            result = result + self.formatter.listitem(1)
            result = result + self.formatter.pagelink(filename)
            result = result + self.formatter.listitem(0)
        result = result + self.formatter.bullet_list(0)
        return result


    def _macro_UserPreferences(self, args):
        from MoinMoin import user
        return user.getUserForm(self.form)
    
