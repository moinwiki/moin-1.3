# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RandomQuote Macro

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.
    Originally written by Thomas Waldmann.
    Gustavo Niemeyer added wiki markup parsing of the quotes.
    
    Selects a random quote from FortuneCookies or a given page.

    Usage:
        [[RandomQuote()]]
        [[RandomQuote(WikiTips)]]
    
    Comments:
        It will look for list delimiters on the page in question.
        It will ignore anything that is not in an "*" list.

    $Id: RandomQuote.py,v 1.6 2003/11/09 21:01:03 thomaswaldmann Exp $
"""

import random, sys, cStringIO
from MoinMoin.Page import Page

def execute(macro, args):
    _ = macro.request.getText

    pagename = args or 'FortuneCookies'
    raw = Page(pagename).get_raw_body()
    if not macro.request.user.may.read(pagename):
        raw = ""

    # this selects lines looking like a list item
    # !!! TODO: make multi-line quotes possible (optionally split by "----" or something)
    quotes = raw.splitlines()
    quotes = [quote.strip() for quote in quotes]
    quotes = [quote[2:] for quote in quotes if quote.startswith('* ')]
    
    quote = random.choice(quotes or [
        macro.formatter.highlight(1) +
        _('No quotes on %(pagename)s.') % locals() +
        macro.formatter.highlight(0)
        ])

    page = Page(pagename)
    page.set_raw_body(quote)
    out = cStringIO.StringIO()
    backup = sys.stdout, macro.request.write
    sys.stdout, macro.request.write = out, out.write
    page.send_page(macro.request, content_only=1)
    sys.stdout, macro.request.write = backup
    quote = out.getvalue()

    return quote

