"""
    MoinMoin - RandomPage Macro

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: RandomPage.py,v 1.1 2000/11/25 16:41:24 jhermann Exp $
"""

# Imports
import whrandom
from MoinMoin import config, wikiutil


def execute(macro, args):
    # get number of wanted links        
    try:
        links = max(int(args), 1)
    except:
        links = 1

    # select the pages from the page list
    all_pages = wikiutil.getPageList(config.text_dir)
    pages = []
    while len(pages) < links and all_pages:
        page = whrandom.choice(all_pages)
        pages.append(page)
        all_pages.remove(page)

    # return a single page link
    if links == 1: return macro.formatter.pagelink(pages[0])

    # return a list of page links
    pages.sort()
    result = macro.formatter.bullet_list(1)
    for name in pages:
        result = result + macro.formatter.listitem(1)
        result = result + macro.formatter.pagelink(name)
        result = result + macro.formatter.listitem(0)
    result = result + macro.formatter.bullet_list(0)

    return result

