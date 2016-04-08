# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - LikePages action

    Copyright (c) 2001 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This action generates a list of pages that either start or end
    with the same word as the current pagename. If only one matching
    page is found, that page is displayed directly.

    $Id: LikePages.py,v 1.22 2003/11/09 21:00:55 thomaswaldmann Exp $
"""

import re, cgi
from MoinMoin import config, user, util, wikiutil, webapi
from MoinMoin.Page import Page


def execute(pagename, request):
    _ = request.getText
    start, end, matches = findMatches(pagename, request)

    # error?
    if isinstance(matches, type('')):
        Page(pagename).send_page(request, msg=matches)
        return

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
    wikiutil.send_title(request, _('Multiple matches for "%s...%s"') % (start, end),
        pagename=pagename)

    showMatches(pagename, request, start, end, matches)

    wikiutil.send_footer(request, pagename)


def findMatches(pagename, request,
        s_re=re.compile('([%s][%s]+)' % (config.upperletters, config.lowerletters)),
        e_re=re.compile('([%s][%s]+)$' % (config.upperletters, config.lowerletters))):
    from MoinMoin.support import difflib
    _ = request.getText

    # get page lists
    pagelist = wikiutil.getPageList(config.text_dir)
    lowerpages = [p.lower() for p in pagelist]
    similar = difflib.get_close_matches(pagename.lower(), lowerpages, 10) 

    # figure the start and end words
    s_match = s_re.match(pagename)
    e_match = e_re.search(pagename)
    if not (s_match and e_match or similar):
        return None, None, _('<b>You cannot use LikePages on an extended pagename!</b>')

    start = None
    end = None
    matches = {}
    if s_match and e_match:
        # extract the words
        start = s_match.group(1)
        end = e_match.group(1)
        subpage = pagename + '/'

        # find any matching pages
        for anypage in pagelist:
            # skip current page
            if anypage == pagename:
                continue
            if anypage.startswith(subpage):
                matches[anypage] = 4
            else:
                if anypage.startswith(start):
                    matches[anypage] = 1
                if anypage.endswith(end):
                    matches[anypage] = matches.get(anypage, 0) + 2

    if similar:
        pagemap = {}
        for anypage in pagelist:
            pagemap[anypage.lower()] = anypage

        for anypage in similar:
            if pagemap[anypage] == pagename:
                continue
            matches[pagemap[anypage]] = 8

    # CNC:2003-05-30
    for pagename in matches.keys():
        if not request.user.may.read(pagename):
            del matches[pagename]

    return start, end, matches


def showMatches(pagename, request, start, end, matches):
    keys = matches.keys()
    keys.sort()
    _showMatchGroup(request, matches, keys, 8, pagename)
    _showMatchGroup(request, matches, keys, 4, "%s/..." % pagename)
    _showMatchGroup(request, matches, keys, 3, "%s...%s" % (start, end))
    _showMatchGroup(request, matches, keys, 1, "%s..." % (start,))
    _showMatchGroup(request, matches, keys, 2, "...%s" % (end,))


def _showMatchGroup(request, matches, keys, match, title):
    _ = request.getText
    matchcount = matches.values().count(match)

    if matchcount:
        print '<b>' + _('%(matchcount)d %(matches)s for "%(title)s"') % {
            'matchcount': matchcount,
            'matches': (_(' match'), _(' matches'))[matchcount != 1],
            'title': cgi.escape(title)} + '</b>'
        print "<ul>"
        for key in keys:
            if matches[key] == match:
                page = Page(key)
                print '<li><a href="%s/%s">%s</a>' % (
                    webapi.getScriptname(),
                    wikiutil.quoteWikiname(page.page_name),
                    page.split_title())
        print "</ul>"

