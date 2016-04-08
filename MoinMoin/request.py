"""
    MoinMoin - HTTP Request Data

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: request.py,v 1.2 2001/10/23 22:04:48 jhermann Exp $
"""

import os, time

#############################################################################
### Timing
#############################################################################

class Clock:
    """ Helper class for code profiling """

    def __init__(self):
        self.timings = {'total': time.clock()}

    def start(self, timer):
        self.timings[timer] = time.clock() - self.timings.get(timer, 0)

    def stop(self, timer):
        self.timings[timer] = time.clock() - self.timings[timer]

    def value(self, timer):
        return "%.3f" % (self.timings[timer],)

    def dump(self, file):
        for timing in self.timings.items():
            file.write("%s = %.3f\n" % timing)


#############################################################################
### Request Data
#############################################################################

class Request:
    """ A collection for all data associated with ONE request. """

    def __init__(self, properties={}):
        self.form = None
        self.saved_cookie = os.environ.get('HTTP_COOKIE', None)

        self.clock = Clock()

        # for webapi.cgiMoin
        self.sent_headers = 0
        self.user_headers = []

        self.__dict__.update(properties)

