#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
"""
    This implements a global (and a local) blacklist against wiki spammers.

    If started from commandline, it prints a merged list (moinmaster + MT) on
    stdout, and what it got additionally from MT on stderr.
    
    @license: GNU GPL, see COPYING for details
    @author: Thomas Waldmann
"""

# give some log entries to stderr
debug = 1

import re, sys, time

if __name__ == '__main__':
    sys.path.insert(0, "../..")

from MoinMoin.security import Permissions
from MoinMoin import caching, wikiutil


# Errors ---------------------------------------------------------------

class Error(Exception):
    """Base class for antispam errors."""

    def __str__(self):
        return repr(self)

class WikirpcError(Error):
    """ Raised when we get xmlrpclib.Fault """

    def __init__(self, msg, fault):
        """ Init with msg and xmlrpclib.Fault dict """
        self.msg = msg
        self.fault = fault

    def __str__(self):
        """ Format the using description and data from the fault """
        return self.msg + ": [%(faultCode)s]  %(faultString)s" % self.fault


# Functions ------------------------------------------------------------

def dprint(s):
    if debug:
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        sys.stderr.write('%s\n' % s)


def makelist(text):
    """ Split text into lines, strip them, skip # comments """
    lines = text.splitlines()
    list = []
    for line in lines:
        line = line.split(' # ', 1)[0] # rest of line comment
        line = line.strip()
        if line and not line.startswith('#'):
            list.append(line)
    return list


def getblacklist(request, pagename, do_update):
    """ Get blacklist, possibly downloading new copy

    @param request: current request (request instance)
    @param pagename: bad content page name (unicode)
    @rtype: list
    @return: list of blacklisted regular expressions
    """
    from MoinMoin.PageEditor import PageEditor
    p = PageEditor(pagename, request, uid_override="Antispam subsystem")
    if do_update:
        tooold = time.time() - 3600
        mymtime = wikiutil.version2timestamp(p.mtime_usecs())
        failure = caching.CacheEntry(request, "antispam", "failure")
        fail_time = failure.mtime() # only update if no failure in last hour
        if (mymtime < tooold) and (fail_time < tooold):
            dprint("%d *BadContent too old, have to check for an update..." % tooold)
            import xmlrpclib

            # TODO replace following with import socket when we require py 2.3
            # also change the call / exception names accordingly
            from MoinMoin.support import timeoutsocket

            timeout = 15 # time out for reaching the master server via xmlrpc
            old_timeout = timeoutsocket.getDefaultSocketTimeout()
            timeoutsocket.setDefaultSocketTimeout(timeout)
            
            # For production code
            uri = "http://moinmaster.wikiwikiweb.de:8000/?action=xmlrpc2"
            # For testing (use your test wiki as BadContent source)
            ##uri = "http://localhost/main/?action=xmlrpc2")
            master = xmlrpclib.ServerProxy(uri)

            try:
                # Get BadContent info
                master.putClientInfo('ANTISPAM-CHECK',
                                     request.http_host+request.script_name)
                response = master.getPageInfo(pagename)

                # It seems that response is always a dict
                if isinstance(response, dict) and 'faultCode' in response:
                    raise WikirpcError("failed to get BadContent information",
                                       response)
                
                # Compare date against local BadContent copy
                masterdate = response['lastModified']
                mydate = xmlrpclib.DateTime(tuple(time.gmtime(mymtime)))
                dprint("master: %s mine: %s" % (masterdate, mydate))
                if mydate < masterdate:
                    # Get new copy and save
                    dprint("Fetching page from master...")
                    master.putClientInfo('ANTISPAM-FETCH',
                                         request.http_host + request.script_name)
                    response = master.getPage(pagename)
                    if isinstance(response, dict) and 'faultCode' in response:
                        raise WikirpcError("failed to get BadContent data",
                                           response)
                    p._write_file(response)

            except timeoutsocket.Timeout:
                failure.update("") # update cache to wait before the next try

            except Error, err:
                # In case of Error, we log the error and use the local
                # BadContent copy.
                dprint(str(err))

            # set back socket timeout
            timeoutsocket.setDefaultSocketTimeout(old_timeout)
                
    blacklist = p.get_raw_body()
    return makelist(blacklist)


class SecurityPolicy(Permissions):
    """ Extend the default security policy with antispam feature """
    
    def save(self, editor, newtext, rev, **kw):
        BLACKLISTPAGES = ["BadContent", "LocalBadContent"]
        if not editor.page_name in BLACKLISTPAGES:
            request = editor.request

            # Start timing of antispam operation
            request.clock.start('antispam')
            
            blacklist = []
            for pn in BLACKLISTPAGES:
                do_update = (pn != "LocalBadContent")
                blacklist += getblacklist(request, pn, do_update)
            if blacklist:
                for blacklist_re in blacklist:
                    match = re.search(blacklist_re, newtext, re.I)
                    if match:
                        # Log error and raise SaveError, PageEditor
                        # should handle this.
                        _ = editor.request.getText
                        msg = _('Sorry, can not save page because "%(content)s"'
                                ' is not allowed in this wiki.') % {
                            'content': match.group()
                            }
                        dprint(msg)
                        raise editor.SaveError(msg)
            request.clock.stop('antispam')
            
        # No problem to save if my base class agree
        return Permissions.save(self, editor, newtext, rev, **kw)


def main():
    """ Fetch spammer patterns from MT blacklist and moinmaster and merge them.
        A complete new list for moinmaster gets printed to stdout,
        only the new entries are printed to stderr.
    """
    import urllib
    mtbl = urllib.urlopen("http://www.jayallen.org/comment_spam/blacklist.txt").read()
    mmbl = urllib.urlopen("http://moinmaster.wikiwikiweb.de:8000/BadContent?action=raw").read()
    mtbl = makelist(mtbl)
    mmbl = makelist(mmbl)
    print "#format plain"
    print "#acl All:read"
    newbl = []
    for i in mtbl:
        for j in mmbl:
            match = re.search(j, i, re.I)
            if match:
                break
        if not match and i not in mmbl:
            print >>sys.stderr, "%s" % i
            newbl.append(i)
    bl = mmbl + newbl
    bl.sort()
    lasti = None
    for i in bl:
        if i != lasti:
            print i
            lasti = i

if __name__ == '__main__':
    main()


