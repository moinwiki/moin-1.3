"""
    MoinMoin - Processor Package

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Processors need to define a process() function that gets
    passed the current formatter and a list of lines to be
    processed. A processor is allowed to manipulate that list,
    since it is destroyed after processing.

    The first line of the list is always the bang path, so
    you can place arguments there and parse them.

    $Id: __init__.py,v 1.2 2002/03/17 13:46:17 jhermann Exp $
"""

from MoinMoin.util import getPackageModules
processors = getPackageModules(__file__)
del getPackageModules

