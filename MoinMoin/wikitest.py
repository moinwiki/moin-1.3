# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Installation tests

    Copyright (c) 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    Note that this module tests a wiki instance for errors, and
    does not unit-test the code or something.

    $Id: wikitest.py,v 1.9 2003/11/09 21:00:52 thomaswaldmann Exp $
"""

def runTest(request):
    """ This is used by moin.cgi to test the configuration, after MoinMoin
        is successfully imported. It should print a plain text diagnosis
        to stdout.
    """
    # Note that importing here makes a difference, namely the request
    # object is already created
    import os, sys, xml
    from MoinMoin import config, util, version, editlog

    print 'Release ', version.release
    print 'Revision', version.revision
    print
    print 'Python version', sys.version
    print 'Python installed to', sys.exec_prefix
    print
    print 'PyXML is %sinstalled' % (xml.__file__.find('_xmlplus') == -1 and 'NOT ' or '')
    print

    print 'Python Path:'
    for dir in sys.path:
        print '   ', dir
    print

    # check if the request is a local one
    import socket
    local_request = socket.getfqdn(os.environ.get('SERVER_NAME')) == \
        socket.getfqdn(os.environ.get('REMOTE_ADDR'))

    # check directories
    print "Checking directories..."
    dirs = [('data', config.data_dir),
            ('text', config.text_dir),
            ('user', config.user_dir),
            ('backup', config.backup_dir)]
    for name, path in dirs:
        if not os.path.isdir(path):
            print "*** %s directory NOT FOUND (set to '%s')" % (name, path)
        elif not os.access(path, os.R_OK | os.W_OK | os.X_OK):
            print "*** %s directory NOT ACCESSIBLE (set to '%s')" % (name, path)
        else:
            path = os.path.abspath(path)
            print "    %s directory tests OK (set to '%s')" % (name, path)
    print

    # check editlog access
    log = editlog.makeLogStore(request)
    msg = log.sanityCheck()
    if msg: print "***", msg

    # check for "diff" command
    diff = util.popen(config.external_diff + " --version", "r")
    lines = diff.readlines()
    rc = diff.close()
    if rc or not lines:
        print "*** Could not find external diff utility '%s'!" % config.external_diff
    else:
        print 'Found an external diff: "%s"' % (lines[0].strip(),)

    # keep some values to ourselves
    print "\nServer Environment:"
    if local_request:
        # print the environment, in case people use exotic servers with broken
        # CGI APIs (say, M$ IIS), to help debugging those
        keys = os.environ.keys()
        keys.sort()
        for key in keys:
            print "    %s = %s" % (key, repr(os.environ[key]))
    else:
        print "    ONLY AVAILABLE FOR LOCAL REQUESTS ON THIS HOST!"

    # run unit tests
    print "\nUnit Tests:"
    try:    
        from MoinMoin import _tests
    except ImportError:
        print "    *** NOT AVAILABLE ***"
    else:
        _tests.run(request)

