"""
    MoinMoin - Data associated with a single Request

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: request.py,v 1.9 2002/04/25 19:33:56 jhermann Exp $
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

        self.user = None
        self.form = None
        self.logger = None
        self.pragma = {}
        self.saved_cookie = os.environ.get('HTTP_COOKIE', None)

        self.clock = Clock()

        # for webapi.cgiMoin
        self.sent_headers = 0
        self.user_headers = []

        self.__dict__.update(properties)

        self.lang = i18n.getLang()
        i18n.adaptCharset(self.lang)

        self._footer_fragments = {}


    def add2footer(self, key, htmlcode):
        """ Add a named HTML fragment to the footer, after the default links
        """
        self._footer_fragments[key] = htmlcode


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

    def getEventLogger(self):
        """ Return a (the) event logger instance.
        """
        if self.logger is None:
            from MoinMoin.eventlog import EventLogger
            self.logger = EventLogger()

        return self.logger

