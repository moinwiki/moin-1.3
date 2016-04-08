# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Processor Package

    Processors need to define a process() function that gets
    passed the current formatter and a list of lines to be
    processed. A processor is allowed to manipulate that list,
    since it is destroyed after processing.

    The first line of the list is always the bang path, so
    you can place arguments there and parse them.

    @copyright: 2002 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

processors = pysupport.getPackageModules(__file__)
modules = processors
