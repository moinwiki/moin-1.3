# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - FootNote Macro

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Collect and emit footnotes. Note that currently footnote
    text cannot contain wiki markup.

    $Id: FootNote.py,v 1.5 2003/11/09 21:01:02 thomaswaldmann Exp $
"""

# Imports
import sha


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
        fn_id = "-%s-%s" % (sha.new(args).hexdigest(), idx)
        return "%s%s%s%s" % (
            macro.formatter.sup(1),
            macro.formatter.anchordef('fnref' + fn_id),
            macro.formatter.anchorlink('fndef' + fn_id, idx),
            macro.formatter.sup(0),)

    # nothing to do or emit
    return ''


def emit_footnotes(request, formatter):
    # emit collected footnotes
    if request.footnotes:
        result = ['____']
        for idx in range(len(request.footnotes)):
            fn_id = "-%s-%d" % (sha.new(request.footnotes[idx]).hexdigest(), idx+1)
            fn_no = formatter.anchorlink('fnref' + fn_id, str(idx+1))
            indent = 4 - len(('%4d' % (idx+1)).strip())

            result.append(formatter.linebreak(0))
            result.append(formatter.anchordef('fndef' + fn_id))
            result.append(formatter.code(1))
            result.append(formatter.sup(1))
            result.append(formatter.hardspace * indent + fn_no + formatter.hardspace)
            result.append(formatter.sup(0))
            result.append(formatter.code(0))
            result.append(formatter.text(request.footnotes[idx]))
        request.footnotes = []
        return ''.join(result)

    return ''

