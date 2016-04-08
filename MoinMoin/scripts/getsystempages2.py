#!/usr/bin/python2.2
"""
This script gets all SystemPages from srcwiki via xmlrpc and
stores them into dstwiki via xmlrpc. We use wiki rpc v2 here.

GPL software, 2003-08-10 Thomas Waldmann
"""

import xmlrpclib
from BasicAuthTransport import BasicAuthTransport

# xmlrpc on moinmaster does not work yet -- ThomasWaldmann 2003-08-30
#srcwiki = xmlrpclib.ServerProxy("http://twistedmatrix.com/users/jh.twistd/master/moin.cgi/FrontPage?action=xmlrpc")
user = "xxxxxx"
password = "xxxxxxx"
srctrans = BasicAuthTransport(user,password)
dsttrans = BasicAuthTransport(user,password)
srcwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/__xmlrpc/?action=xmlrpc2", transport=srctrans)
dstwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/__xmlrpc/?action=xmlrpc2", transport=dsttrans)

def transferpage(srcwiki, dstwiki, pagename):
    pagedata = srcwiki.getPage(pagename)
    dstwiki.putPage(pagename, pagedata)
    print "Transferred %s." % pagename

allsystempagesgroup = 'AllSystemPagesGroup'
transferpage(srcwiki, dstwiki, allsystempagesgroup)
allgrouppages = srcwiki.listLinks(allsystempagesgroup)
for langgrouppage in allgrouppages:
    pagename = langgrouppage['name']
    transferpage(srcwiki, dstwiki, pagename)
    pages = srcwiki.listLinks(pagename)
    for page in pages:
        transferpage(srcwiki, dstwiki, page['name'])

