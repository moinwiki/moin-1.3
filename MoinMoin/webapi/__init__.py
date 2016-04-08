"""
    MoinMoin - Interface to HTTP stuff

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.5 2001/10/23 22:04:49 jhermann Exp $
"""

# Imports
import os, sys

# load the appropriate interface here
if os.environ.get('GATEWAY_INTERFACE') == 'CGI/1.1':
    from cgiMoin import *
elif sys.modules.has_key('twisted.web.script'):
    from MoinMoin.webapi.twistedMoin import *
else:
    pass
    #raise NotImplementedError("Unsupported web interface")

# And later, via some if statements:
# from webwareMoin import *
# ... etc.

