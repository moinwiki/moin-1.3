"""
    MoinMoin - HTTP interfacing via twisted.web

    Copyright (c) 2001 by J�rgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    NEVER IMPORT THIS MODULE DIRECTLY, ALWAYS USE

        from MoinMoin import webapi

    $Id: twistedMoin.py,v 1.1 2001/10/23 22:04:49 jhermann Exp $
"""

# Imports
import os, string, sys
from MoinMoin import cgimain


#############################################################################
### Accessors
#############################################################################

def isSSL():
    """ Return true if we are on a SSL (https) connection. """
    return os.environ.get('SSL_PROTOCOL', '') != ''


def getScriptname():
    """ Return the scriptname part of the URL ("/path/to/my.cgi"). """
    return "/" + string.join(cgimain.request.twistd.prepath, '/')


def getPathinfo():
    """ Return the remaining part of the URL. """
    pathinfo = cgimain.request.twistd.postpath
    if pathinfo:
        return "/" + string.join(pathinfo, '/')
    return ''


def getQualifiedURL(uri = None):
    """ Return a full URL starting with schema, servername and port.

        *uri* -- append this server-rooted uri (must start with a slash)
    """
    result = 'http://' + (cgimain.request.twistd.getHeader('host') or cgimain.request.twistd.getHost())

    if uri: result = result + uri

    return result

    """
    schema, stdport = (('http', '80'), ('https', '443'))[isSSL()]

    host = os.environ.get('HTTP_HOST')
    if not host:
        host = os.environ.get('SERVER_NAME', 'localhost')
        port = os.environ.get('SERVER_PORT', '80')
        if port != stdport: host = host + ":" + port

    result = "%s://%s" % (schema, host)
    if uri: result = result + uri

    return result
    """

def getBaseURL():
    """ Return a fully qualified URL to this script. """
    return getQualifiedURL(getScriptname())



#############################################################################
### Headers
#############################################################################

def setHttpHeader(header):
    key, value = string.split(header, ':')
    value = string.lstrip(value)
    cgimain.request.twistd.setHeader("content-type", self.type)

def http_headers(more_headers=[]):
    for header in more_headers:
        setHttpHeader(header)

def http_redirect(url):
    """ Redirect to a fully qualified, or server-rooted URL """
    if string.count(url, "://") == 0:
        url = "http://%s:%s%s" % (
            os.environ.get('SERVER_NAME'),
            os.environ.get('SERVER_PORT'),
            url)

    http_headers(["Location: " + url])


#############################################################################
### Twisted request handling
#############################################################################

count = 0

class Output:
    def __init__(self, request):
        self.request = request
        self.write = self.request.write

    def flush(self):
        pass


def run(request):
    oldstdout = sys.stdout

    try:
        sys.stdout = Output(request)

        global count
        count = count + 1
        #print "You called me %d times!\n" % count

        cgimain.run({'twistd': request})

        #print getScriptname()
        #print getPathinfo()
    finally:
        sys.stdout = oldstdout
    
