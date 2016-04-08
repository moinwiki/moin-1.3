# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WantedPages Macro

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: WantedPages.py,v 1.13 2003/11/09 21:01:04 thomaswaldmann Exp $
"""

# Imports
import string, urllib
from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page

_guard = 0


def execute(macro, args):
    _ = macro.request.getText

    # prevent recursive calls
    global _guard
    if _guard: return ''

    # build a dict of wanted pages
    _guard = 1
    wanted = {}
    pages = wikiutil.getPageDict(config.text_dir)
    for page in pages.values():
        if not macro.request.user.may.read(page.page_name):
            continue
        # Regular users won't get /MoinEditorBackup pages shown anyway, but
        # WikiAdmin(s)  would - because they have global read rights.
        # Further, pages wanted from editor backup pages are irrelevant.
        if page.page_name.endswith('/MoinEditorBackup'):
            continue
        links = page.getPageLinks(macro.request)
        for link in links:
            if not pages.has_key(link):
                if wanted.has_key(link):
                    wanted[link][page.page_name] = 1
                else:
                    wanted[link] = {page.page_name: 1}
    _guard = 0

    # check for the extreme case
    if not wanted:
        return "<p><b>%s</b></p>" % _("No wanted pages in this wiki.")

    # return a list of page links
    wantednames = wanted.keys()
    wantednames.sort()
    result = macro.formatter.number_list(1)
    for name in wantednames:
        if not name: continue
        result = result + macro.formatter.listitem(1)
        result = result + macro.formatter.pagelink(name, generated=1)

        wherelink = lambda n, w=name, p=pages: \
            p[n].link_to(querystr='action=highlight&value=%s' % urllib.quote_plus(w))
        where = wanted[name].keys()
        where.sort()
        if macro.formatter.page.page_name in where:
            where.remove(macro.formatter.page.page_name)
        result = result + ": " + string.join(map(wherelink, where), ', ')

        result = result + macro.formatter.listitem(0)
    result = result + macro.formatter.number_list(0)

    return result

