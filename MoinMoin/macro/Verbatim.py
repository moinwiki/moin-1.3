# -*- coding: iso-8859-1 -*-
"""
    Outputs the text verbatimly.

    @copyright: ...
    @license: GNU GPL, see COPYING for details
"""

Dependencies = []

def execute(macro, args):
    return macro.formatter.escapedText(args)
