# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Interface to HTTP stuff

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.10 2003/11/09 21:01:15 thomaswaldmann Exp $
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

