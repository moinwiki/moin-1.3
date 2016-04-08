"""
    MoinMoin - HTTP interfacing via CGI

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    NEVER IMPORT THIS MODULE DIRECTLY, ALWAYS USE

        from MoinMoin import webapi

    $Id: cgiMoin.py,v 1.13 2002/04/17 21:58:17 jhermann Exp $
"""

# Imports
import os, string

#############################################################################
### Accessors
#############################################################################

def isSSL():
    """ Return true if we are on a SSL (https) connection. """
    return os.environ.get('SSL_PROTOCOL', '') != '' or \
           os.environ.get('SSL_PROTOCOL_VERSION', '') != ''


def getScriptname():
    """ Return the scriptname part of the URL ("/path/to/my.cgi"). """
    name = os.environ.get('SCRIPT_NAME', '')
    if name == '/': return ''
    return name


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
    if uri and uri[:4] == "http":
        return uri

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

def setHttpHeader(request, header):
    request.user_headers.append(header)


def http_headers(request, more_headers=[]):
    from MoinMoin import config

    if request.sent_headers:
        #print "Headers already sent!!!\n"
        return
    request.sent_headers = 1
    have_ct = 0

    # send http headers
    for header in more_headers:
        if string.lower(header)[:13] == "content-type:": have_ct = 1
        print header

    for header in request.user_headers:
        if string.lower(header)[:13] == "content-type:": have_ct = 1
        print header

    if not have_ct:
        print "Content-type: text/html;charset=%s" % config.charset

    #print "Pragma: no-cache"
    #print "Cache-control: no-cache"
    #!!! Better set expiry to some 10 mins or so for normal pages?
    print

    #from pprint import pformat
    #sys.stderr.write(pformat(more_headers))
    #sys.stderr.write(pformat(request.user_headers))


def http_redirect(request, url):
    """ Redirect to a fully qualified, or server-rooted URL """
    if string.count(url, "://") == 0:
        url = getQualifiedURL(url)

    http_headers(request, [
        "Status: 302",
        "Location: " + url,
    ])

