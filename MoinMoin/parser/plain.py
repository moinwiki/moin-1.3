"""
    MoinMoin - Plain Text Parser

    Copyright (c) 2000, 2001, 2002 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: plain.py,v 1.7 2002/04/17 19:24:58 jhermann Exp $
"""

# Imports
import cgi, string


#############################################################################
### Plain Text Parser
#############################################################################

class Parser:
    """
        Send plain text in a HTML <pre> element.
    """

    def __init__(self, raw, request, **kw):
        self.raw = raw

    def format(self, formatter, form):
        """ Send the text.
        """

        #!!! send each line via the usual formatter calls
        text = cgi.escape(self.raw)
        text = string.expandtabs(text)
        text = string.replace(text, '\n', '<br>\n')
        text = string.replace(text, ' ', '&nbsp;')
        print text

