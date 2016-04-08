# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.widget.html Tests

    Copyright (c) 2003 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test_widget_html.py,v 1.6 2003/11/09 21:00:54 thomaswaldmann Exp $
"""

import cgi, unittest
from MoinMoin.widget import html


class TextTestCase(unittest.TestCase):
    def runTest(self):
        markup = '<br /> &'
        self.failUnlessEqual(str(html.Text(markup)), cgi.escape(markup))


class RawTestCase(unittest.TestCase):
    def runTest(self):
        markup = '<br /> &amp;'
        self.failUnlessEqual(str(html.Raw(markup)), markup)


class AttrTestCase(unittest.TestCase):
    def runTest(self):
        self.failUnlessRaises(AttributeError, html.BR, name='foo')


class EmptyElementTestCase(unittest.TestCase):
    def runTest(self):
        html._SORT_ATTRS = 1

        self.failUnlessEqual(str(html.BR()), '<br />')
        self.failUnlessEqual(str(html.HR()), '<hr />')


class CompositeElementTestCase(unittest.TestCase):
    def runTest(self):
        html._SORT_ATTRS = 1

        tag = html.P().append('simple & unescaped text')
        self.failUnlessEqual(str(tag), '<p>simple &amp; unescaped text</p>')

        tag = html.P().extend(['simple', ' & ', html.Text('unescaped text')])
        self.failUnlessEqual(str(tag), '<p>simple &amp; unescaped text</p>')

