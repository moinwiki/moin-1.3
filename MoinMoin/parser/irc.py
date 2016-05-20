# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - IRC Log Parser (irssi style logs)

    @copyright: 2004 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import re
from MoinMoin import wikiutil

class Parser:
    """
        Send IRC logs in a table
    """
    extensions = ['.irc']

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
        self.form = request.form
        self._ = request.getText
        self.out = kw.get('out', request)

    def format(self, formatter):
        lines = self.raw.split('\n')
        pattern = re.compile(r"\(?(.\d:\d\d)\)?\s+\<\s*(.*?)\s*\>\s+(.*)")
        self.out.write(formatter.table(1))
        for line in lines:
            match = pattern.match(line)
            if match:
                self.out.write(formatter.table_row(1))
                for g in [1,2,3]:
                    self.out.write(formatter.table_cell(1))
                    self.out.write(wikiutil.escape(match.group(g)))
                    self.out.write(formatter.table_cell(0))
                self.out.write(formatter.table_row(0))
        self.out.write(formatter.table(0))

