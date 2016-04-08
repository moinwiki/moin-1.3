"""
    MoinMoin - Processor for Syntax Highlighting

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: Colorize.py,v 1.3 2002/04/17 19:24:58 jhermann Exp $
"""

import string, sys, cStringIO
from MoinMoin.parser import python

def process(request, formatter, lines):
    if not formatter.in_pre:
        sys.stdout.write(formatter.preformatted(1))

    if string.strip(lines[0]) == "#!python":
        del lines[0]

    # !!! same code as with "inline:" handling in parser/wiki.py,
    # this needs to be unified!

    buff = cStringIO.StringIO()
    colorizer = python.Parser(string.join(lines, '\n'), request, out = buff)
    colorizer.format(formatter, {})

    sys.stdout.write(formatter.rawHTML(buff.getvalue()))
    sys.stdout.write(formatter.preformatted(0))

