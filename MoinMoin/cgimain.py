# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Main CGI Module

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: cgimain.py,v 1.65 2003/11/09 21:00:48 thomaswaldmann Exp $
"""

opened_logs = 0


#############################################################################
### Helper functions
#############################################################################

def createRequest(properties={}):
    # set up request data
    from MoinMoin.request import Request
    return Request(properties)


def test(properties={}):
    from MoinMoin.wikitest import runTest
    request = createRequest(properties)
    runTest(request)
    return request


#############################################################################
### Main code
#############################################################################

def run(properties={}):
    import cgi, os, sys, string

    # force input/output to binary
    if sys.platform == "win32" and not properties.get('standalone', 0):
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    # create CGI log file, and one for catching stderr output
    from MoinMoin import config
    global opened_logs
    if not opened_logs:
        cgi.logfile = os.path.join(config.data_dir, 'cgi.log')
        sys.stderr = open(os.path.join(config.data_dir, 'error.log'), 'at')
        opened_logs = 1

    if os.environ.get('AUTH_TYPE','') == 'Basic':
        auth_username = os.environ.get('REMOTE_USER','')
        properties.update({'auth_username': auth_username})

    # create request object, including default user
    request = createRequest(properties)

    # Imports
    from MoinMoin import version, wikiutil, webapi
    from MoinMoin.Page import Page
    from MoinMoin.i18n import _

    # check for web spiders very early, and refuse anything except viewing
    forbidden = 0
    if os.environ.get('QUERY_STRING') != '' or os.environ.get('REQUEST_METHOD') != 'GET':
        from MoinMoin.util import web
        forbidden = web.isSpiderAgent()

    if not forbidden and config.hosts_deny:
        ip = os.environ.get('REMOTE_ADDR')
        for host in config.hosts_deny:
            if ip == host or host[-1] == '.' and ip.startswith(host):
                forbidden = 1
                break

    if forbidden:
        webapi.http_headers(request, [
            'Status: 403 FORBIDDEN',
            'Content-Type: text/plain'
        ])
        request.write('You are not allowed to access this!\n')
        sys.exit(0)

    # install stdout guard if available
    if hasattr(webapi, 'StdoutGuard'):
        sys.stdout = webapi.StdoutGuard(request)

    # sys.stderr.write("----\n")
    # for key in os.environ.keys():    
    #     sys.stderr.write("    %s = '%s'\n" % (key, os.environ[key]))

    query_string = os.environ.get('QUERY_STRING')
    if query_string == 'action=xmlrpc':
        from MoinMoin.wikirpc import xmlrpc
        xmlrpc(request)
        return request

    if query_string == 'action=xmlrpc2':
        from MoinMoin.wikirpc2 import xmlrpc2
        xmlrpc2(request)
        return request

    # parse request data
    try:
        request.form = cgi.FieldStorage()
        path_info = webapi.getPathinfo()

        action = None
        if request.form.has_key('action'):
            action = request.form['action'].value

        pagename = None
        if len(path_info) and path_info[0] == '/':
            pagename = wikiutil.unquoteWikiname(path_info[1:])
    except: # catch and print any exception
        webapi.http_headers(request)
        cgi.print_exception()
        sys.exit(0)

    # possibly jump to page where user left off
    if not pagename and not action and request.user.remember_last_visit:
        pagetrail = request.user.getTrail()
        if pagetrail:
            webapi.http_redirect(request, Page(pagetrail[-1]).url())
            sys.exit(0)

    try:
        # handle request
        from MoinMoin import wikiaction

        # check for non-URI characters and then handle them according to
        # http://www.w3.org/TR/REC-html40/appendix/notes.html#h-B.2.1
        if pagename and sys.version[:2] != '1.':
            try:
                dummy = unicode(pagename, 'ASCII')
            except UnicodeError:
                # we have something else than plain ASCII, try converting
                # from UTF-8 to local charset
                try:
                    pagename = unicode(pagename, 'UTF-8').encode(config.charset)
                except UnicodeError:
                    # give up, use URI value literally and see what happens
                    pass

        if request.form.has_key('filepath') and request.form.has_key('noredirect'):
            # looks like user wants to save a drawing
            from MoinMoin.action.AttachFile import execute
            execute(pagename, request)
            sys.exit(0)
        if action:
            handler = wikiaction.getHandler(action)
            if handler:
                handler(pagename or wikiutil.getSysPage(config.page_front_page).page_name, request)
            else:
                webapi.http_headers(request)
                print "<p>" + _("Unknown action")
        else:
            if request.form.has_key('goto'):
                query = string.strip(request.form['goto'].value)
            elif pagename:
                query = pagename
            else:
                query = wikiutil.unquoteWikiname(os.environ.get('QUERY_STRING', '')) or \
                    wikiutil.getSysPage(config.page_front_page).page_name

            if config.allow_extended_names:
                Page(query).send_page(request, count_hit=1)
            else:
                from MoinMoin.parser.wiki import Parser
                import re
                word_match = re.match(Parser.word_rule, query)
                if word_match:
                    word = word_match.group(0)
                    Page(word).send_page(request, count_hit=1)
                else:
                    webapi.http_headers(request)
                    print '<p>' + _("Can't work out query") + ' "<pre>' + query + '</pre>"'

        # generate page footer
        # (actions that do not want this footer use sys.exit(0) to break out
        # of the default execution path, see the "except SystemExit" below)

        request.clock.stop('total')

        if config.show_timings and request.form.getvalue('action', None) != 'print':
            print '<pre><font size="1" face="Verdana">',
            request.clock.dump(sys.stdout)
            print '</font></pre>'

        import socket
        print '<!-- MoinMoin %s on %s served this page in %s secs -->' % (
            version.revision, socket.gethostname(), request.clock.value('total'))
        print '</body></html>'

    except SystemExit:
        pass

    except: # catch and print any exception
        webapi.http_headers(request)
        print
        print "<!-- ERROR REPORT FOLLOWS -->"

        saved_exc = sys.exc_info()
        try:
            from MoinMoin.support import cgitb
        except:
            # no cgitb, for whatever reason
            cgi.print_exception(*saved_exc)
        else:
            try:
                cgitb.handler()
            except:
                cgi.print_exception(*saved_exc)
                print "\n\n<hr><p><b>Additionally, cgitb raised this exception:</b></p>"
                cgi.print_exception()
        del saved_exc

    # flush the output, ignore errors caused by the user closing the socket
    try:
        sys.stdout.flush()
    except IOError, ex:
        import errno
        if ex.errno != errno.EPIPE: raise

    return request

