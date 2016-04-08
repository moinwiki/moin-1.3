"""
    MoinMoin - TableOfContents Macro

    Copyright (c) 2000, 2001, 2002 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: TableOfContents.py,v 1.3 2002/02/13 21:13:53 jhermann Exp $
"""

# Imports
import re, sha


def execute(macro, args):
    heading = re.compile(r"^\s*(?P<hmarker>=+)\s(.*)\s(?P=hmarker)$")
    result = ""
    baseindent = 0
    indent = 0
    lineno = 0

    for line in macro.parser.lines:
        # Filter out the headings
        lineno = lineno + 1
        match = heading.match(line)
        if not match: continue

        # Get new indent level
        newindent = len(match.group(1))
        if not indent:
            baseindent = newindent - 1
            indent = baseindent

        # Close lists
        for i in range(0,indent-newindent):
            result = result + macro.formatter.number_list(0)

        # Open Lists
        for i in range(0,newindent-indent):
            result = result + macro.formatter.number_list(1)

        # Add the heading
        result = result + macro.formatter.listitem(1)
        result = result + macro.formatter.anchorlink(
            "head-"+sha.new(match.group(2)).hexdigest(),
            match.group(2))
        result = result + macro.formatter.listitem(0)

        # Set new indent level
        indent = newindent

    # Close pending lists
    for i in range(baseindent,indent):
        result = result + macro.formatter.number_list(0)

    return result

