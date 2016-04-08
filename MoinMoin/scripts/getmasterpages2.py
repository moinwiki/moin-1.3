#!/usr/bin/python2.2
"""
This script is a hack because moinmaster wiki does not support
xmlrpc due to unknown reasons. It gets all SystemPages from srcwiki
via action=raw and stores them into dstwiki via xmlrpc.

We use wiki rpc v2 here.

GPL software, 2003-09-27 Thomas Waldmann
"""

import sys, xmlrpclib, urllib

sys.path.append("/home/twaldmann/moincvs/moin--cvs")
from MoinMoin import wikiutil

from BasicAuthTransport import BasicAuthTransport

srcurlformat = "http://twistedmatrix.com/users/jh.twistd/master/moin.cgi/%s?action=raw"
user = "xxxxxx"
password = "xxxxxxx"
#srcwiki = xmlrpclib.ServerProxy("http://linuxwiki.org/?action=xmlrpc2")
dsttrans = BasicAuthTransport(user,password)
dstwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/__xmlrpc/?action=xmlrpc2", transport=dsttrans)

def rawGetPage(srcurl, pagename, encoding='iso8859-1'):
    url = srcurl % wikiutil.quoteWikiname(pagename.encode(encoding))
    pagedata = urllib.urlopen(url).read()
    return unicode(pagedata, encoding).encode('utf-8')

def transferpage(srcurlformat, dstwiki, pagename):
    # pagedata = srcwiki.getPage(pagename)
    pagedata = rawGetPage(srcurlformat, pagename, 'iso8859-1')
    rc = dstwiki.putPage(pagename, pagedata)
    print "Transferred %s. Len = %d, rc = %d" % (pagename.encode('iso8859-1'), len(pagedata), rc)

allsystempagesgroup = 'AllSystemPagesGroup'
transferpage(srcurlformat, dstwiki, allsystempagesgroup)
allgrouppages = dstwiki.listLinks(allsystempagesgroup)

for langgrouppage in allgrouppages:
    pagename = langgrouppage['name']
    transferpage(srcurlformat, dstwiki, pagename)
    pages = dstwiki.listLinks(pagename)
    for page in pages:
        transferpage(srcurlformat, dstwiki, page['name'])

