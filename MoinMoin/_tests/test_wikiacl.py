# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikiacl Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin import config, wikiacl, _tests

class parsingTestCase(unittest.TestCase):
    def runTest(self):
        if not config.acl_enabled:
            return

        acl = wikiacl.AccessControlList(
            ["Admin1,Admin2:read,write,admin"
             " JoeDoe:read"
             " BadBadGuy:"
             " All:read"]
        )

        nsave=_tests.request.user.name
        _tests.request.user.name='JoeDoe'
        self.failIf(acl.may(_tests.request, 'admin'))
        _tests.request.user.name='Admin1'
        self.failUnless(acl.may(_tests.request, 'write'))
        _tests.request.user.name='Admin2'
        self.failUnless(acl.may(_tests.request, 'admin'))
        _tests.request.user.name='BelongsToAll'
        self.failUnless(acl.may(_tests.request, 'read'))
        _tests.request.user.name='BelongsToAll'
        self.failIf(acl.may(_tests.request, 'write'))
        
        _tests.request.user.name='BadBadGuy'
        for right in config.acl_rights_valid:
            self.failIf(acl.may(_tests.request, right))
        _tests.request.user.name=nsave

