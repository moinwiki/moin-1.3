# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PageSize Macro

    Copyright (c) 2002 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: PageSize.py,v 1.7 2003/11/09 21:01:03 thomaswaldmann Exp $
"""

# Imports
import string
from MoinMoin import config, wikiutil


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
    result = macro.formatter.number_list(1)
    for size, page in sizes:
        result = (result + macro.formatter.listitem(1) +
            macro.formatter.code(1) + 
            string.replace("%6d" % size, " ", "&nbsp;") + " " +
            macro.formatter.code(0) + 
            macro.formatter.pagelink(page.page_name, generated=1) + 
            macro.formatter.listitem(0)
        )
    result = result + macro.formatter.number_list(0)

    return result

