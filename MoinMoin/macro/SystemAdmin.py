# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - System Administration

    Copyright (c) 2001, 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Web interface to do MoinMoin system administration tasks.

    $Id: SystemAdmin.py,v 1.11 2003/11/09 21:01:04 thomaswaldmann Exp $
"""

from MoinMoin import wikiutil
from MoinMoin.util import pysupport
from MoinMoin.userform import do_user_browser
from MoinMoin.action.AttachFile import do_admin_browser


def execute(macro, args):
    _ = macro.request.getText

    # do not show system admin to not admin users
    # !!! add ACL stuff here - meanwhile do this ugly hack:
    try: 
        if not macro.request.user.may._admin():
            return ''
    except AttributeError: # we do not have _admin in SecurityPolicy, so we give up
        return ''

    result = []
    _MENU = {
        'attachments': (("File attachment browser"), do_admin_browser),
        'users': (("User account browser"), do_user_browser),
    }
    choice = macro.request.form.getvalue('sysadm', None)

    # !! unfinished!
    """
    result = wikiutil.link_tag("?action=export", _("Download XML export of this wiki"))
    if pysupport.isImportable('gzip'):
        result += " [%s]" % wikiutil.link_tag("?action=export&compression=gzip", "gzip")
    """

    # create menu
    menuitems = [(label, id) for id, (label, handler) in _MENU.items()]
    menuitems.sort()
    for label, id in menuitems:
        if id == choice:
            result.append(macro.formatter.strong(1))
            result.append(macro.formatter.text(label))
            result.append(macro.formatter.strong(0))
        else:
            result.append(wikiutil.link_tag("%s?sysadm=%s" % (
                macro.formatter.page.page_name, id), label))
        result.append('<br>')
    result.append('<br>')

    # add chosen content
    if _MENU.has_key(choice):
        result.append(_MENU[choice][1](macro.request))

    return macro.formatter.rawHTML(''.join(result))

