"""
    MoinMoin - Interface to HTTP stuff

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.9 2002/02/13 21:13:55 jhermann Exp $
"""

# Imports
import os, sys

# Header set to force misbehaved proxies and browsers to keep their
# hands off a page
# Details: http://support.microsoft.com/support/kb/articles/Q234/0/67.ASP
nocache = [
    "Pragma: no-cache",
    "Cache-Control: no-cache",
    "Expires: -1",
]

# load the appropriate interface here
if os.environ.get('GATEWAY_INTERFACE') == 'CGI/1.1':
    from MoinMoin.webapi.cgiMoin import *
elif sys.modules.has_key('twisted.web.script'):
    from MoinMoin.webapi.twistedMoin import *
else:
    from MoinMoin.webapi.cliMoin import *

