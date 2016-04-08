# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Macro Package

    Copyright (c) 2000 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    The canonical interface to macros is their execute() function,
    which gets passed an instance of the Macro class. Such an instance
    has the four members parser, formatter, form and request.

    Using "form" directly is deprecated and should be replaced
    by "request.form".

    Besides the execute() function, macros can export additional
    functions to offer services to other macros or actions. A few
    actually do that, e.g. AttachFile.

    $Id: __init__.py,v 1.4 2003/11/09 21:01:04 thomaswaldmann Exp $
"""

from MoinMoin.util import pysupport

extension_macros = pysupport.getPackageModules(__file__)

