#!/usr/bin/env python2.3
# -*- coding: iso8859-1 -*-
"""
    This implements a global (and a local) blacklist against wiki spammers.

    If started from commandline, it prints a merged list (moinmaster + MT) on
    stdout, and what it got additionally from MT on stderr.
    
    @license: GNU GPL, see COPYING for details
    @author: Thomas Waldmann
"""

# raise an exception when user tries to save bad content
raiseexception = 1

# give some log entries to stderr
debug = 1

import re, sys, time

if __name__ == '__main__':
    sys.path.append("/home/twaldmann/moincvs/moin--main--1.2")

from MoinMoin.security import Permissions

def dprint(s):
    if debug:
        print >>sys.stderr, s

def makelist(s):
    """ split text into lines, strip them, skip # comments """
    s = s.replace('\r','').split('\n')
    l = []
    for line in s:
        line = line.split(' # ', 1)[0] # rest of line comment
        line = line.strip()
        if line and line[0] != '#':
            l.append(line)
    return l

def getblacklist(request, pagename, do_update):
    from MoinMoin.PageEditor import PageEditor
    p = PageEditor(pagename, request)
    if do_update:
        tooold = time.time() - 3600
        mymtime = p.mtime()
        if mymtime < tooold:
            dprint("%d *BadContent too old, have to check for an update..." % tooold)
            import xmlrpclib
            master = xmlrpclib.ServerProxy("http://moinmaster.wikiwikiweb.de:8000/?action=xmlrpc2")
            try:
                master.putClientInfo('ANTISPAM-CHECK', request.http_host)
                mastermtime = master.getPageInfo(pagename)['version']
                dprint("master: %d mine: %d" % (mastermtime, mymtime))
                if mymtime < mastermtime:
                    dprint("Fetching page from master...")
                    master.putClientInfo('ANTISPAM-FETCH', request.http_host)
                    text = master.getPage(pagename)
                    p._write_file(text)
            except: # XXX howto catch connection refused?
                pass
    blacklist = p.get_raw_body()
    return makelist(blacklist)
    
class SecurityPolicy(Permissions):
    def save(self, editor, newtext, datestamp, **kw):
        BLACKLISTPAGES = ["BadContent","LocalBadContent"]
        if not editor.page_name in BLACKLISTPAGES:
            request = editor.request
            blacklist = []
            for pn in BLACKLISTPAGES:
                do_update = (pn != "LocalBadContent")
                blacklist += getblacklist(request, pn, do_update)
            if blacklist:
                for blacklist_re in blacklist:
                    match = re.search(blacklist_re, newtext, re.I)
                    if match:
                        break
                if match:
                    msg = "Not saving page %s because content matches blacklist: %s\n" % (editor.page_name, match.group())
                    dprint(msg)
                    if raiseexception:
                        raise msg
                return match == None
        return True

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


