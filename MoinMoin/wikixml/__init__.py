"""
    MoinMoin - Package Initialization

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Subpackage containing XML support code.

    $Id: __init__.py,v 1.2 2002/02/13 21:13:55 jhermann Exp $
"""

try:
    from xml.sax import saxutils
    ok = hasattr(saxutils, 'quoteattr') # check for correct patch level
except ImportError:
    ok = 0

