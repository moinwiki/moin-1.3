# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.PageEditor Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin._tests import request
from MoinMoin import PageEditor, _tests

class ExpandVarsTestCase(unittest.TestCase):
    """PageEditor: testing page editor"""   

    pagename = 'OnlyAnIdiotWouldCreateSuchaPage' 

    _tests = (
        # Variable,             Expanded
        ("@PAGE@",              pagename),
        ("em@PAGE@bedded",      "em%sbedded" % pagename),
        ("@NOVAR@",             "@NOVAR@"),
        ("case@Page@sensitive", "case@Page@sensitive"),
        )

    def setUp(self):
        self.pg = PageEditor.PageEditor(request, self.pagename)
        
    def testExpandVariables(self):
        """PageEditor: expanding variables"""
        for var, expected in self._tests:
            result = self.pg._expand_variables(var)
            self.assertEqual(result, expected,
                'Expected "%(expected)s" but got "%(result)s"' % locals())   
