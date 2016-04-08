"""
    MoinMoin - FootNote Macro

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Collect and emit footnotes. Note that currently footnote
    text cannot contain wiki markup.

    $Id: FootNote.py,v 1.2 2002/01/24 23:25:22 jhermann Exp $
"""

# Imports
import string
#from MoinMoin.i18n import _


def execute(macro, args):
    # create storage for footnotes
    if not hasattr(macro.request, 'footnotes'):
        macro.request.footnotes = []
    
    if not args:
        return emit_footnotes(macro.request, macro.formatter)
    else:
        # store footnote and emit number
        macro.request.footnotes.append(args)
        idx = str(len(macro.request.footnotes))
        return "%s%s%s" % (
            macro.formatter.sup(1),
            macro.formatter.anchorlink('moin_footnote' + idx, idx),
            macro.formatter.sup(0),)

    # nothing to do or emit
    return ''


def emit_footnotes(request, formatter):
    # emit collected footnotes
    if request.footnotes:
        result = ['____']
        for idx in range(len(request.footnotes)):
            result.append(formatter.linebreak(0))
            result.append(formatter.anchordef('moin_footnote%d' % (idx+1)))
            result.append(formatter.code(1))
            result.append(formatter.sup(1))
            result.append(string.replace('%4d ' % (idx+1), ' ', formatter.hardspace))
            result.append(formatter.sup(0))
            result.append(formatter.code(0))
            result.append(request.footnotes[idx])
        request.footnotes = []
        return string.join(result, '')

    return ''

