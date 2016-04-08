# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - TableOfContents Macro

    Optional integer argument: maximal depth of listing.

    @copyright: 2000, 2001, 2002 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# Imports
import re, sha

Dependencies = ["page"]

def execute(macro, args):
    heading = re.compile(r"^\s*(?P<hmarker>=+)\s(.*)\s(?P=hmarker)$")
    result = []
    baseindent = 0
    indent = 0
    lineno = 0
    titles = {}

    try:
        mindepth = int(macro.request.getPragma('section-numbers', 1))
    except (ValueError, TypeError):
        mindepth = 1

    try:
        maxdepth = max(int(args), 1)
    except (ValueError, TypeError):
        maxdepth = 99

    for line in macro.parser.lines:
        # Filter out the headings
        lineno = lineno + 1
        # FIXME this also finds "headlines" in {{{ code sections }}}:
        match = heading.match(line)
        if not match: continue
        title_text = match.group(2)
        titles.setdefault(title_text, 0)
        titles[title_text] += 1

        # Get new indent level
        newindent = len(match.group(1))
        if newindent > maxdepth: continue
        if newindent < mindepth: continue
        if not indent:
            baseindent = newindent - 1
            indent = baseindent

        # Close lists
        for i in range(0,indent-newindent):
            result.append(macro.formatter.number_list(0))

        # Open Lists
        for i in range(0,newindent-indent):
            result.append(macro.formatter.number_list(1))

        # Add the heading
        unique_id = ''
        if titles[title_text] > 1:
            unique_id = '-%d' % titles[title_text]

        result.append(macro.formatter.listitem(1))
        result.append(macro.formatter.anchorlink(
            "head-" + sha.new(title_text).hexdigest() + unique_id, title_text))
        result.append(macro.formatter.listitem(0))
        
        # Set new indent level
        indent = newindent

    # Close pending lists
    for i in range(baseindent, indent):
        result.append(macro.formatter.number_list(0))

    return ''.join(result)

