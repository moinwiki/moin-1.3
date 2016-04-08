# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - HTTP interfacing via CGI

    Copyright (c) 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    NEVER IMPORT THIS MODULE DIRECTLY, ALWAYS USE

        from MoinMoin import webapi

    $Id: cgiMoin.py,v 1.18 2003/11/09 21:01:16 thomaswaldmann Exp $
"""

# Imports
import os, sys

#############################################################################
### Accessors
#############################################################################

def isSSL():
    """ Return true if we are on a SSL (https) connection. """
    return os.environ.get('SSL_PROTOCOL', '') != '' or \
           os.environ.get('SSL_PROTOCOL_VERSION', '') != '' or \
           os.environ.get('HTTPS', '') == 'on'


def getScriptname():
    """ Return the scriptname part of the URL ("/path/to/my.cgi"). """
    name = os.environ.get('SCRIPT_NAME', '')
    if name == '/': return ''
    return name


def getUserAgent():
    """ Get the user agent
    """
    return os.environ.get('HTTP_USER_AGENT', '')


def getPathinfo():
    """ Return the remaining part of the URL. """
    pathinfo = os.environ.get('PATH_INFO', '')

    # Fix for bug in IIS/4.0
    if os.name == 'nt':
        scriptname = getScriptname()
        if pathinfo.startswith(scriptname):
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

class StdoutGuard:
    """ Throw an exception when someone tries to write prematurely to
        sys.stdout.
    """

    def __init__(self, request):
        self.request = request

    def __getattr__(self, attr):
        # send headers, then raise an exception to create a stack trace
        sys.stdout = sys.__stdout__
        http_headers(self.request)
        raise RuntimeError("Premature access to sys.stdout.%s" % attr)


def setHttpHeader(request, header):
    request.user_headers.append(header)


def http_headers(request, more_headers=[]):
    from MoinMoin import config

    if request.sent_headers:
        #print "Headers already sent!!!\n"
        return
    request.sent_headers = 1
    have_ct = 0

    # deactivate guard
    sys.stdout = sys.__stdout__

    # send http headers
    for header in more_headers:
        if header.lower().startswith("content-type:"): have_ct = 1
        request.write(header, '\r\n')

    for header in request.user_headers:
        if header.lower().startswith("content-type:"): have_ct = 1
        request.write(header, '\r\n')

    if not have_ct:
        request.write("Content-type: text/html;charset=%s\r\n" % config.charset)

    request.write('\r\n')

    #from pprint import pformat
    #sys.stderr.write(pformat(more_headers))
    #sys.stderr.write(pformat(request.user_headers))


def http_redirect(request, url):
    """ Redirect to a fully qualified, or server-rooted URL """
    if url.find("://") == -1:
        url = getQualifiedURL(url)

    http_headers(request, [
        "Status: 302",
        "Location: " + url,
    ])

