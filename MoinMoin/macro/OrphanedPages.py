# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - OrphanedPages Macro

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: OrphanedPages.py,v 1.12 2003/11/09 21:01:03 thomaswaldmann Exp $
"""

# Imports
from MoinMoin import config, user, wikiutil

_guard = 0


def execute(macro, args):
    _ = macro.request.getText

    # prevent recursive calls
    global _guard
    if _guard: return ''

    # delete all linked pages from a dict of all pages
    _guard = 1
    pages = wikiutil.getPageDict(config.text_dir)
    # we do not look at pages we have no read rights on - this avoids
    # having MoinEditorBackup showing up (except your very own one)
    for key in pages.keys():
        if not macro.request.user.may.read(pages[key].page_name) or \
           key.endswith('/MoinEditorBackup'):
            del pages[key]
    orphaned = {}
    orphaned.update(pages)
    for page in pages.values():
        links = page.getPageLinks(macro.request)
        for link in links:
            if orphaned.has_key(link):
                del orphaned[link]
    _guard = 0

    # check for the extreme case
    if not orphaned:
        return "<p><b>%s</b></p>" % _("No orphaned pages in this wiki.")

    # return a list of page links
    orphanednames = orphaned.keys()
    orphanednames.sort()
    result = macro.formatter.number_list(1)
    for name in orphanednames:
        if not name: continue
        result = result + macro.formatter.listitem(1)
        result = result + macro.formatter.pagelink(name, generated=1)
        result = result + macro.formatter.listitem(0)
    result = result + macro.formatter.number_list(0)

    return result

