"""
    MoinMoin - System Administration

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Web interface to do MoinMoin system administration tasks.

    $Id: SystemAdmin.py,v 1.3 2001/12/01 20:30:10 jhermann Exp $
"""

from MoinMoin import config, util, wikiutil
from MoinMoin.i18n import _


def execute(macro, args):
    print wikiutil.link_tag("?action=export", _("Download XML export of this wiki"))
    if util.isImportable('gzip'):
        print " [%s]" % wikiutil.link_tag("?action=export&compression=gzip", "gzip")

    return ""
