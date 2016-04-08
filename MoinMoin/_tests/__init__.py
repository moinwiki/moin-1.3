# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Unit tests

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Subpackage containing all unit tests. This is currently NOT
    installed.

    $Id: __init__.py,v 1.8 2003/11/09 21:00:53 thomaswaldmann Exp $
"""

import os, sys, unittest
from MoinMoin import config, user
from MoinMoin.util import pysupport

# List of config parameters that must be forced to defaults
# in order to make the tests work
_FORCED_DEFAULTS = [
    'date_fmt',
    'datetime_fmt',
    'page_template_regex',
    'page_form_regex',
    'page_category_regex',
]

# Request instance for tests
request = None

def makeSuite():
    """ Automatically create tests and test suites for all tests.

        For this to work, test modules must reside in MoinMoin._tests
        (i.e. right here) and have names starting with "test_", and
        contain test cases with names ending in "TestCase".
    """
    result = unittest.TestSuite()
    test_modules = pysupport.getPackageModules(__file__)

    for mod_name in test_modules:
        if not mod_name.startswith('test_'): continue

        module = __import__(__name__ + '.' + mod_name, globals(), locals(), ['__file__'])
        test_cases = [
            obj() for name, obj in module.__dict__.items()
                if name.endswith('TestCase')
        ]

        if test_cases:
            suite = unittest.TestSuite(test_cases)
            result.addTest(suite)

    return result


def run(provided_request=None):
    global request

    if provided_request:
        request = provided_request
    else:
        from MoinMoin import cgimain
        request = cgimain.createRequest()

        import cgi
        request.form = cgi.FieldStorage(environ = {'QUERY_STRING': 'action=print'})

    for cfgval in _FORCED_DEFAULTS:
        setattr(config, cfgval, config._cfg_defaults[cfgval])

    os.environ['HTTP_COOKIE'] = ''
    request.user = user.User(request)

    suite = makeSuite()
    unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)

