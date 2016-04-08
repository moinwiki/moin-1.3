"""
    MoinMoin - OrphanedPages Macro

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: OrphanedPages.py,v 1.3 2001/05/31 01:02:08 jhermann Exp $
"""

# Imports
from MoinMoin import config, user, wikiutil

_guard = 0


def execute(macro, args):
    # prevent recursive calls
    global _guard
    if _guard: return ''

    # delete all linked pages from a dict of all pages
    _guard = 1
    pages = wikiutil.getPageDict(config.text_dir)
    orphaned = {}
    orphaned.update(pages)
    for page in pages.values():
        links = page.getPageLinks()
        for link in links:
            if orphaned.has_key(link):
                del orphaned[link]
    _guard = 0

    # check for the extreme case
    if not orphaned:
        return "<p><b>%s</b></p>" % user.current.text("No orphaned pages in this wiki.")

    # return a list of page links
    orphanednames = orphaned.keys()
    orphanednames.sort()
    result = macro.formatter.number_list(1)
    for name in orphanednames:
        if not name: continue
        result = result + macro.formatter.listitem(1)
        result = result + macro.formatter.pagelink(name)
        result = result + macro.formatter.listitem(0)
    result = result + macro.formatter.number_list(0)

    return result

