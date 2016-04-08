"""
    MoinMoin - HTTP interfacing for command line

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    NEVER IMPORT THIS MODULE DIRECTLY, ALWAYS USE

        from MoinMoin import webapi

    $Id: cliMoin.py,v 1.2 2002/04/17 21:58:17 jhermann Exp $
"""


#############################################################################
### Accessors
#############################################################################

def isSSL():
    """ Return true if we are on a SSL (https) connection. """
    return 0

def getScriptname():
    """ Return the scriptname part of the URL ("/path/to/my.cgi"). """
    return '.'


def getPathinfo():
    """ Return the remaining part of the URL. """
    return ''


def getQualifiedURL(uri = None):
    """ Return a full URL starting with schema, servername and port.

        *uri* -- append this server-rooted uri (must start with a slash)
    """
    return uri


def getBaseURL():
    """ Return a fully qualified URL to this script. """
    return getQualifiedURL(getScriptname())



#############################################################################
### Headers
#############################################################################

def setHttpHeader(request, header):
    pass

def http_headers(request, more_headers=[]):
    pass

def http_redirect(request, url):
    """ Redirect to a fully qualified, or server-rooted URL """
    raise Exception("Redirect not supported for command line tools!")

