# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikiutil Tests

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test_wikiutil.py,v 1.4 2003/11/09 21:00:54 thomaswaldmann Exp $
"""

import unittest
from MoinMoin import wikiutil


# test works only for default config
class isTemplatePageTestCase(unittest.TestCase):
    GOOD = [
        'aTemplate',
        'MyTemplate',
    ]
    BAD = [
        'Template',
        'ATemplate',
        'TemplateInFront',
        'xTemplateInFront',
        'XTemplateInFront',
    ]

    def runTest(self):
        for name in self.GOOD:
            self.failUnless(wikiutil.isTemplatePage(name))
        for name in self.BAD:
            self.failIf(wikiutil.isTemplatePage(name))


# test works only for default config
class isFormPageTestCase(unittest.TestCase):
    GOOD = [
        'aForm',
        'MyForm',
    ]
    BAD = [
        'Form',
        'AForm',
        'FormInFront',
        'xFormInFront',
        'XFormInFront',
    ]

    def runTest(self):
        for name in self.GOOD:
            self.failUnless(wikiutil.isFormPage(name))
        for name in self.BAD:
            self.failIf(wikiutil.isFormPage(name))

