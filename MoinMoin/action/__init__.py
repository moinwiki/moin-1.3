"""
    MoinMoin - Extension Action Package

    Copyright (c) 2000 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>  
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.4 2002/02/13 21:13:52 jhermann Exp $
"""

from MoinMoin import config, util

extension_actions = util.getPackageModules(__file__)

for action in config.excluded_actions:
    try:
        extension_actions.remove(action)
    except ValueError:
        pass

