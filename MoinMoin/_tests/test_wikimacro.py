# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikimacro Tests

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test_wikimacro.py,v 1.3 2003/11/09 21:00:54 thomaswaldmann Exp $
"""

import unittest, os
from MoinMoin import _tests
from MoinMoin import wikimacro
from MoinMoin.parser.plain import Parser
from MoinMoin.formatter.text_html import Formatter


def execute(macro, args):
    """ Test helper.
    """
    assert hasattr(macro, "request")
    assert hasattr(macro.request, "user")
    return args


def _make_macro():
    p = Parser("##\n", _tests.request)
    p.formatter = Formatter(_tests.request)
    p.form = _tests.request.form
    m = wikimacro.Macro(p)
    return m


class NormalMacroTestCase(unittest.TestCase):
    def runTest(self):
        m = _make_macro()
        self.failUnlessEqual(
            m.execute("BR", ""),
            m.formatter.linebreak(0))


class PluginMacroTestCase(unittest.TestCase):
    def runTest(self):
        _plugins = wikimacro._plugins
        try:
            macro_name = 'test_wikimacro'
            wikimacro._plugins = os.path.dirname(__file__)
            wikimacro.names.append(macro_name)
            wikimacro.plugin_macros.append(macro_name)

            self.failUnlessEqual(_make_macro().execute(macro_name, "OK"), "OK")
        finally:
            wikimacro._plugins = _plugins

