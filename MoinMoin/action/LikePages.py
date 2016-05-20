# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - LikePages action

    This action generates a list of pages that either start or end
    with the same word as the current pagename. If only one matching
    page is found, that page is displayed directly.

    @copyright: (c) 2001 by Richard Jones <richard@bizarsoftware.com.au>
    @copyright: (c) 2001 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re
from MoinMoin import config, wikiutil
from MoinMoin.Page import Page


def execute(pagename, request):
    _ = request.getText
    from MoinMoin.formatter.text_html import Formatter
    request.formatter = Formatter(request)
    start, end, matches = findMatches(pagename, request)

    # Error?
    if isinstance(matches, (str, unicode)):
        Page(request, pagename).send_page(request, msg=matches)
        return

    # No matches
    if not matches:
        Page(request, pagename).send_page(request,
            msg = _('No pages like "%s"!') % (pagename,))
        return

    # One match - display it
    if len(matches) == 1:
        Page(request, matches.keys()[0]).send_page(request,
            msg = _('Exactly one page like "%s" found, redirecting to page.') % (
            pagename,))
        return

    # more than one match, list 'em
    request.http_headers()

    # This action generate data using the user language
    request.setContentLanguage(request.lang)

    wikiutil.send_title(request, _('Pages like "%s"') % (pagename),
                        pagename=pagename)
        
    # Start content - IMPORTANT - witout content div, there is no
    # direction support!
    request.write(request.formatter.startContent("content"))

    showMatches(pagename, request, start, end, matches)

    # End content and send footer
    request.write(request.formatter.endContent())
    wikiutil.send_footer(request, pagename)


def findMatches(pagename, request,
        s_re=re.compile('([%s][%s]+)' % (config.chars_upper, config.chars_lower)),
        e_re=re.compile('([%s][%s]+)$' % (config.chars_upper, config.chars_lower))):
    """ Find like pages
    
    @rtype: tuple
    @return: start word, end word, matches dict
    """
    import difflib
    _ = request.getText

    # Get list of user readable pages, excluding current page
    pagelist = request.rootpage.getPageList()
    try:
        pagelist.remove(pagename)
    except ValueError:
        pass

    # Get pages that starts or ends with same word as this page

    # If we don't get resuslts with wiki words matching, fallback to
    # simple first word and last word, using spaces.
    words = pagename.split()
    match = s_re.match(pagename)
    if match:
        start = match.group(1)
    else:
       start = words[0] 
        
    match = e_re.search(pagename)
    if match:
        end = match.group(1)
    else:
        end = words[-1] 
    
    matches = {}
    subpage = pagename + '/'

    # find any matching pages
    for page in pagelist:
        if page.startswith(subpage):
            matches[page] = 4
        else:
            if page.startswith(start):
                matches[page] = 1
            if page.endswith(end):
                matches[page] = matches.get(page, 0) + 2

    # Get similar pages using difflib, using case insensitive matching

    lowerpages = [p.lower() for p in pagelist]
    similar = difflib.get_close_matches(pagename.lower(), lowerpages, 10)
    if similar:
        # Find the original name by looking up in pagelist
        for lower in similar:
            name = pagelist[lowerpages.index(lower)]
            # Add to matches
            if not matches.has_key(name):
                matches[name] = 8
            
    return start, end, matches

def showMatches(pagename, request, start, end, matches, show_count = True):
    keys = matches.keys()
    keys.sort()
    _showMatchGroup(request, matches, keys, 8, pagename, show_count)
    _showMatchGroup(request, matches, keys, 4, "%s/..." % pagename, show_count)
    _showMatchGroup(request, matches, keys, 3, "%s...%s" % (start, end), show_count)
    _showMatchGroup(request, matches, keys, 1, "%s..." % (start,), show_count)
    _showMatchGroup(request, matches, keys, 2, "...%s" % (end,), show_count)


def _showMatchGroup(request, matches, keys, match, title, show_count = True):
    _ = request.getText
    matchcount = matches.values().count(match)

    if matchcount:
        if show_count:
            request.write(request.formatter.paragraph(1))
            request.write(request.formatter.strong(1))
            request.write(_('%(matchcount)d %(matches)s for "%(title)s"') % {
                'matchcount': matchcount,
                'matches': ' ' + (_('match'), _('matches'))[matchcount != 1],
                'title': wikiutil.escape(title)})
            request.write(request.formatter.strong(0))
            request.write(request.formatter.paragraph(0))
        request.write(request.formatter.bullet_list(1))
        for key in keys:
            if matches[key] == match:
                page = Page(request, key)
                request.write(request.formatter.listitem(1))
                request.write(request.formatter.pagelink(1, page.page_name))
                request.write(request.formatter.text(page.page_name))
                request.write(request.formatter.pagelink(0))
                request.write(request.formatter.listitem(0))
        request.write(request.formatter.bullet_list(0))


