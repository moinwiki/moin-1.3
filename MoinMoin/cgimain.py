"""
    MoinMoin - Main CGI Module

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: cgimain.py,v 1.31 2001/10/24 19:15:32 jhermann Exp $
"""

opened_logs = 0

#############################################################################
### Test code
#############################################################################

def test():
    """ This is used by test.cgi to test the configuration, after MoinMoin
        is sucessfully imported. It should print a plain text diagnosis
        to stdout.
    """
    import os, string
    from MoinMoin import config, util, version, editlog

    print 'Release ', version.release
    print 'Revision', version.revision
    print

    # check directories
    print "Checking directories..."
    dirs = [('data', config.data_dir),
            ('text', config.text_dir),
            ('user', config.user_dir),
            ('backup', config.backup_dir)]
    for name, path in dirs:
        if os.path.isdir(path):
            path = os.path.abspath(path)
            print "    %s directory tests OK (set to '%s')" % (name, path)
        else:
            print "*** %s directory NOT FOUND (set to '%s')" % (name, path)
    print

    # check editlog access
    log = editlog.makeLogStore()
    msg = log.sanityCheck()
    if msg: print "***", msg

    # check for "diff" command
    diff = util.popen("diff --version", "r")
    lines = diff.readlines()
    rc = diff.close()
    if rc or not lines:
        print "*** Could not find an external 'diff' program!"
    else:
        print 'Found an external diff: "%s"' % (string.strip(lines[0]),)

    # print the environment, in case people use exotic servers with broken
    # CGI APIs (say, M$ IIS), to help debugging those
    print "\nServer Environment:"
    for key in os.environ.keys():
        print "    %s = %s" % (key, repr(os.environ[key]))


#############################################################################
### Main code
#############################################################################

def run(properties={}):
    # set up request data
    from MoinMoin.request import Request
    global request
    request = Request(properties)

    # Imports
    request.clock.start('imports')
    import cgi, os, sys
    from MoinMoin import config, version, wikiutil, user, webapi
    from MoinMoin.Page import Page
    request.clock.stop('imports')

    # create CGI log file, and one for catching stderr output
    global opened_logs
    if not opened_logs:
        cgi.logfile = os.path.join(config.data_dir, 'cgi_log')
        sys.stderr = open(os.path.join(config.data_dir, 'err_log'), 'at')
        opened_logs = 1

    # sys.stderr.write("----\n")
    # for key in os.environ.keys():    
    #     sys.stderr.write("    %s = '%s'\n" % (key, os.environ[key]))

    # parse request data
    try:
        request.form = cgi.FieldStorage()
        path_info = webapi.getPathinfo()

        action = None
        if request.form.has_key('action'):
            action = request.form['action'].value

        pagename = None
        if len(path_info) and path_info[0] == '/':
            pagename = wikiutil.unquoteWikiname(path_info[1:]) or config.page_front_page
    except: # catch and print any exception
        webapi.http_headers()
        cgi.print_exception()
        sys.exit(0)

    try:
        # handle request
        from MoinMoin import wikiaction

        if action:
            handler = wikiaction.getHandler(action)
            if handler:
                handler(pagename or config.page_front_page, request.form)
            else:
                webapi.http_headers()
                print "<p>" + user.current.text("Unknown action")
        else:
            if request.form.has_key('goto'):
                query = request.form['goto'].value
            elif pagename:
                query = pagename
            else:
                query = wikiutil.unquoteWikiname(os.environ.get('QUERY_STRING', '')) or config.page_front_page

            if config.allow_extended_names:
                Page(query).send_page(request.form)
            else:
                import re
                word_re_str = r"([%s][%s]+){2,}" % (
                    config.upperletters, config.lowerletters)
                word_match = re.match(word_re_str, query)
                if word_match:
                    word = word_match.group(0)
                    Page(word).send_page(request.form)
                else:
                    webapi.http_headers()
                    print '<p>' + user.current.text("Can't work out query") + ' "<pre>' + query + '</pre>"'

        # generate page footer
        # (actions that do not want this footer use sys.exit(0) to break out
        # of the default execution path, see the "except SystemExit" below)

        request.clock.stop('total')

        if config.show_timings:
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
        webapi.http_headers()
        print
        print "<!-- ERROR REPORT FOLLOWS -->"

        try:
            from MoinMoin.support import cgitb
            cgitb.handler()
        except:
            cgi.print_exception()

    sys.stdout.flush()

