"""
    MoinMoin - HTTP interfacing via CGI

    Copyright (c) 2001 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    NEVER IMPORT THIS MODULE DIRECTLY, ALWAYS USE

        from MoinMoin import webapi

    $Id: cgiMoin.py,v 1.4 2001/05/04 22:00:16 jhermann Exp $
"""

# Imports
import os, string


#############################################################################
### Accessors
#############################################################################

def isSSL():
    """ Return true if we are on a SSL (https) connection. """
    return os.environ.get('SSL_PROTOCOL', '') != ''


def getScriptname():
    """ Return the scriptname part of the URL ("/path/to/my.cgi"). """
    return os.environ.get('SCRIPT_NAME', '')


def getPathinfo():
    """ Return the remaining part of the URL. """
    pathinfo = os.environ.get('PATH_INFO', '')

    # Fix for bug in IIS/4.0
    if os.name == 'nt':
        scriptname = getScriptname()
        if string.find(pathinfo, scriptname) == 0:
            pathinfo = pathinfo[len(scriptname):]                
    
    return pathinfo


def getQualifiedURL(uri = None):
    """ Return a full URL starting with schema, servername and port.

        *uri* -- append this server-rooted uri (must start with a slash)
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


def getBaseURL():
    """ Return a fully qualified URL to this script. """
    return getQualifiedURL(getScriptname())



#############################################################################
### Headers
#############################################################################

# Globals
sent_headers = 0
user_headers = []


def setHttpHeader(header):
    global user_headers
    user_headers.append(header)


def http_headers(more_headers=[]):
    global sent_headers
    if sent_headers:
        #print "Headers already sent!!!\n"
        return
    sent_headers = 1
    have_ct = 0

    # send http headers
    for header in more_headers:
        if string.lower(header)[:13] == "content-type:": have_ct = 1
        print header

    global user_headers
    for header in user_headers:
        if string.lower(header)[:13] == "content-type:": have_ct = 1
        print header

    if not have_ct:
        print "Content-type: text/html"

    #print "Pragma: no-cache"
    #print "Cache-control: no-cache"
    #!!! Better set expiry to some 10 mins or so for normal pages?
    print

    #from pprint import pformat
    #sys.stderr.write(pformat(more_headers))
    #sys.stderr.write(pformat(user_headers))


def http_redirect(url):
    """ Redirect to a fully qualified, or server-rooted URL """
    if string.count(url, "://") == 0:
        url = "http://%s:%s%s" % (
            os.environ.get('SERVER_NAME'),
            os.environ.get('SERVER_PORT'),
            url)

    http_headers(["Location: " + url])

