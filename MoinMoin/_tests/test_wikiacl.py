# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikiacl Tests

    @copyright: 2003-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin._tests import TestConfig
from MoinMoin import config, wikiacl, _tests

acliter = wikiacl.ACLStringIterator

class ACLStringIteratorTestCase(unittest.TestCase):
    cfg = _tests.request.cfg
    
    def setUp(self):
        self.config = TestConfig(defaults=['acl_rights_valid', 'acl_rights_before'],
                                 acl_enabled=1)
                
    def tearDown(self):
        del self.config
        
    def testEmpty(self):
        """ wikiacl: empty acl string raise StopIteration """
        iter = acliter(self.cfg.acl_rights_valid, '')
        self.failUnlessRaises(StopIteration, iter.next)

    def testWhiteSpace(self):
        """ wikiacl: white space acl string raise StopIteration """
        iter = acliter(self.cfg.acl_rights_valid, '       ')
        self.failUnlessRaises(StopIteration, iter.next)
            
    def testDefault(self):
        """ wikiacl: default meta acl """
        iter = acliter(self.cfg.acl_rights_valid, 'Default Default')
        for mod, entries, rights in iter:
            self.assertEqual(entries, ['Default'])
            self.assertEqual(rights, [])
                
    def testEmptyRights(self):
        """ wikiacl: empty rights """    
        iter = acliter(self.cfg.acl_rights_valid, 'WikiName:')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['WikiName'])
        self.assertEqual(rights, [])

    def testSingleWikiNameSingleWrite(self):
        """ wikiacl: single wiki name, single right """
        iter = acliter(self.cfg.acl_rights_valid, 'WikiName:read')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['WikiName'])
        self.assertEqual(rights, ['read'])

    def testMultipleWikiNameAndRights(self):
        """ wikiacl: multiple wiki names and rights """
        iter = acliter(self.cfg.acl_rights_valid, 'UserOne,UserTwo:read,write')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['UserOne', 'UserTwo'])
        self.assertEqual(rights, ['read', 'write'])      
        
    def testMultipleEntries(self):
        """ wikiacl: multiple entries """
        iter = acliter(self.cfg.acl_rights_valid,
                       'UserOne:read,write UserTwo:read All:')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['UserOne'])
        self.assertEqual(rights, ['read', 'write'])      
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['UserTwo'])
        self.assertEqual(rights, ['read'])      
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['All'])
        self.assertEqual(rights, [])      
       
    def testNameWithSpaces(self):
        """ wikiacl: single name with spaces """
        iter = acliter(self.cfg.acl_rights_valid, 'user one:read')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['user one'])
        self.assertEqual(rights, ['read'])

    def testMultipleWikiNameAndRights(self):
        """ wikiacl: multiple names with spaces """
        iter = acliter(self.cfg.acl_rights_valid, 'user one,user two:read')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['user one', 'user two'])
        self.assertEqual(rights, ['read'])      
        
    def testMultipleEntriesWithSpaces(self):
        """ wikiacl: multiple entries with spaces """
        iter = acliter(self.cfg.acl_rights_valid, 'user one:read,write user two:read')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['user one'])
        self.assertEqual(rights, ['read', 'write'])      
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['user two'])
        self.assertEqual(rights, ['read'])      
         
    def testMixedNames(self):
        """ wikiacl: mixed wiki names and names with spaces """
        iter = acliter(self.cfg.acl_rights_valid,
                       'UserOne,user two:read,write user three,UserFour:read')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['UserOne', 'user two'])
        self.assertEqual(rights, ['read', 'write'])      
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['user three', 'UserFour'])
        self.assertEqual(rights, ['read'])      

    def testModifier(self):
        """ wikiacl: acl modifiers """
        iter = acliter(self.cfg.acl_rights_valid, '+UserOne:read -UserTwo:')
        mod, entries, rights = iter.next()
        self.assertEqual(mod, '+')
        self.assertEqual(entries, ['UserOne'])
        self.assertEqual(rights, ['read'])
        mod, entries, rights = iter.next()
        self.assertEqual(mod, '-')
        self.assertEqual(entries, ['UserTwo'])
        self.assertEqual(rights, [])
        
    def testIgnoreInvalidACL(self):
        """ wikiacl: ignore invalid acl

        The last part of this acl can not be parsed. If it ends with :
        then it will be parsed as one name with spaces.
        """
        iter = acliter(self.cfg.acl_rights_valid, 'UserOne:read user two is ignored')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['UserOne'])
        self.assertEqual(rights, ['read'])
        self.failUnlessRaises(StopIteration, iter.next)
        
    def testEmptyNamesWithRight(self):
        """ wikiacl: empty names with rights

        The documents does not talk about this case, may() should ignore
        the rights because there is no entry.
        """
        iter = acliter(self.cfg.acl_rights_valid, 'UserOne:read :read All:')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['UserOne'])
        self.assertEqual(rights, ['read'])
        mod, entries, rights = iter.next()
        self.assertEqual(entries, [])
        self.assertEqual(rights, ['read'])        
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['All'])
        self.assertEqual(rights, [])

    def testIgnodeInvalidRights(self):
        """ wikiacl: ignore rights not in acl_rights_valid """
        iter = acliter(self.cfg.acl_rights_valid, 'UserOne:read,sing,write,drink,sleep')
        mod, entries, rights = iter.next()
        self.assertEqual(rights, ['read', 'write'])        

    def testBadGuy(self):
        """ wikiacl: bad guy may not allowed anything

        This test was failing on the apply acl rights test.
        """
        iter = acliter(self.cfg.acl_rights_valid, 'UserOne:read,write BadGuy: All:read')
        mod, entries, rights = iter.next()
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['BadGuy'])
        self.assertEqual(rights, [])

    def testAllowExtraWhitespace(self):
        """ wikiacl: allow extra white space between entries """
        iter = acliter(self.cfg.acl_rights_valid,
                       'UserOne,user two:read,write   user three,UserFour:read  All:')
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['UserOne', 'user two'])
        self.assertEqual(rights, ['read', 'write'])      
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['user three', 'UserFour'])
        self.assertEqual(rights, ['read'])      
        mod, entries, rights = iter.next()
        self.assertEqual(entries, ['All'])
        self.assertEqual(rights, [])            
       

class AclTestCase(unittest.TestCase):
    """wikiacl: testing access control list

    TO DO: test unknown user?
    """
    request = _tests.request

    def setUp(self):
        # Backup user
        self.config = TestConfig(defaults=['acl_rights_valid', 'acl_rights_before'],
                                 acl_enabled=1)
        self.savedUser = self.request.user.name
        
    def tearDown(self):
        # Restore user
        self.request.user.name = self.savedUser
        del self.config
        
    def testApplyACLByUser(self):
        """wikiacl: applying acl by user name"""
        assert self.request.cfg.acl_enabled

        # This acl string...
        acl_rights = [
            "Admin1,Admin2:read,write,delete,revert,admin  "
            "Admin3:read,write,admin  "
            "JoeDoe:read,write  "
            "name with spaces,another one:read,write  "
            "CamelCase,extended name:read,write  "
            "BadGuy:  "
            "All:read  "
            ]
        acl = wikiacl.AccessControlList(self.request, acl_rights)

        # Should apply these rights:
        users = (
            # user,                 rights
            # CamelCase names
            ('Admin1',              ('read', 'write', 'admin', 'revert', 'delete')),
            ('Admin2',              ('read', 'write', 'admin', 'revert', 'delete')),
            ('Admin3',              ('read', 'write', 'admin')),
            ('JoeDoe',              ('read', 'write')),
            ('SomeGuy',             ('read',)),
            # Extended names or mix of extended and CamelCase
            ('name with spaces',    ('read','write',)),
            ('another one',         ('read','write',)),
            ('CamelCase',           ('read','write',)),
            ('extended name',       ('read','write',)),
            # Blocking bad guys
            ('BadGuy',              ()),
            # All other users - every one not mentioned in the acl lines
            ('All',                 ('read',)),
            ('Anonymous',           ('read',)),
            )       

        # Check rights
        for user, may in users:
            mayNot = [right for right in self.request.cfg.acl_rights_valid
                      if right not in may]
            # User should have these rights...
            for right in may:
                self.assert_(acl.may(self.request, user, right),
                    '"%(user)s" should be allowed to "%(right)s"' % locals())
            # But NOT these:
            for right in mayNot:
                self.failIf(acl.may(self.request, user, right),
                    '"%(user)s" should NOT be allowed to "%(right)s"' % locals())
            
