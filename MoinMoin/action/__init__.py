"""
    MoinMoin - Extension Action Package

    Copyright (c) 2000 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>  
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.5 2002/04/16 21:03:34 jhermann Exp $
"""

from MoinMoin import config, util

# create a list of extension actions from the subpackage directory
extension_actions = util.getPackageModules(__file__)

# remove actions excluded by the configuration
for action in config.excluded_actions:
    try:
        extension_actions.remove(action)
    except ValueError:
        pass

