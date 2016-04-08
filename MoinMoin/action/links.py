"""
    MoinMoin - "links" action

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Generate a link database like MeatBall:LinkDatabase.

    $Id: links.py,v 1.6 2002/04/24 19:36:54 jhermann Exp $
"""

import string, sys
from MoinMoin import config, wikiutil, webapi
from MoinMoin.i18n import _


def execute(pagename, request):
    form = request.form

    # get the MIME type
    if form.has_key('mimetype'):
        mimetype = form['mimetype'].value
    else:
        mimetype = "text/html"

    webapi.http_headers(request, ["Content-Type: " + mimetype])

    if mimetype == "text/html":
        wikiutil.send_title(_('Full Link List for "%s"') % config.sitename)
        print '<pre>'

    pages = wikiutil.getPageDict(config.text_dir)
    pagelist = pages.keys()
    pagelist.sort()

    for name in pagelist:
        if mimetype == "text/html":
            print pages[name].link_to(),
        else:
            _emit(name)
        for link in pages[name].getPageLinks(request):
            if mimetype == "text/html":
                if pages.has_key(link):
                    print pages[link].link_to(),
                else:
                    _emit(link)
            else:
                _emit(link)
        print

    if mimetype == "text/html":
        print '</pre>'
        wikiutil.send_footer(request, pagename, editable=0, showactions=0, form=form)
    else:
        sys.exit(0)

def _emit(pagename):
    """ Send pagename, encode it if it contains spaces
    """
    if string.find(pagename, ' ') >= 0:
        print wikiutil.quoteWikiname(pagename),
    else:
        print pagename,

