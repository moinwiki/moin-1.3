# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Data associated with a single Request

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: request.py,v 1.22 2003/11/09 21:00:50 thomaswaldmann Exp $
"""

import os, string, time, sys

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
        # order is important here!
        from MoinMoin import user
        self.auth_username = properties.get('auth_username','')
        self.user = user.User(self)
        # !!! if all refs to user.current are removed, kill this assign
        user.current = self.user

        # CNC:2003-03-30
        from MoinMoin import wikigroup
        self.groups = wikigroup.GroupDict()
        self.groups.scangroups()

        from MoinMoin import i18n

        self.form = None
        self.logger = None
        self.pragma = {}
        self.saved_cookie = os.environ.get('HTTP_COOKIE', None)
        self.mode_getpagelinks = 0

        self.clock = Clock()

        # for webapi.cgiMoin
        self.sent_headers = 0
        self.user_headers = []

        self.__dict__.update(properties)

        self.i18n = i18n
        self.lang = i18n.getLang()
        self.getText = lambda text, i18n=self.i18n, lang=self.lang: i18n.getText(text, lang)
        i18n.adaptCharset(self.lang)

        self.reset()


    def reset(self):
        """ Called after saving a page, before serving the updated page;
            solves some practical problems with request state modified
            during saving.
        """
        from MoinMoin import config

        self.current_lang = config.default_lang
        self._footer_fragments = {}
        self._all_pages = None

        if hasattr(self, "_fmt_hd_counters"):
            del self._fmt_hd_counters


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


    def getPageList(self):
        """ A cached version of wikiutil.getPageList().
            Also, this list is always sorted.
        """
        if self._all_pages is None:
            from MoinMoin import config, wikiutil
            self._all_pages = wikiutil.getPageList(config.text_dir)
            self._all_pages.sort()

        return self._all_pages


    def getEventLogger(self):
        """ Return a (the) event logger instance.
        """
        if self.logger is None:
            from MoinMoin.eventlog import EventLogger
            self.logger = EventLogger()

        return self.logger


    def write(self, *data):
        """ Write to output stream.
        """
        for piece in data:
            sys.stdout.write(piece)

