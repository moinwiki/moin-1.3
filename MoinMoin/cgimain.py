"""
    MoinMoin - Main CGI Module

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: cgimain.py,v 1.19 2001/01/10 22:03:43 jhermann Exp $
"""


#############################################################################
### Prolog
#############################################################################

from MoinMoin import util

# Imports
util.clock.start('imports')
import cgi, os, re, socket, string, sys

from MoinMoin import version, wikiutil
from MoinMoin.Page import Page
util.clock.stop('imports')

# Load configuration
util.clock.start('config')
from MoinMoin import config
util.clock.stop('config')


#############################################################################
### Test code
#############################################################################

def test():
    """ This is used by test.cgi to test the configuration, after MoinMoin
        is sucessfully imported. It should print a plain text diagnosis
        to stdout.
    """
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
    if not os.access(config.editlog_name, os.W_OK):
        print "*** The edit log '%s' is not writable!" % (config.editlog_name,)

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

def run():
    global form

    global saved_cookie
    saved_cookie = os.environ.get('HTTP_COOKIE', None)

    # sys.stderr.write("----\n")
    # for key in os.environ.keys():    
    #     sys.stderr.write("    %s = '%s'\n" % (key, os.environ[key]))

    # parse request data
    try:
        form = cgi.FieldStorage()
        path_info = util.getPathinfo()

        action = None
        if form.has_key('action'):
            action = form['action'].value
    
        pagename = None
        if len(path_info) and path_info[0] == '/':
            pagename = wikiutil.unquoteWikiname(path_info[1:]) or config.front_page
    except: # catch and print any exception
        util.http_headers()
        cgi.print_exception()
        sys.exit(0)
    
    try:
        # handle request
        from MoinMoin import wikiaction
    
        if action:
            handler = wikiaction.getHandler(action)
            if handler:
                handler(pagename or config.front_page, form)
            else:
                util.http_headers()
                print "<p>Unknown action"
        else:
            if form.has_key('goto'):
                query = form['goto'].value
            elif pagename:
                query = pagename
            else:       
                query = wikiutil.unquoteWikiname(os.environ.get('QUERY_STRING', '')) or config.front_page
    
            if config.allow_extended_names:
                Page(query).send_page(form)
            else:
                word_re_str = r"([%s][%s]+){2,}" % (
                    config.upperletters, config.lowerletters)
                word_match = re.match(word_re_str, query)
                if word_match:
                    word = word_match.group(0)
                    Page(word).send_page(form)
                else:
                    util.http_headers()
                    print "<p>Can't work out query \"<pre>" + query + "</pre>\""
    
        # generate page footer
        # (actions that do not want this footer use sys.exit(0) to break out
        # of the default execution path, see the "except SystemExit" below)

        util.clock.stop('total')
    
        if config.show_timings:
            print '<pre><font size="1" face="Verdana">',
            util.clock.dump(sys.stdout)
            print '</font></pre>'
    
        print '<!-- MoinMoin %s on %s served this page in %s secs -->' % (
            version.revision, socket.gethostname(), util.clock.value('total'))
        print '</body></html>'
    
    except SystemExit:
        pass

    except: # catch and print any exception
        util.http_headers()
        cgi.print_exception()
    
    sys.stdout.flush()


if os.environ.has_key('GATEWAY_INTERFACE'):
    # create CGI log file, and one for catching stderr output
    cgi.logfile = os.path.join(config.data_dir, 'cgi_log')
    sys.stderr = open(os.path.join(config.data_dir, 'err_log'), 'at')
else:
    # if called from the shell, delegate to the "cmdmain" module
    from MoinMoin import cmdmain
    run = cmdmain.run

