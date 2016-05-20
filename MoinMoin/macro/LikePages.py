# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create list of LikePages

    @copyright: 2004 by Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = []

from MoinMoin.action import LikePages

def execute(macro, args):
    start, end, matches = LikePages.findMatches(macro.formatter.page.page_name, macro.request)
    if matches and not isinstance(matches, type('')):
        if not isinstance(matches, type(u'')):
            import StringIO
            out = StringIO.StringIO()
            macro.request.redirect(out)
            LikePages.showMatches(macro.formatter.page.page_name, macro.request, start, end, matches, False)
            macro.request.redirect()
            return out.getvalue()
    return args
