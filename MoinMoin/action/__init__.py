# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Extension Action Package

    Copyright (c) 2000 by Richard Jones <richard@bizarsoftware.com.au>
    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>  
    All rights reserved, see COPYING for details.

    $Id: __init__.py,v 1.7 2003/11/09 21:00:56 thomaswaldmann Exp $
"""

from MoinMoin import config
from MoinMoin.util import pysupport

# create a list of extension actions from the subpackage directory
extension_actions = pysupport.getPackageModules(__file__)

# remove actions excluded by the configuration
for action in config.excluded_actions:
    try:
        extension_actions.remove(action)
    except ValueError:
        pass

