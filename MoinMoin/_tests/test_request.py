# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.module_tested Tests

    Module names must start with 'test_' to be included in the tests.

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin._tests import request, TestConfig
from MoinMoin import config

class NormalizePagenameTestCase(unittest.TestCase):
            
    def testPageInvalidChars(self):
        """ request: normalize pagename: remove invalid unicode chars

        Assume the default setting
        """
        test  = u'\u0000\u202a\u202b\u202c\u202d\u202e'
        expected = u''
        result = request.normalizePagename(test)
        self.assertEqual(result, expected,
                         ('Expected "%(expected)s" but got "%(result)s"') % locals())

    def testNormalizeSlashes(self):
        """ request: normalize pagename: normalize slashes """
        cases  = (
            (u'/////', u''),
            (u'/a', u'a'),
            (u'a/', u'a'),
            (u'a/////b/////c', u'a/b/c'),
            (u'a b/////c d/////e f', u'a b/c d/e f'),
            )
        for test, expected in cases:
            result = request.normalizePagename(test)
            self.assertEqual(result, expected,
                             ('Expected "%(expected)s" but got "%(result)s"') %
                             locals())

    def testNormalizeWhitespace(self):
        """ request: normalize pagename: normalize whitespace """
        cases  = (
            (u'         ', u''),
            (u'    a', u'a'),
            (u'a    ', u'a'),
            (u'a     b     c', u'a b c'),
            (u'a   b  /  c    d  /  e   f', u'a b/c d/e f'),
            # All 30 unicode spaces
            (config.chars_spaces, u''),
            )
        for test, expected in cases:
            result = request.normalizePagename(test)
            self.assertEqual(result, expected,
                             ('Expected "%(expected)s" but got "%(result)s"') %
                             locals())

    def testUnderscoreTestCase(self):
        """ request: normalize pagename: underscore convert to spaces and normalized

        Underscores should convert to spaces, then spaces should be
        normalized, order is important!
        """
        cases  = (
            (u'_________', u''),
            (u'__a', u'a'),
            (u'a__', u'a'),
            (u'a__b__c', u'a b c'),
            (u'a__b__/__c__d__/__e__f', u'a b/c d/e f'),
            )
        for test, expected in cases:
            result = request.normalizePagename(test)
            self.assertEqual(result, expected,
                             ('Expected "%(expected)s" but got "%(result)s"') %
                             locals())


class GroupPagesTestCase(unittest.TestCase):

   def setUp(self):
       self.config = TestConfig(page_group_regex = r'.+Group')              

   def tearDown(self):
       del self.config

   def testNormalizeGroupName(self):
       """ request: normalize pagename: restrict groups to alpha numeric Unicode
       
       Spaces should normalize after invalid chars removed!
       """
       import re
       group = re.compile(r'.+Group', re.UNICODE)       
       cases  = (
           # current acl chars
           (u'Name,:Group', u'NameGroup'),
           # remove than normalize spaces
           (u'Name ! @ # $ % ^ & * ( ) + Group', u'Name Group'),
           )
       for test, expected in cases:
           # validate we are testing valid group names
           assert group.search(test)
           result = request.normalizePagename(test)
           self.assertEqual(result, expected,
                            ('Expected "%(expected)s" but got "%(result)s"') %
                            locals())


# This let you run each test from the command line. When run with 
# "make test" it is not used.     
def suite():
    test_cases = [unittest.makeSuite(obj, 'test') 
        for name, obj in globals().items()
        if name.endswith('TestCase')]
    return unittest.TestSuite(test_cases)
    
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

