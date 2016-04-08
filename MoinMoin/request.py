"""
    MoinMoin - HTTP Request Data

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: request.py,v 1.5 2002/02/13 21:13:52 jhermann Exp $
"""

import os, string, time

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
        from MoinMoin import i18n

        self.form = None
        self.pragma = {}
        self.saved_cookie = os.environ.get('HTTP_COOKIE', None)

        self.clock = Clock()

        # for webapi.cgiMoin
        self.sent_headers = 0
        self.user_headers = []

        self.__dict__.update(properties)

        self.lang = i18n.getLang()
        i18n.adaptCharset(self.lang)

    def getPragma(self, key, defval=None):
        """ Query a pragma value (#pragma processing instruction)

            Keys are not case-sensitive.
        """
        return self.pragma.get(string.lower(key), defval)

    def setPragma(self, key, value):
        """ Set a pragma value (#pragma processing instruction)

            Keys are not case-sensitive.
        """
        self.pragma[string.lower(key)] = value

