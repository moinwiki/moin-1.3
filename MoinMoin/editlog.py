# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Edit log management

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Functions to keep track of when people have changed pages, so we
    can do the recent changes page and so on.

    $Id: editlog.py,v 1.28 2003/11/09 21:00:49 thomaswaldmann Exp $
"""

# Imports
import cgi, os, string
from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page


#############################################################################
### Basic Interface
#############################################################################

class LogBase:
    """ Basic interface for log stores.
    """

    def __init__(self, request, optstr):
        self.request = request
        self.options = optstr

    def sanityCheck(self):
        """ Perform a self-test, i.e. check for correct config, permissions,
            etc. Return error message or `false`.
        """
        return None

    def addEntry(self, pagename, host, mtime, comment, action):
        """ Add an entry to the editlog """
        pass


#############################################################################
### Logging to text file
#############################################################################

def makeLogEntry(request, pagename, host, mtime, comment, action="SAVE"):
    """ Generate a line for the editlog.
    
        If `host` is None, it's read from the CGI environment.
    """
    import socket

    if not host:
        host = os.environ.get('REMOTE_ADDR', '')

    try:
        hostname = socket.gethostbyaddr(host)[0]
    except socket.error:
        hostname = host

    remap_chars = string.maketrans('\t\r\n', '   ')
    comment = string.translate(comment, remap_chars)

    return string.join((wikiutil.quoteFilename(pagename), host, repr(mtime),
        hostname, request.user.valid and request.user.id or '', comment, action), "\t") + "\n"


def loadLogEntry(request, filepath):
    """ Load a single log entry from a file, used for last-edited indicator
        and lock files.
        
        Return None or EditLog instance.
    """
    if os.path.exists(filepath):
        log = EditLog(request, filename=filepath)
        if log.next():
            return log
        del log

    return None


class LogText(LogBase):
    """ Storage for log entries in a plain text file.

        The editlog is stored with one record per line, as tab-separated
        words: pagename, host, time, hostname, userid

        TODO: Check values written in are reasonable
    """

    def __init__(self, request, optstr):
        LogBase.__init__(self, request, optstr)
        self.filename = os.path.join(config.data_dir, optstr)

    def sanityCheck(self):
        """ Check for editlog file access.
        """
        if not os.access(self.filename, os.W_OK):
            return "The edit log '%s' is not writable!" % (self.filename,)
        return None


    def addEntry(self, pagename, host, mtime, comment, action="SAVE"):
        """ Add an entry to the editlog """
        entry = makeLogEntry(self.request, pagename, host, mtime, comment, action)

        logfile = open(self.filename, 'a+')
        try:
            # fcntl.flock(logfile.fileno(), fcntl.LOCK_EX)
            logfile.seek(0, 2)                  # to end
            logfile.write(entry)
        finally:
            # fcntl.flock(logfile.fileno(), fcntl.LOCK_UN)
            logfile.close()

        if action[:4] == "SAVE":
            # write entry to last-edited file
            lastedited = open(wikiutil.getPagePath(pagename, 'last-edited'), 'w')
            try:
                lastedited.write(entry)
            finally:
                lastedited.close()


#############################################################################
### Factory
#############################################################################

def makeLogStore(request, option=None):
    """ Creates a storage object that provides an implementation of the
        storage type given in the `option` parameter; option consists
        of a `schema:` part, followed by a schema-specific option string.

        Currently supported schemas are: "text".
    """
    if option is None: option = config.LogStore

    schema, optstr = string.split(option, ':', 1)
    if schema == "text":
        return LogText(request, optstr)
    return None


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

    def __init__(self, request, **kw):
        self.request = request

        self._index = 0
        self._usercache = {}
        self._filename = kw.get('filename', os.path.join(config.data_dir, 'editlog'))

        self._lines = self._editlog_raw_lines()
        if not kw.get('reverse', 0):
            self._lines.reverse()

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
        try:
            line = self._lines[self._index + offset]
            ok = 1
        except IndexError:
            line = ""
            ok = 0
        self._parse_log_line(line)
        return ok

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
        """ Return a tuple of type id and string or Page object
            representing the user that did the edit.

            The type id is one of 'ip' (DNS or numeric IP), 'user' (user name)
            or 'homepage' (Page instance of user's homepage).
        """
        result = ('ip', self.hostname)
        if self.userid:
            if not self._usercache.has_key(self.userid):
                self._usercache[self.userid] = user.User(self.request, self.userid)
            userdata = self._usercache[self.userid]
            if userdata.name:
                pg = wikiutil.getHomePage(self.request, username=userdata.name)
                if pg:
                    result = ('homepage', pg)
                else:
                    result = ('user', userdata.name)

        return result


    def getEditor(self):
        """ Return a HTML-safe string representing the user that did the edit.
        """
        kind, editor = self.getEditorData()
        if kind == 'homepage':
            return '<span title="%s">%s</span>' % (cgi.escape(self.hostname), editor.link_to())
        elif kind == 'ip':
            return '<span title="%s">%s</span>' % (cgi.escape(self.addr), cgi.escape(editor))
        else:
            return '<span title="%s">%s</span>' % (cgi.escape(self.hostname), cgi.escape(editor))


    def size(self):
        """ Return size in bytes.
        """
        try:
            return os.path.getsize(self._filename)
        except os.error:
            return 0

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
        try:
            logfile = open(self._filename, 'rt')
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
        fields = line.strip().split('\t')
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

