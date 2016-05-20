# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RandomPage Macro

    @copyright: 2000 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import random

Dependencies = ["time"]

def execute(macro, args):
    # get number of wanted links        
    try:
        links = max(int(args), 1)
    except StandardError:
        links = 1

    # select the pages from the page list
    all_pages = macro.request.rootpage.getPageList()
    pages = []
    while len(pages) < links and all_pages:
        page = random.choice(all_pages)
        if macro.request.user.may.read(page):
            pages.append(page)
        all_pages.remove(page)

    if not pages:
        return ''

    # return a single page link
    if links == 1: return (macro.formatter.pagelink(1, pages[0], generated=1) +
                           macro.formatter.text(pages[0]) +
                           macro.formatter.pagelink(0))

    # return a list of page links
    pages.sort()
    result = macro.formatter.bullet_list(1)
    for name in pages:
        result = result + macro.formatter.listitem(1)
        result = result + macro.formatter.pagelink(1, name, generated=1)
        result = result + macro.formatter.text(name)
        result = result + macro.formatter.pagelink(0)
        result = result + macro.formatter.listitem(0)
    result = result + macro.formatter.bullet_list(0)

    return result

