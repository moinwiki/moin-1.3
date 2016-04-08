"""
    MoinMoin - WantedPages Macro

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: WantedPages.py,v 1.4 2001/03/28 23:03:43 jhermann Exp $
"""

# Imports
import cgi, string
from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page

_guard = 0


def execute(macro, args):
    # prevent recursive calls
    global _guard
    if _guard: return ''
    
    # build a dict of wanted pages
    _guard = 1
    wanted = {}
    pages = wikiutil.getPageDict(config.text_dir)
    for page in pages.values():
        links = page.getPageLinks()
        for link in links:
            if not pages.has_key(link):
                if wanted.has_key(link):
                    wanted[link][page.page_name] = 1
                else:
                    wanted[link] = {page.page_name: 1}
    _guard = 0

    # check for the extreme case
    if not wanted:
        return "<p><b>%s</b></p>" % user.current.text("No wanted pages in this wiki.")

    # return a list of page links
    wantednames = wanted.keys()
    wantednames.sort()
    result = macro.formatter.number_list(1)
    wherelink = lambda n, p=pages: p[n].link_to()
    for name in wantednames:
        if not name: continue
        result = result + macro.formatter.listitem(1)
        result = result + macro.formatter.pagelink(name)

        where = wanted[name].keys()
        where.sort()
        if macro.formatter.page.page_name in where:
            where.remove(macro.formatter.page.page_name)
        result = result + ": " + string.join(map(wherelink, where), ', ')

        result = result + macro.formatter.listitem(0)
    result = result + macro.formatter.number_list(0)

    return result

