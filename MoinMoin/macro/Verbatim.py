# -*- coding: iso-8859-1 -*-
"""
    add description here

    @copyright: ...
    @license: GNU GPL, see COPYING for details
"""

Dependencies = ["language"]

def execute(macro, args):
    return macro.formatter.escapedText(args)
