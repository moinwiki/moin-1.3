# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.Page Tests

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test_Page.py,v 1.2 2003/11/09 21:00:53 thomaswaldmann Exp $
"""

import unittest
from MoinMoin import Page


class existsTestCase(unittest.TestCase):
    def runTest(self):
        pg = Page.Page('OnlyAnIdiotWouldCreateSuchaPage')
        self.failIf(pg.exists())

