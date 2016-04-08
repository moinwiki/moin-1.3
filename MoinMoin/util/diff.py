# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Side by side diffs

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    Copyright (c) 2002 by Scott Moonen <smoonen@andstuff.org>
    All rights reserved, see COPYING for details.

    $Id: diff.py,v 1.6 2003/11/09 21:01:14 thomaswaldmann Exp $
"""

import cgi
from MoinMoin.support import difflib


escape = cgi.escape

def indent(line):
    eol = ''
    while line and line[0] == '\n':
        eol += '\n'
        line = line[1:]
    stripped = line.lstrip()
    if len(line) - len(stripped):
        line = "&nbsp;" * (len(line) - len(stripped)) + stripped
    #return "%d / %d / %s" % (len(line), len(stripped), line)
    return eol + line


# This code originally by Scott Moonen, used with permission.
def diff(request, old, new):
    """ Find changes between old and new and return
        HTML markup visualising them.
    """
    _ = request.getText
    t_line = _("Line") + " "

    seq1 = old.splitlines()
    seq2 = new.splitlines()

    seqobj = difflib.SequenceMatcher(None, seq1, seq2)
    linematch = seqobj.get_matching_blocks()

    if len(seq1) == len(seq2) and linematch[0] == (0, 0, len(seq1)):
        # No differences.
        return _("<b>No differences found!</b>")

    lastmatch = (0, 0)
    end       = (len(seq1), len(seq2))

    result = (
           "<table class='diff'>\n"
         + "<tr><td colspan='2' class='diff-removed'>"
         + "<del class='diff-removed'>"
         + _('Deletions are marked like this.')
         + "</del>"
         + "</td><td colspan='2' class='diff-added'>"
         + "<ins class='diff-added'>"
         + _('Additions are marked like this.')
         + "</ins>"
         + "</td></tr>\n"
    )

    # Print all differences
    for match in linematch:
        # Starts of pages identical?
        if lastmatch == match[0:2]:
            lastmatch = (match[0] + match[2], match[1] + match[2])
            continue

        result += (
               "<tr><td colspan='2' class='diff-title'><strong>"
             + t_line + str(lastmatch[0] + 1) + ":"
             + "</strong></td><td colspan='2' class='diff-title'><strong>"
             + t_line + " " + str(lastmatch[1] + 1) + ":"
             + "</strong></td></tr>\n"
        )

        leftpane  = ''
        rightpane = ''
        linecount = max(match[0] - lastmatch[0], match[1] - lastmatch[1])
        for line in range(linecount):
            if line < match[0] - lastmatch[0]:
                if line > 0:
                    leftpane += '\n'
                leftpane += seq1[lastmatch[0] + line]
            if line < match[1] - lastmatch[1]:
                if line > 0:
                    rightpane += '\n'
                rightpane += seq2[lastmatch[1] + line]

        charobj   = difflib.SequenceMatcher(None, leftpane, rightpane)
        charmatch = charobj.get_matching_blocks()

        if charobj.ratio() < 0.5:
            # Insufficient similarity.
            if leftpane:
                leftresult = "<del class='diff-removed'>" + indent(escape(leftpane)) + "</del>"
            else:
                leftresult = ''

            if rightpane:
                rightresult = "<ins class='diff-added'>" + indent(escape(rightpane)) + "</ins>"
            else:
                rightresult = ''
        else:
            # Some similarities; markup changes.
            charlast = (0, 0)
            charend  = (len(leftpane), len(rightpane))

            leftresult  = ''
            rightresult = ''
            for thismatch in charmatch:
                if thismatch[0] - charlast[0] != 0:
                    leftresult += (
                         "<del class='diff-removed'>"
                       + indent(escape(leftpane[charlast[0]:thismatch[0]]))
                       + "</del>"
                    )
                if thismatch[1] - charlast[1] != 0:
                    rightresult += (
                          "<ins class='diff-added'>"
                        + indent(escape(rightpane[charlast[1]:thismatch[1]]))
                        + "</ins>"
                    )
                leftresult += escape(leftpane[thismatch[0]:thismatch[0] + thismatch[2]])
                rightresult += escape(rightpane[thismatch[1]:thismatch[1] + thismatch[2]])
                charlast = (thismatch[0] + thismatch[2], thismatch[1] + thismatch[2])

        leftpane  = '<br />\n'.join(map(indent, leftresult.splitlines()))
        rightpane = '<br />\n'.join(map(indent, rightresult.splitlines()))

        result += (
               "<tr><td colspan='2' class='diff-removed' width='50%'>"
             + leftpane
             + "</td><td colspan='2' class='diff-added' width='50%'>"
             + rightpane
             + "</td></tr>\n"
        )

        lastmatch = (match[0] + match[2], match[1] + match[2])

    result += '</table>\n'

    return result

