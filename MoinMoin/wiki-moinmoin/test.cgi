#! /usr/bin/env python

"""
    MoinMoin - CGI Diagnosis

    Copyright (c) 2000 by Jürgen Hermann <jh@web.de>
    All rights reserved, see COPYING for details.

    $Id: test.cgi,v 1.1 2000/11/03 00:44:10 jhermann Exp $
"""

import sys, cgi


def run():
    try:
        from MoinMoin import cgimain
        print 'Package "MoinMoin" sucessfully imported.'
        print

    except:
        import pprint
    
        print 'Can\'t import "MoinMoin" package!'
        print
        print 'Your PYTHONPATH is:'
        print pprint.pformat(sys.path)
        return

    cgimain.test()


print "Content-Type: text/plain"
print
print "MoinMoin CGI Diagnosis"
print "======================"
print

try:
    run()
except:
    type, value, tb = sys.exc_info()
    import traceback, string
    print
    print "Traceback (innermost last):"
    print string.join(traceback.format_tb(tb) +
        traceback.format_exception_only(type, value))

