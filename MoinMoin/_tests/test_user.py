# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.user Tests

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test_user.py,v 1.2 2003/11/09 21:00:54 thomaswaldmann Exp $
"""

import unittest
from MoinMoin import user


class encodePasswordTestCase(unittest.TestCase):

    def runTest(self):
        self.failUnlessEqual(
            user.encodePassword("MoinMoin"), 
            "{SHA}X+lk6KR7JuJEH43YnmettCwICdU=")
