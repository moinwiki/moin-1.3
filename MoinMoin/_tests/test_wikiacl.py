# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikiacl Tests

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test_wikiacl.py,v 1.6 2003/11/09 21:00:54 thomaswaldmann Exp $
"""

import unittest
from MoinMoin import config, wikiacl, _tests

class parsingTestCase(unittest.TestCase):
    def runTest(self):
        if not config.acl_enabled:
	    return
	    
        acl = wikiacl.AccessControlList(_tests.request,
            ["Admin1,Admin2:read,write,admin"
             " JoeDoe:read"
             " BadBadGuy:"
             " All:read"]
        )

        self.failIf(acl.may('JoeDoe', 'admin'))
        self.failUnless(acl.may('Admin1', 'write'))
        self.failUnless(acl.may('Admin2', 'admin'))
        self.failUnless(acl.may('BelongsToAll', 'read'))
        self.failIf(acl.may('BelongsToAll', 'write'))

        for right in config.acl_rights_valid:
            self.failIf(acl.may('BadBadGuy', right))

