# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.util.pysupport Tests

    @copyright: 2004 by Jürgen Hermann <ograf@bitart.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest, os
from MoinMoin.util import pysupport
from MoinMoin._tests import request, TestConfig


class ImportNameFromMoinTestCase(unittest.TestCase):
    """ Test importName of MoinMoin modules

    We don't make any testing for files, assuming that moin package is
    not broken.
    """

    def testNonExisting(self):
        """ pysupport: import nonexistent moin parser return None """
        self.failIf(pysupport.importName('MoinMoin.parser.abcdefghijkl',
                                         'Parser'))

    def testExisting(self):
        """ pysupport: import wiki parser from moin succeed
        
        This tests if a module can be imported from the package
        MoinMoin. Should never fail!
        """
        self.failUnless(pysupport.importName('MoinMoin.parser.wiki',
                                             'Parser'))
   

class ImportNameFromPluginTestCase(unittest.TestCase):
    """ Test if importName form wiki plugin package """
    
    def setUp(self):
        """ Check for valid plugin and parser packages """
        # Make sure we have valid plugin and parser dir
        self.plugindir = os.path.join(request.cfg.data_dir, 'plugin')
        assert os.path.exists(os.path.join(self.plugindir, '__init__.py')), \
            "Can't run tests, no plugin package"
        self.parserdir = os.path.join(self.plugindir, 'parser')
        assert os.path.exists(os.path.join(self.parserdir, '__init__.py')), \
            "Can't run tests, no plugin.parser package"
    
    def testNonEsisting(self):
        """ pysupport: import nonexistent plugin return None """
        name = 'abcdefghijkl'

        # Make sure that the file does not exists
        for suffix in ['.py', '.pyc']:
            path = os.path.join(self.parserdir, name + suffix)
            assert not os.path.exists(path), \
               "Can't run test, path exists: %r" % path
        
        self.failIf(pysupport.importName('plugin.parser.%s' % name,
                                         'Parser'))

    def testExisting(self):
        """ pysupport: import existing plugin succeed
        
        Tests if a module can be imported from an arbitrary path
        like it is done in moin for plugins. Some strange bug
        in the old implementation failed on an import of os,
        cause os does a from os.path import that will stumble
        over a poisoned sys.modules.
        """
        # Save a test plugin
        pluginName = 'MoinMoinTestParser'
        data = '''
import sys, os

class Parser:
    pass
'''
        # Plugin path does not include the suffix!
        pluginPath = os.path.join(self.parserdir, pluginName)

        # File must not exists - or we might destroy user data!
        for suffix in ['.py', '.pyc']:
            assert not os.path.exists(pluginPath + suffix), \
               "Can't run test, path exists: %r" % path
        
        try:
            # Write test plugin
            f = file(pluginPath + '.py', 'w')
            f.write(data)
            f.close()

            modulename = request.cfg.siteid + '.plugin.parser.' + pluginName
            plugin = pysupport.importName(modulename, 'Parser')
            self.failUnless(plugin.__name__ == 'Parser',
                            'Failed to import the test plugin')
        finally:
            # Remove the test plugin, including the pyc file.
            for suffix in ['.py', '.pyc']:
                try:
                    os.unlink(pluginPath + suffix)
                except OSError:
                    pass
