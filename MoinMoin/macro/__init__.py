"""
    MoinMoin - Macro Package

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    The canonical interface to macros is their execute() function,
    which gets passed an instance of the Macro class. Such an instance
    has the four members parser, formatter, form and request.

    Using "form" directly is deprecated and should be replaced
    by "request.form".

    Besides the execute() function, macros can export additional
    functions to offer services to other macros or actions. A few
    actually do that, e.g. AttachFile.

    $Id: __init__.py,v 1.2 2002/04/17 19:54:35 jhermann Exp $
"""

import MoinMoin.util

extension_macros = MoinMoin.util.getPackageModules(__file__)

