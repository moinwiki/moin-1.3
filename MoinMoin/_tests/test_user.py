# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.user Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin import user
from MoinMoin.request import RequestCLI


class PasswordTestCase(unittest.TestCase):
    """user: passwords tests"""

    def testEncodePassword(self):
        """user: encode password"""
        result = user.encodePassword("MoinMoin")
        expected = "{SHA}X+lk6KR7JuJEH43YnmettCwICdU="
        self.assertEqual(result, expected,
                         'Expected "%(expected)s" but got "%(result)s"' % locals())

class GroupNameTestCase(unittest.TestCase):

    request = RequestCLI()
    request.cfg.page_group_regex = r'.+Group'
    import re
    group = re.compile(r'.+Group', re.UNICODE)
    
    def testGroupNames(self):
        """ user: isValidName: reject group names """   
        test = u'AdminGroup'
        assert self.group.search(test)
        result = user.isValidName(self.request, test)
        expected = False
        self.assertEqual(result, expected,
                        'Expected "%(expected)s" but got "%(result)s"' % locals()) 
            

class IsValidNameTestCase(unittest.TestCase):

    request = RequestCLI()
    
    def testNonAlnumCharacters(self):
        """ user: isValidName: reject unicode non alpha numeric characters

        : and , used in acl rules, we might add more characters to the syntax.
        """
        invalid = u'! @ # $ % ^ & * ( ) - = + , : ; " | ~ / \\ \u0000 \u202a'.split()
        base = u'User%sName'
        expected = False
        for c in invalid:
            name = base % c
            result = user.isValidName(self.request, name)           
        self.assertEqual(result, expected,
                         'Expected "%(expected)s" but got "%(result)s"' % locals()) 


    def testWhitespace(self):
        """ user: isValidName: reject leading, traling or multiple whitespace """
        cases = (
            u' User Name',
            u'User Name ',
            u'User   Name',
            )
        expected = False
        for test in cases:
            result = user.isValidName(self.request, test)          
            self.assertEqual(result, expected,
                         'Expected "%(expected)s" but got "%(result)s"' % locals())

    def testValid(self):
        """ user: isValidName: accept names in any language, with spaces """
        cases = (
            u'Jürgen Hermann', # German
            u'ניר סופר', # Hebrew
            u'CamelCase', # Good old camel case
            u'가각간갇갈 갉갊감 갬갯걀갼' # Hangul (gibrish)
            )
        expected = True
        for test in cases:
            result = user.isValidName(self.request, test)          
            self.assertEqual(result, expected,
                             'Expected "%(expected)s" but got "%(result)s"' % locals())


