"""
    MoinMoin - Edit log management

    Copyright (c) 2000-2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: editlog.py,v 1.4 2001/03/09 17:26:01 jhermann Exp $
"""

# Imports
import string, time
from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page


#############################################################################
### Edit Logging
#############################################################################

# Functions to keep track of when people have changed pages, so we can
# do the recent changes page and so on.
# The editlog is stored with one record per line, as tab-separated
# words: pagename, host, time, hostname, userid

# TODO: Check values written in are reasonable

def editlog_add(pagename, host, mtime):
    """ Add an entry to the editlog """
    from MoinMoin import user
    import socket

    try:
        hostname = socket.gethostbyaddr(host)[0]
    except socket.error:
        hostname = host

    logfile = open(config.editlog_name, 'a+')
    entry = string.join((wikiutil.quoteFilename(pagename), host, `mtime`,
                         hostname, user.User().id), "\t") + "\n"
    try: 
        # fcntl.flock(logfile.fileno(), fcntl.LOCK_EX)
        logfile.seek(0, 2)                  # to end
        logfile.write(entry)
    finally:
        # fcntl.flock(logfile.fileno(), fcntl.LOCK_UN)
        logfile.close()


class EditLog:
    """ A read-only form of the editlog. Do NOT access the file
        config.editlog_name directly, since this may well end up
        in a database.

        After you called next(), the following member variables are valid:
        pagename, addr, ed_time, hostname, userid
    """

    def __init__(self):
        self._lines = self._editlog_raw_lines()
        self._lines.reverse()
        self._index = 0
        self._usercache = {}

        # set default member values
        self._parse_log_line("")

    #
    # Public interface
    #

    def next(self):
        """ Load next editlog entry, return false after last entry """
        if self._index >= len(self._lines):
            self._parse_log_line("")
            return 0
        self._parse_log_line(self._lines[self._index])
        self._index = self._index + 1
        return 1


    def reset(self):
        """ Reset for a new iteration """
        self._index = 0


    def filter(self, **kw):
        """ Filter current entries, reset() does NOT clear any filter
            previously set. The cursor is automatically set to the
            first entry.
        """
        cond = self._make_condition(kw)
        rest = []
        self.reset()
        while self.next():
            if cond(self):
                rest.append(self._lines[self._index-1])
        self._lines = rest
        self.reset()


    def find(self, **kw):
        """ Find an entry, return true on success.
        """
        cond = self._make_condition(kw)
        for index in range(len(self._lines)):
            self._parse_log_line(self._lines[index])
            if cond(self):
                return 1

        self._parse_log_line("")
        return 0            


    def getEditor(self):
        """ Return a string representing the user that did the edit.
        """
        result = self.hostname
        if self.userid:
            if not self._usercache.has_key(self.userid):
                self._usercache[self.userid] = user.User(self.userid)
            userdata = self._usercache[self.userid]
            if userdata.name:
                pg = Page(userdata.name)
                if pg.exists():
                    result = pg.link_to()
                else:
                    result = userdata.name or self.hostname

        return result


    def __len__(self):
        return len(self._lines)

    # this would return a raw line, and we do not want that
    #def __getitem__(self, key):
    #    return self._lines[key]


    #
    # Helper methods
    #

    def _editlog_raw_lines(self):
        """ Load a list of raw editlog lines """
        logfile = open(config.editlog_name, 'rt')
        try:
            # fcntl.flock(logfile.fileno(), fcntl.LOCK_SH)
            return logfile.readlines()
        finally:
            # fcntl.flock(logfile.fileno(), fcntl.LOCK_UN)
            logfile.close()
        return []


    def _parse_log_line(self, line):
        """ Parse a log line to member variables:
            pagename, addr, ed_time, hostname, userid
        """
        fields = string.split(string.strip(line), '\t')
        while len(fields) < 5: fields.append('')

        self.pagename, self.addr, self.ed_time, self.hostname, self.userid = fields[:5]
        if not self.hostname:
            self.hostname = self.addr
        self.pagename = wikiutil.unquoteFilename(self.pagename)
        self.ed_time = float(self.ed_time or "0")

    def _make_condition(self, kw):
        """ Create a callable that filters an entry according to values
            in the dictionary "kw". The keys in that dictionary have to
            be the member names of the fields ("pagename", etc.).
        """
        expr = "1"
        for field in ['pagename', 'addr', 'hostname', 'userid']:
            if kw.has_key(field):
                expr = "%s and x.%s == %s" % (expr, field, `kw[field]`)

        if kw.has_key('ed_time'):
            expr = "%s and int(x.ed_time) == %s" % (expr, int(kw['ed_time']))

        return eval("lambda x: " + expr)
