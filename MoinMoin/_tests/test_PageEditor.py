# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.PageEditor Tests

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test_PageEditor.py,v 1.3 2003/11/09 21:00:53 thomaswaldmann Exp $
"""

import unittest
from MoinMoin import PageEditor, _tests


class expand_variablesTestCase(unittest.TestCase):
    def runTest(self):
        pagename = 'OnlyAnIdiotWouldCreateSuchaPage'
        pg = PageEditor.PageEditor(pagename, _tests.request)
        self.failUnlessEqual(pg._expand_variables("@PAGE@"), pagename)
        self.failUnlessEqual(pg._expand_variables("em@PAGE@bedded"), "em%sbedded" % pagename)
        self.failUnlessEqual(pg._expand_variables("@NOVAR@"), "@NOVAR@")
        self.failUnlessEqual(pg._expand_variables("case@Page@sensitive"), "case@Page@sensitive")

