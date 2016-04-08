"""
    MoinMoin - LikePages action

    Copyright (c) 2001 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This action generates a list of pages that either start or end
    with the same word as the current pagename. If only one matching
    page is found, that page is displayed directly.

    $Id: LikePages.py,v 1.14 2002/04/24 19:36:54 jhermann Exp $
"""

import re
from MoinMoin import config, user, util, wikiutil, webapi
from MoinMoin.Page import Page
from MoinMoin.i18n import _


def execute(pagename, request,
        s_re=re.compile('([%s][%s]+)' % (config.upperletters, config.lowerletters)),
        e_re=re.compile('([%s][%s]+)$' % (config.upperletters, config.lowerletters))):

    # figure the start and end words
    s_match = s_re.match(pagename)
    e_match = e_re.search(pagename)
    if not (s_match and e_match):
        Page(pagename).send_page(request,
            msg=_('<b>You cannot use LikePages on an extended pagename!</b>'))
        return

    # extract the words
    start = s_match.group(1)
    s_len = len(start)
    end = e_match.group(1)
    e_len = len(end)
    subpage = pagename + '/'
    sp_len = len(subpage)

    # find any matching pages
    matches = {}
    for anypage in wikiutil.getPageList(config.text_dir):
        # skip current page
        if anypage == pagename:
            continue
        p_len = len(anypage)
        if p_len > sp_len and anypage[:sp_len] == subpage:
            matches[anypage] = 4
        else:
            if p_len > s_len and anypage[:s_len] == start:
                matches[anypage] = 1
            if p_len > e_len and anypage[-e_len:] == end:
                matches[anypage] = matches.get(anypage, 0) + 2

    # no matches :(
    if not matches:
        Page(pagename).send_page(request,
            msg='<strong>' + _('No pages match "%s"!') % (pagename,) + '</strong>')
        return

    # one match - display it
    if len(matches) == 1:
        Page(matches.keys()[0]).send_page(request,
            msg='<strong>' + _('Exactly one matching page for "%s" found!') % (pagename,) + '</strong>')
        return

    # more than one match, list 'em
    webapi.http_headers(request)
    wikiutil.send_title(_('Multiple matches for "%s...%s"') % (start, end),
        pagename=pagename)

    keys = matches.keys()
    keys.sort()
    showMatches(matches, keys, 4, "%s/..." % pagename)
    showMatches(matches, keys, 3, "%s...%s" % (start, end))
    showMatches(matches, keys, 1, "%s..." % (start,))
    showMatches(matches, keys, 2, "...%s" % (end,))

    wikiutil.send_footer(request, pagename)


def showMatches(matches, keys, match, title):
    matchcount = matches.values().count(match)

    if matchcount:
        print '<b>' + _('%(matchcount)d %(matches)s for "%(title)s"') % {
            'matchcount': matchcount,
            'matches': (_(' match'), _(' matches'))[matchcount != 1],
            'title': title} + '</b>'
        print "<ul>"
        for key in keys:
            if matches[key] == match:
                page = Page(key)
                print '<li><a href="%s">%s</a>' % (
                    wikiutil.quoteWikiname(page.page_name),
                    page.split_title())
        print "</ul>"

