"""
    MoinMoin - LikePages action

    Copyright (c) 2001 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This action generates a list of pages that either start or end
    with the same word as the current pagename. If only one matching
    page is found, that page is displayed directly.

    $Id: LikePages.py,v 1.4 2001/03/30 21:06:52 jhermann Exp $
"""

import re
from MoinMoin import config, user, util, wikiutil, webapi
from MoinMoin.Page import Page


def execute(pagename, form,
        s_re=re.compile('([%s][%s]+)' % (config.upperletters, config.lowerletters)),
        e_re=re.compile('([%s][%s]+)$' % (config.upperletters, config.lowerletters))):

    # figure the start and end words
    match = s_re.match(pagename)
    start = match.group(1)
    s_len = len(start)
    match = e_re.search(pagename)
    end = match.group(1)
    e_len = len(end)

    # find any matching pages
    matches = {}
    for anypage in wikiutil.getPageList(config.text_dir):
        # skip current page
        if anypage == pagename:
            continue
        p_len = len(anypage)
        if p_len > s_len and anypage[:s_len] == start:
            matches[anypage] = 1
        if p_len > e_len and anypage[-e_len:] == end:
            matches[anypage] = matches.get(anypage, 0) + 2

    # no matches :(
    if not matches:
        return Page(pagename).send_page(form,
            msg='<strong>' + user.current.text('No pages match "%s"!') % (pagename,) + '</strong>')

    # one match - display it
    if len(matches) == 1:
        return Page(matches.keys()[0]).send_page(form,
            msg='<strong>' + user.current.text('Exactly one matching page for "%s" found!') % (pagename,) + '</strong>')

    # more than one match, list 'em
    webapi.http_headers()
    wikiutil.send_title(user.current.text('Multiple matches for "%s...%s"') % (start, end),  
        pagename=pagename)

    keys = matches.keys()
    keys.sort()
    showMatches(matches, keys, 3, "%s...%s" % (start, end))
    showMatches(matches, keys, 1, "%s..." % (start,))
    showMatches(matches, keys, 2, "...%s" % (end,))

    wikiutil.send_footer(pagename)


def showMatches(matches, keys, match, title):
    matchcount = matches.values().count(match)

    if matchcount:
        print '<b>' + user.current.text('%(matchcount)d %(matches)s for "%(title)s"') % {
            'matchcount': matchcount,
            'matches': (user.current.text(' match'), user.current.text(' matches'))[matchcount != 1],
            'title': title} + '</b>'
        print "<ul>"
        for key in keys:
            if matches[key] == match:
                page = Page(key)
                print '<li><a href="%s">%s</a>' % (
                    wikiutil.quoteWikiname(page.page_name),
                    page.split_title())
        print "</ul>"

