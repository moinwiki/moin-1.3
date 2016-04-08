# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PageSize Macro

    @copyright: 2002 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
from MoinMoin import config, wikiutil

Dependencies = ["pages"]

def execute(macro, args):
    # get list of pages and their objects
    pages = wikiutil.getPageDict(config.text_dir)

    # get sizes and sort them
    sizes = []
    for name, page in pages.items():
        if macro.request.user.may.read(name):
            sizes.append((page.size(), page))
    sizes.sort()
    sizes.reverse()

    # format list
    result = []
    result.append(macro.formatter.number_list(1))
    for size, page in sizes:
        result.append(macro.formatter.listitem(1))
        result.append(macro.formatter.code(1))
        result.append(("%6d" % size).replace(" ", "&nbsp;") + " ")
        result.append(macro.formatter.code(0))
        result.append(macro.formatter.pagelink(page.page_name, generated=1))
        result.append(macro.formatter.listitem(0))
    result.append(macro.formatter.number_list(0))

    return ''.join(result)

