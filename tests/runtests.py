# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Run Unit tests

    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os, sys

moinpath = os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), os.pardir)))
sys.path.insert(0, moinpath)

from MoinMoin import _tests
_tests.run()

