"""
    MoinMoin - XMLRPC2 Interface

    GPL code written 2003 by Thomas Waldmann
    Parts of this code are based on Juergen Hermann's wikirpc.py,
    Les Orchard's "xmlrpc.cgi" and further work by Gustavo Niemeyer.

    Needs Python 2.0 and up.

    See http://www.ecyrd.com/JSPWiki/Wiki.jsp?page=WikiRPCInterface
    and http://www.decafbad.com/twiki/bin/view/Main/XmlRpcToWiki
    for specs on many of the functions here.

    See also http://www.jspwiki.org/Wiki.jsp?page=WikiRPCInterface2
    for the new stuff.

    The main difference between wikirpc.py (v1) and wikirpc2.py (v2)
    is that v2 relies on utf-8 as transport encoding. No url-encoding
    and no base64 anymore, except when really necessary (like for
    transferring binary files like attachments maybe).

    $Id: wikirpc2.py,v 1.4 2003/11/29 16:52:22 thomaswaldmann Exp $
"""

import sys, urllib, time

from MoinMoin import config, webapi, user
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.support import xmlrpclib
from MoinMoin.macro import RecentChanges

_debug = 1

#############################################################################
### Helpers
#############################################################################

def _instr(text):
    """ Convert inbound string from UTF-8.
    """
    if config.charset != 'UTF-8':
        text = text.encode(config.charset)
        #This is not text = unicode(text, 'UTF-8').encode(config.charset)
        #because we already get unicode! Strange, but true...
    else:
        text = text.encode('UTF-8')
        #as we obviously get unicode, we have to encode to utf-8 again
    return text

def _outstr(text):
    """ Convert outbound string to UTF-8.
    """
    if config.charset != 'UTF-8':
        text = unicode(text, config.charset).encode('UTF-8')
    return text

def _inlob(text):
    """ Convert inbound base64-encoded UTF-8 to Large OBject.
    """
    text = text.data
    if config.charset != 'UTF-8':
        text = unicode(text, 'UTF-8').encode(config.charset)
    return text

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

def xmlrpc_getRPCVersionSupported(request):
    """ Returns 2 with this version of the Wiki API.
    """
    return 2

def xmlrpc_getAllPages(request):
    """ Returns a list of all pages. The result is an array of utf-8 strings.
    """
    from MoinMoin import wikiutil

    pagelist = wikiutil.getPageList(config.text_dir)
    pagelist = filter(request.user.may.read, pagelist)

    return map(_outstr, pagelist)

def xmlrpc_getRecentChanges(request, date):
    """	array getRecentChanges ( Date timestamp ):
        Get list of changed pages since timestamp, which should be in
        UTC. The result is an array, where each element is a struct:
        * name (string) :
            Name of the page. The name is in UTF-8.
        * lastModified (date) :
            Date of last modification, in UTC.
        * author (string) :
            Name of the author (if available). UTF-8.
        * version (int) :
            Current version.
    """
    
    return_items = []
    
    log = RecentChanges.LogIterator(request)
    while log.getNextChange():
        # skip if older than "date"
        if xmlrpclib.DateTime(log.ed_time) < date:
            continue
        
        # skip if knowledge not permitted
        if not request.user.may.read(log.pagename):
            continue
        
        # get page name (str) from log
        pagename_str = _outstr(log.pagename)

        # get last-modified UTC (DateTime) from log
        gmtuple = tuple(time.gmtime(log.ed_time))
        lastModified_date = xmlrpclib.DateTime(gmtuple)

        # get user name (str) from log
        author_str = log.hostname
        if log.userid:
            userdata = user.User(request, log.userid)
            if userdata.name:
                author_str = userdata.name
        author_str = _outstr(author_str)
        
        # get version# (int) from log
        # moin uses unix time as the page version number
        version_int = int(log.ed_time)

        return_item = { 'name':  pagename_str,
                        'lastModified': lastModified_date,
                        'author': author_str,
                        'version': version_int }
        return_items.append(return_item)
    
    return return_items

def xmlrpc_getPageInfo(request, pagename):
    """ struct getPageInfo( string pagename ) :
        returns a struct with elements
        * name (string): the canonical page name, UTF-8.
        * lastModified (date): Last modification date, UTC.
        * author (string): author name, UTF-8.
        * version (int): current version
    """
    return xmlrpc_getPageInfoVersion(request, pagename, None)

def xmlrpc_getPageInfoVersion(request, pagename, version):
    """ struct getPageInfoVersion( string pagename, int version ) :
        returns a struct just like plain getPageInfo(), but this time
        for a specific version.
    """
    pn = _instr(pagename)
    if not request.user.may.read(pn):
        return xmlrpclib.Fault(1, "You are not allowed to read this page")

    if version != None:
        page = Page(pn, date=version)
    else:
        page = Page(pn)
    last_edit = page.last_edit(request)
    gmtuple = tuple(time.gmtime(last_edit['timestamp']))
    return { 'name': pagename,
             'lastModified' : xmlrpclib.DateTime(gmtuple),
             'author': _outstr(str(last_edit['editor'])),
             'version': int(last_edit['timestamp']),       # the timestamp is our "version"!
    }


def xmlrpc_getPage(request, pagename):
    """ Get the raw Wiki text of page, latest version. Page name must be
        UTF-8. Returned value is a string with UTF-8 encoded page data.
    """    
    return xmlrpc_getPageVersion(request, pagename, None)


def xmlrpc_getPageVersion(request, pagename, version):
    """ Get the raw Wiki text of page, specified version. Page name must be
        UTF-8, with URL encoding. Returned value is a binary object,
        with UTF-8 encoded page data.
    """    

    pagename = _instr(pagename)
    if not request.user.may.read(pagename):
        return xmlrpclib.Fault(1, "You are not allowed to read this page")

    if version != None:
        page = Page(pagename, date=version)
    else:
        page = Page(pagename)

    return _outstr(page.get_raw_body())


def xmlrpc_getPageHTML(request, pagename):
    """ String getPageHTML( String pagename ):
        Return page in rendered HTML. Returns UTF-8, expects UTF-8.
    """
    return xmlrpc_getPageHTMLVersion(request, pagename, None)

def xmlrpc_getPageHTMLVersion(request, pagename, version):
    """ String getPageHTMLVersion( String pagename, int version ):
        Return page in rendered HTML. Returns UTF-8, expects UTF-8.
    """
    pagename = _instr(pagename)
    if not request.user.may.read(pagename):
        return xmlrpclib.Fault(1, "You are not allowed to read this page")

    import cStringIO, cgi
    if version != None:
        page = Page(pagename, date=version)
    else:
        page = Page(pagename)

    stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    request.form = cgi.FieldStorage(headers={})
    page.send_page(request, content_only=1)
    result = sys.stdout.getvalue()
    sys.stdout = stdout

    return _outstr(result)


def xmlrpc_listLinks(request, pagename):
    """	array listLinks( string pagename ): Lists all links for a given
        page. The returned array contains structs, with the following
        elements
        * name (string) : The page name or URL the link is to, UTF-8 encoding.
        * type (int) : The link type. Zero (0) for internal Wiki
          link, one (1) for external link (URL - image link, whatever).
    """
    pagename = _instr(pagename)
    if not request.user.may.read(pagename):
        return xmlrpclib.Fault(1, "You are not allowed to read this page")

    page = Page(pagename)

    links_out = []
    for link in page.getPageLinks(request):
        links_out.append({ 'name': _outstr(link), 'type': 0 })
    return links_out		


def xmlrpc_putPage(request, pagename, pagetext):
    """	boolean wiki.putPage( String pagename, String text ): Set the
        text of a page, returning true on success
    """

    # we use a test page instead of using the requested pagename until
    # we have authentication set up - so nobody will be able to raid the wiki
    #pagename = _instr(pagename)
    pagename = "PutPageTestPage"

    # only authenticated (trusted) users may use putPage!
    # TODO: maybe replace this with an ACL right 'rpcwrite'
    if not (request.user.trusted and request.user.may.edit(pagename)):
        return xmlrpclib.Fault(1, "You are not allowed to edit this page")

    page = PageEditor(pagename, request)

    msg = page.saveText(_instr(pagetext), "0")
    if _debug and msg:
        sys.stderr.write("Msg: %s\n" % msg)

    #we need this to update pagelinks cache:
    import cgi,cStringIO
    #request.reset() # do we need that???
    stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    request.form = cgi.FieldStorage(headers={})
    page.send_page(request, content_only=1)
    sys.stdout = stdout

    return xmlrpclib.Boolean(1)
		

#############################################################################
### Dispatcher
#############################################################################

def xmlrpc2(request):
    # read request
    data = sys.stdin.read()

    params, method = xmlrpclib.loads(data)

    if _debug:
        sys.stderr.write('- XMLRPC ' + '-' * 70 + '\n')
        sys.stderr.write('%s(%s)\n\n' % (method, repr(params)))

    # generate response
    try:
        response = globals().get('xmlrpc_' + method)(request, *params)
    except:
        # report exception back to server
        response = xmlrpclib.dumps(xmlrpclib.Fault(1, _dump_exc()))
    else:
        # wrap response in a singleton tuple
        response = (response,)

        # serialize it
        response = xmlrpclib.dumps(response, methodresponse=1)

    webapi.http_headers(request, [
        "Content-Type: text/xml; charset=UTF-8",
        "Content-Length: %d" % len(response),
    ])
    sys.stdout.write(response)

    if _debug:
        sys.stderr.write('- XMLRPC ' + '-' * 70 + '\n')
        sys.stderr.write(response + '\n\n')

