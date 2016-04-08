# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Event log management

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    The event log records things in time like viewing a page,
    editing it, etc. For now, we just add events, later we need
    to add statistical reports, and aggregation to a database.

    $Id: eventlog.py,v 1.13 2003/11/09 21:00:49 thomaswaldmann Exp $
"""

# Imports
import os, string, time, urllib
from MoinMoin import config, util
import MoinMoin.util.web


#############################################################################
### Event logger
#############################################################################

class EventLogger:
    """ The event log.
    """

    def __init__(self):
        self._filename = os.path.join(config.data_dir, 'event.log')
        self._logfile = None

    def _write(self, data):
        if not self._logfile:
            self._logfile = open(self._filename, 'a')
        self._logfile.write(data + "\n")
        self._logfile.flush()

    def add(self, eventtype, values={}, add_http_info=1):
        """ Write an event of type `eventtype, with optional key/value
            pairs appended (i.e. you have to pass a dict).
        """
        if util.web.isSpiderAgent():
            return

        kvlist = values.items()
        if add_http_info:
            for key in ['REMOTE_ADDR', 'HTTP_USER_AGENT', 'HTTP_REFERER']:
                val = os.environ.get(key, '')
                if val: kvlist.append((key, val))
        kvpairs = ""
        for key, val in kvlist:
            if kvpairs: kvpairs = kvpairs + "&"
            kvpairs = "%s%s=%s" % (kvpairs, urllib.quote(key), urllib.quote(val))
        self._write("%s\t%s\t%s" % (time.time(), eventtype, kvpairs))

    def read(self, filter=None):
        """ Return a list of (time, eventtype, valuedict) triples.

            `filter` -- list of eventtypes to filter for
        """
        file = open(self._filename, 'r')
        events = file.readlines()
        file.close()

        data = []
        for event in events:
            try:
                time, eventtype, kvpairs = string.split(string.rstrip(event), '\t')
            except ValueError:
                # badly formatted line in file, skip it
                continue
            if filter and eventtype not in filter: continue
            data.append((float(time), eventtype, util.web.parseQueryString(kvpairs)))

        return data

    def size(self):
        """ Return size in bytes.
        """
        try:
            return os.path.getsize(self._filename)
        except os.error:
            return 0

