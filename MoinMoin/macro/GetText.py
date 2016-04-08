"""
    MoinMoin - Load I18N Text

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    This macro has the main purpose of supporting Help* page authors
    to insert the texts that a user actually sees on his screen into
    the description of the related features (which otherwise could
    get very confusing).

    $Id: GetText.py,v 1.1 2001/12/07 22:54:14 jhermann Exp $
"""

# Imports
from MoinMoin.i18n import getText

def execute(macro, args):
    return getText(args)

