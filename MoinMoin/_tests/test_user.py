# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.user Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin import user

class encodePasswordTestCase(unittest.TestCase):

    def runTest(self):
        self.failUnlessEqual(
            user.encodePassword("MoinMoin"), 
            "{SHA}X+lk6KR7JuJEH43YnmettCwICdU=")
