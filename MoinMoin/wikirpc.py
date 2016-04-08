"""
    MoinMoin - XMLRPC Interface

    Copyright (c) 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Parts of this code are based on Les Orchard's "xmlrpc.cgi".
    Needs Python 2.0 and up.

    See http://www.ecyrd.com/JSPWiki/Wiki.jsp?page=WikiRPCInterface
    and http://www.decafbad.com/twiki/bin/view/Main/XmlRpcToWiki
    for specs on many of the functions here.

    $Id: wikirpc.py,v 1.4 2002/05/09 03:47:51 jhermann Exp $
"""

import sys, urllib

from MoinMoin import config, webapi
from MoinMoin.support import xmlrpclib

_debug = 1

#############################################################################
### Helpers
#############################################################################

def _instr(text):
    """ Convert inbound string from urlencoded UTF-8.
    """
    text = urllib.unquote(text)
    if config.charset == 'UTF-8':
        return text
    else:
        return unicode(text, 'UTF-8').encode(config.charset)

def _outstr(text):
    """ Convert outbound string to urlencoded UTF-8.
    """
    if config.charset != 'UTF-8':
        text = unicode(text, config.charset).encode('UTF-8')
    return urllib.quote(text)

def _outlob(text):
    """ Convert outbound Large OBject to base64-encoded UTF-8.
    """
    if config.charset != 'UTF-8':
        text = unicode(text, config.charset).encode('UTF-8')
    return xmlrpclib.Binary(text)

def _dump_exc():
    """ Convert an exception to a string.
    """
    import traceback

    return "%s: %s\n%s" % (
        sys.exc_info()[0],
        sys.exc_info()[1],
        '\n'.join(traceback.format_tb(sys.exc_info()[2])),
    )


#############################################################################
### Interface implementation
#############################################################################

def xmlrpc_getRPCVersionSupported():
    """ Returns 1 with this version of the Wiki API.
    """
    return 1

def xmlrpc_getAllPages():
    """ Returns a list of all pages. The result is an array of strings,
        again UTF-8 in URL encoding.
    """
    from MoinMoin import wikiutil

    pagelist = wikiutil.getPageList(config.text_dir)
    return map(_outstr, pagelist)


def xmlrpc_getPage(pagename):
    """ Get the raw Wiki text of page, latest version. Page name must be
        UTF-8, with URL encoding. Returned value is a binary object,
        with UTF-8 encoded page data.
    """    
    from MoinMoin.Page import Page

    page = Page(_instr(pagename))
    return _outlob(page.get_raw_body())


#############################################################################
### Dispatcher
#############################################################################

def xmlrpc(request):
    # read request
    data = sys.stdin.read()

    params, method = xmlrpclib.loads(data)

    if _debug:
        sys.stderr.write('- XMLRPC ' + '-' * 70 + '\n')
        sys.stderr.write('%s(%s)\n\n' % (method, repr(params)))

    # generate response
    try:
        response = globals().get('xmlrpc_' + method)(*params)
    except:
        # report exception back to server
        response = xmlrpclib.dumps(xmlrpclib.Fault(1, _dump_exc()))
    else:
        if 0 and _debug:
            sys.stderr.write('- XMLRPC ' + '-' * 70 + '\n')
            sys.stderr.write(repr(response) + '\n\n')

        # wrap response in a singleton tuple
        response = (response,)

        # serialize it
        response = xmlrpclib.dumps(response, methodresponse=1)

    webapi.http_headers(request, [
        "Content-Type: text/xml",
        "Content-Length: %d" % len(response),
    ])
    sys.stdout.write(response)

    if _debug:
        sys.stderr.write('- XMLRPC ' + '-' * 70 + '\n')
        sys.stderr.write(response + '\n\n')

