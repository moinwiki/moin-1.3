"""
    MoinMoin - Edit log management

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Functions to keep track of when people have changed pages, so we
    can do the recent changes page and so on.

    $Id: editlog.py,v 1.14 2002/02/13 21:13:52 jhermann Exp $
"""

# Imports
import cgi, os, string, time
from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page


#############################################################################
### Basic Interface
#############################################################################

class LogBase:
    """ Basic interface for log stores.
    """

    def __init__(self, optstr):
        self.options = optstr

    def sanityCheck(self):
        """ Perform a self-test, i.e. check for correct config, permissions,
            etc. Return error message or `false`.
        """
        return None

    def addEntry(self, pagename, host, mtime, comment):
        """ Add an entry to the editlog """
        pass


#############################################################################
### Logging to text file
#############################################################################

class LogText(LogBase):
    """ Storage for log entries in a plain text file.

        The editlog is stored with one record per line, as tab-separated
        words: pagename, host, time, hostname, userid

        TODO: Check values written in are reasonable
    """

    def __init__(self, optstr):
        LogBase.__init__(self, optstr)
        self.filename = os.path.join(config.data_dir, optstr)

    def sanityCheck(self):
        """ Check for editlog file access.
        """
        if not os.access(self.filename, os.W_OK):
            return "The edit log '%s' is not writable!" % (self.filename,)

    def addEntry(self, pagename, host, mtime, comment, action="SAVE"):
        """ Add an entry to the editlog """
        import socket

        try:
            hostname = socket.gethostbyaddr(host)[0]
        except socket.error:
            hostname = host

        remap_chars = string.maketrans('\t\r\n', '   ')
        comment = string.translate(comment, remap_chars)

        logfile = open(self.filename, 'a+')
        entry = string.join((wikiutil.quoteFilename(pagename), host, `mtime`,
                             hostname, user.User().id, comment, action), "\t") + "\n"
        try:
            # fcntl.flock(logfile.fileno(), fcntl.LOCK_EX)
            logfile.seek(0, 2)                  # to end
            logfile.write(entry)
        finally:
            # fcntl.flock(logfile.fileno(), fcntl.LOCK_UN)
            logfile.close()


#############################################################################
### Factory
#############################################################################

def makeLogStore(option=None):
    """ Creates a storage object that provides an implementation of the
        storage type given in the `option` parameter; option consists
        of a `schema:` part, followed by a schema-specific option string.

        Currently supported schemas are: "text".
    """
    if option is None: option = config.LogStore

    schema, optstr = string.split(option, ':', 1)
    if schema == "text":
        return LogText(optstr)


#############################################################################
### former code!
#############################################################################

class EditLog:
    """ A read-only form of the editlog. Do NOT access the file
        config.editlog_name directly, since this may well end up
        in a database.

        After you called next(), the following member variables are valid:
        pagename, addr, ed_time, hostname, userid
    """

    _NUM_FIELDS = 7

    def __init__(self, **kw):
        self._lines = self._editlog_raw_lines()
        if not kw.get('reverse', 0):
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
        if self.peek(0):
            self._index = self._index + 1
            return 1
        return 0


    def peek(self, offset):
        """ Peek `offset` entries ahead (or behind), return false after last entry """
        idx = self._index + offset
        if idx < 0 or len(self._lines) <= idx:
            self._parse_log_line("")
            return 0
        self._parse_log_line(self._lines[idx])
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


    def getEditorData(self):
        """ Return a string or Page object representing the user that did the edit.
        """
        result = self.hostname
        if self.userid:
            if not self._usercache.has_key(self.userid):
                self._usercache[self.userid] = user.User(self.userid)
            userdata = self._usercache[self.userid]
            if userdata.name:
                pg = Page(userdata.name)
                if pg.exists():
                    result = pg
                else:
                    result = userdata.name or self.hostname

        return result


    def getEditor(self):
        """ Return a HTML-safe string representing the user that did the edit.
        """
        result = self.getEditorData()
        if isinstance(result, Page):
            return result.link_to()
        return cgi.escape(result)


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
        editlog_name = os.path.join(config.data_dir, 'editlog') #!!! self.filename
        try:
            logfile = open(editlog_name, 'rt')
            try:
                # fcntl.flock(logfile.fileno(), fcntl.LOCK_SH)
                return logfile.readlines()
            finally:
                # fcntl.flock(logfile.fileno(), fcntl.LOCK_UN)
                logfile.close()
        except IOError, er:
            import errno
            if er.errno == errno.ENOENT:
                # just doesn't exist, return empty list
                return []
            else:
                raise er

        return []


    def _parse_log_line(self, line):
        """ Parse a log line to member variables:
            pagename, addr, ed_time, hostname, userid
        """
        fields = string.split(string.strip(line), '\t')
        while len(fields) < self._NUM_FIELDS: fields.append('')

        self.pagename, self.addr, self.ed_time, self.hostname, \
            self.userid, self.comment, self.action = fields[:self._NUM_FIELDS]
        if not self.hostname:
            self.hostname = self.addr
        self.pagename = wikiutil.unquoteFilename(self.pagename)
        self.ed_time = float(self.ed_time or "0")
        if not self.action:
            self.action = 'SAVE'


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

