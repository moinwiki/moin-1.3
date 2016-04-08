# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.PageEditor Tests

    @copyright: 2003-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
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

