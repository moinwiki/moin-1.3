"""
    MoinMoin - Interface to HTTP stuff

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.3 2001/05/04 22:00:16 jhermann Exp $
"""

# Imports
import os

# load the appropriate interface here
if os.environ.get('GATEWAY_INTERFACE') == 'CGI/1.1':
    from cgiMoin import *
else:
    raise NotImplementedError("Unsupported web interface")

# And later, via some if statements:
# from twistedMoin import *
# from webwareMoin import *
# ... etc.

