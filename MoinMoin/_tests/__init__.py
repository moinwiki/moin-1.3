# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Unit tests

    Sub package containing all unit tests. This is currently NOT
    installed.

    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os
import sys
import unittest
from MoinMoin import config, multiconfig, user
from MoinMoin.util import pysupport


# Exceptions
class TestSkiped(Exception):
    """ Raised when a tests is skipped """


class TestConfig:
    """ Custom configuration for unit tests
    
    Some test assume specific configuration, and will fail if the wiki admin
    will change the configuration. For example, DateTime macro test assume 
    the default datetime_fmt.
    
    When you set custom values in a TestConfig, the previous values are saved,
    and when the TestConfig is deleted, they are restored automatically.
    
    Typical use:

        from MoinMoin._tests import TestConfig
        class SomeTestCase(unittest.TestCase):
            def setUp(self):
                self.config = TestConfig(defaults=key_list, key=value,...)              
            def tearDown(self):
                del self.config
            def testSomething(self):
                # test that needs those defaults and custom values
    """
    
    def __init__(self, defaults=(), **custom):
        """ Create temporary configuration for a test 
        
        @param defaults: list of keys that should use the default value
        @param **custom: other keys using non default values, or new keys
               that request.cfg does not have already
        """
        self.old = {}  # Old config values
        self.new = []  # New added attributes
        self.setDefaults(defaults)
        self.setCustom(**custom)
    
    def setDefaults(self, defaults=()):
        """ Set default values for keys in defaults list
        
        Non existing default will raise an AttributeError.
        """
        for key in defaults:
            self._setattr(key, getattr(multiconfig.DefaultConfig, key))              
    
    def setCustom(self, **custom):
        """ Set custom values """
        for key, value in custom.items():
            self._setattr(key, value)
    
    def _setattr(self, key, value):
        """ Set a new value for key saving new added keys """
        if hasattr(request.cfg, key):
            self.old[key] = getattr(request.cfg, key)
        else:
            self.new.append(key)
        setattr(request.cfg, key, value)        
       
    def __del__(self):
        """ Restore previous request.cfg 
        
        Set old keys to old values and delete new keys.
        """
        for key, value in self.old.items():
            setattr(request.cfg, key, value)
        for key in self.new:
            delattr(request.cfg, key)


# Request instance for tests
request = None

def makeSuite():
    """ Automatically create tests and test suites for all tests.

        For this to work, test modules must reside in MoinMoin._tests
        (i.e. right here) and have names starting with "test_", and
        contain test cases with names ending in "TestCase". Each test case
        may contain multiply testAABBCC methods. Those methods will be run by 
        the test suites. See _test_template.py for an example, and use it to
        create new tests.
    """
    result = unittest.TestSuite()
    test_modules = pysupport.getPackageModules(__file__)
    # Sort test modules names by case insensitive compare to get nicer output
    caseInsensitiveCompare = lambda a, b: cmp(a.lower(), b.lower())
    test_modules.sort(caseInsensitiveCompare)

    for mod_name in test_modules:
        if not mod_name.startswith('test_'): continue

        # Import module
        module = __import__(__name__ + '.' + mod_name, 
        	globals(), locals(), ['__file__'])
        # Collect TestCase and create suite for each one
        test_cases = [unittest.makeSuite(obj, 'test') 
            for name, obj in module.__dict__.items()
            if name.endswith('TestCase')]
        
        # Add tests suites
        if test_cases:
            suite = unittest.TestSuite(test_cases)
            result.addTest(suite)

    return result


def run(provided_request=None):
    global request

    if provided_request:
        request = provided_request
    else:
        from MoinMoin.request import RequestCLI
        request = RequestCLI()
    
        request.form = request.args = request.setup_args()
        # {'query_string': 'action=print'}

        request.user = user.User(request)

    suite = makeSuite()
    unittest.TextTestRunner(stream=request, verbosity=2).run(suite)

