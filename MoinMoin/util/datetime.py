# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Date & Time Utilities

    Copyright (c) 2003 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: datetime.py,v 1.3 2003/11/09 21:01:14 thomaswaldmann Exp $
"""

# we guarantee that time is always imported!
import time


def tmtuple(tmsecs=None):
    """ Return a time tuple.

        This is currently an alias for gmtime(), but allows later tweaking.
    """
    # avoid problems due to timezones etc. - especially a underflow
    if -86400 <= tmsecs <= 86400: # if we are around 0, we maybe had
        tmsecs = 0                # 0 initially, so reset it to 0.
    return time.gmtime(tmsecs or time.time())

