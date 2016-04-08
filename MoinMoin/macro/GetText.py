# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Load I18N Text

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro has the main purpose of supporting Help* page authors
    to insert the texts that a user actually sees on his screen into
    the description of the related features (which otherwise could
    get very confusing).

    $Id: GetText.py,v 1.5 2003/11/09 21:01:02 thomaswaldmann Exp $
"""

def execute(macro, args):
    return macro.formatter.text(
        macro.request.getText(args).replace('<br>', '\n')
    )

