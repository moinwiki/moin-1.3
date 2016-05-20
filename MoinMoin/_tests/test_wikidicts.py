# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikidicts tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
import re

from MoinMoin import wikidicts 
from MoinMoin._tests import request, TestConfig
from MoinMoin import Page

class GroupPageTestCase(unittest.TestCase):

    def testGroupMembers(self):
        """ wikidicts: create group from first level list items """
        text = '''
Text ignored
 * CamelCase1
 * extended name
 * ["extended link"]
  * Second level list ignored

Empty lines ignored, so is this text
 * CamelCase2
'''
        group = wikidicts.Group(request, '')
        group.initFromText(text)
        members = group.members()
        members.sort()
        expected =  ['CamelCase1', 'CamelCase2', 'extended link', 'extended name']
        self.assertEqual(members, expected)


class DictPageTestCase(unittest.TestCase):

    def testGroupMembers(self):
        """ wikidicts: create dict from keys and values in text """
        text = '''
Text ignored
 * list items ignored
  * Second level list ignored
 First:: first item
 text with spaces:: second item

Empty lines ignored, so is this text
Next line has key with empty value
 Empty string:: 
 Last:: last item
'''
        d = wikidicts.Dict(request, '')
        d.initFromText(text)        
        self.assertEqual(d['First'], 'first item')
        self.assertEqual(d['text with spaces'], 'second item')
        self.assertEqual(d['Empty string'], '')        
        self.assertEqual(d['Last'], 'last item')


class GroupDictTestCase(unittest.TestCase):

    def testSystemPagesGroupInDicts(self):
        """ wikidict: names in SystemPagesGroup should be in request.dicts

        Get a list of all pages, and check that the dicts list all of them.

        Assume that the SystemPagesGroup is in the data or the underlay dir.
        """
        assert Page.Page(request, 'SystemPagesGroup').exists(), \
               "SystemPagesGroup is missing, Can't run test"
        systemPages = wikidicts.Group(request, 'SystemPagesGroup')
        for member in systemPages.members():
            self.assert_(request.dicts.has_member('SystemPagesGroup', member),
                         '%s should be in request.dict' % member)    


def suite():
    test_cases = [unittest.makeSuite(obj, 'test') 
        for name, obj in globals().items()
        if name.endswith('TestCase')]
    return unittest.TestSuite(test_cases)
    
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
