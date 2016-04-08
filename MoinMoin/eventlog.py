"""
    MoinMoin - Event log management

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    The event log records things in time like viewing a page,
    editing it, etc. For now, we just add events, later we need
    to add statistical reports, and aggregation to a database.

    $Id: eventlog.py,v 1.7 2002/02/13 21:13:52 jhermann Exp $
"""

# Imports
import os, string, time, urllib
from MoinMoin import config, util


#############################################################################
### Event logger
#############################################################################

class EventLogger:
    """ The event log.
    """

    def __init__(self):
        self._logfile = None
        self._ua_match = None
        if config.ua_spiders:
            import re
            self._ua_match = re.compile(config.ua_spiders)

    def _write(self, data):
        if not self._logfile:
            self._logfile = open(os.path.join(config.data_dir, 'event.log'), 'a')
        self._logfile.write(data + "\n")
        self._logfile.flush()

    def add(self, eventtype, values={}, add_http_info=1):
        """ Write an event of type `eventtype, with optional key/value
            pairs appended (i.e. you have to pass a dict).
        """
        if self._ua_match and self._ua_match.search(os.environ.get('HTTP_USER_AGENT', '')):
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
        file = open(os.path.join(config.data_dir, 'event.log'), 'r')
        events = file.readlines()
        file.close()

        data = []
        for event in events:
            time, eventtype, kvpairs = string.split(string.rstrip(event), '\t')
            if filter and eventtype not in filter: continue
            data.append((float(time), eventtype, util.parseQueryString(kvpairs)))

        return data


logger = EventLogger()

