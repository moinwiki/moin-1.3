"""
    MoinMoin - "titleindex" action

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This action generates a plain list of pages, so that other wikis
    can implement http://www.usemod.com/cgi-bin/mb.pl?MetaWiki more
    easily.

    $Id: titleindex.py,v 1.3 2001/03/15 22:20:25 jhermann Exp $
"""

import sys
from MoinMoin import config, util, wikiutil, webapi


def execute(pagename, form):
    # get the MIME type
    if form.has_key('mimetype'):
        mimetype = form['mimetype'].value
    else:
        mimetype = "text/plain"

    webapi.http_headers(["Content-Type: " + mimetype])
    print

    pages = list(wikiutil.getPageList(config.text_dir))
    pages.sort()

    if mimetype == "text/xml":
        print '<?xml version="1.0" encoding="%s"?>' % (config.charset,)
        print '<TitleIndex>'
        for name in pages:
            print '  <Title>%s</Title>' % (util.TranslateCDATA(name),)
        print '</TitleIndex>'
    else:
        for name in pages:
            print name

    sys.exit(0)

