# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create an action link

    @copyright: 2004 by Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

def execute(macro, args):
    items = args.split(',', 2)
    if len(items) < 2:
        text = items[0]
    else:
        text = items[1]
    action = items[0]
    from MoinMoin import wikiutil
    return wikiutil.link_tag(
        macro.request, macro.formatter.page.page_name + "?action=" + action,
        text
    )

