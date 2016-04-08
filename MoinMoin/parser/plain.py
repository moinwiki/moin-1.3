# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Plain Text Parser

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: plain.py,v 1.10 2003/11/09 21:01:05 thomaswaldmann Exp $
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
        self.request = request
        self.form = request.form
        self._ = request.getText

    def format(self, formatter):
        """ Send the text.
        """

        #!!! send each line via the usual formatter calls
        text = cgi.escape(self.raw)
        text = string.expandtabs(text)
        text = string.replace(text, '\n', '<br>\n')
        text = string.replace(text, ' ', '&nbsp;')
        print text

