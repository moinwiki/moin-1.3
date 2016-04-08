"""
    MoinMoin - Extension Action Package

    Copyright (c) 2000 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>  
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.2 2001/01/04 07:30:42 jhermann Exp $
"""

import MoinMoin.util

extension_actions = MoinMoin.util.getPackageModules(__file__)

