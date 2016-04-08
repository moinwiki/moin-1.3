# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Package Initialization

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Subpackage containing XML support code.

    $Id: __init__.py,v 1.3 2003/11/09 21:01:18 thomaswaldmann Exp $
"""

try:
    from xml.sax import saxutils
    ok = hasattr(saxutils, 'quoteattr') # check for correct patch level
except ImportError:
    ok = 0

