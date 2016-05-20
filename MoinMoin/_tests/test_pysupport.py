# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.util.pysupport Tests

    Module names must start with 'test_' to be included in the tests.

    @copyright: 2004 by Jürgen Hermann <ograf@bitart.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest, tempfile, os
from MoinMoin.util import pysupport
from MoinMoin._tests import request, TestConfig


class ImportNameTestCase(unittest.TestCase):
    """ Test if importName works correctly
    """

    def setUp(self):
        """ Create a dummy plugin path with some module inside
        """
        self.plugin_dir = tempfile.mktemp()
        self.parser_dir = os.path.join(self.plugin_dir, 'plugin', 'parser')
        os.makedirs(self.parser_dir)
        open(os.path.join(self.plugin_dir, 'plugin', '__init__.py'), 'w')
        open(os.path.join(self.plugin_dir, 'plugin', 'parser', '__init__.py'), 'w')
        f = open(os.path.join(self.parser_dir, 'test.py'), 'w')
        f.write('import sys, os\ndef test():\n    pass\n')
        f.close()
    
    def tearDown(self):
        """ Remove the plugin dir
        """
        for file in (os.path.join(self.plugin_dir, 'plugin', '__init__.py'),
                     os.path.join(self.plugin_dir, 'plugin', '__init__.pyc'),
                     os.path.join(self.plugin_dir, 'plugin', 'parser', '__init__.py'),
                     os.path.join(self.plugin_dir, 'plugin', 'parser', '__init__.pyc'),
                     os.path.join(self.parser_dir, 'test.py'),
                     os.path.join(self.parser_dir, 'test.pyc')):
            try:
                os.unlink(file)
            except OSError:
                pass
        for dir in (os.path.join(self.plugin_dir, 'plugin', 'parser'),
                    os.path.join(self.plugin_dir, 'plugin'),
                    self.plugin_dir):
            os.rmdir(dir)
 
    def testImportName1(self):
        """ pysupport: import nonexistant parser from moin
        
        Must return None."""
        self.failIf(pysupport.importName('MoinMoin.parser.abcdefghijkl',
                                         'Parser'))

    def testImportName2(self):
        """ pysupport: import wiki parser from moin
        
        This tests if a module can be imported from the package
        MoinMoin. Should never fail, cause importName uses
        __import__ to do it."""
        self.failUnless(pysupport.importName('MoinMoin.parser.wiki',
                                             'Parser'))

    def testImportName3(self):
        """ pysupport: import nonexistant parser plugin
        
        Must return None."""
        self.failIf(pysupport.importName('plugin.parser.abcdefghijkl',
                                         'Parser'))

    def testImportName4(self):
        """ pysupport: import test parser plugin
        
        Tests if a module can be importet from an arbitary path
        like it is done in moin for plugins. Some strange bug
        in the old implementation failed on an import of os,
        cause os does a from os.path import that will stumple
        over a poisoned sys.modules."""
        self.failUnless(pysupport.importName('plugin.parser.test',
                                             'test',
                                             self.plugin_dir),
                        'Failed to import the test plugin!')
